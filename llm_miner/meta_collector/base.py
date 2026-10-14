import pprint
from pydantic import BaseModel, Field
from typing import List, Any, Dict, Optional, Union
from collections.abc import Sequence, Mapping
import json
import re
from decimal import Decimal, InvalidOperation
from llm_miner.schema import Paragraph
from llm_miner.meta_collector.utils import format_chemical_formula, format_chemical_name


class Material(BaseModel):
    name: Optional[str] = None
    symbol: Optional[str] = None
    chemical_formula: Optional[str] = None
    formula_source: Optional[str] = None
    synonyms: Optional[List[str]] = None
    refcode: Optional[str] = None
    is_general: Optional[bool] = None
    sample_id: Optional[str] = None
    role: Optional[str] = None
    substrate_formula: Optional[str] = None
    coating_formula: Optional[str] = None
    coating_amount: Optional[Dict[str, Any]] = None

    # @property
    # def clean_chemical_formula(
    #     self,
    # ) -> (str, bool):
    #     formula, is_general = format_chemical_formula(self.chemical_formula)
    #     return formula, is_general

    def is_equal(self, other: object) -> bool:
        if not isinstance(other, Material):
            return False
        if self.sample_id and other.sample_id and self.sample_id != other.sample_id:
            return False
        # An unspecified loading is not the same sample as a measured loading.
        if self.coating_amount != other.coating_amount:
            return False
        for field in ("role", "substrate_formula", "coating_formula"):
            left, right = getattr(self, field), getattr(other, field)
            if left and right and left != right:
                return False
        if self.sample_id and self.sample_id == other.sample_id:
            return True
        s_formula = self.chemical_formula
        o_formula = other.chemical_formula

        if self.name:
            if (self._identity_name(self.name) == self._identity_name(other.name)
                    or self.name == other.symbol):
                if (
                    s_formula != o_formula
                    and self.formula_source == other.formula_source
                ):
                    return False
                return True
        if self.symbol:
            if self.symbol == other.symbol or self.symbol == other.name:
                return True
        return False

    @staticmethod
    def _identity_name(name):
        if not name:
            return None
        name = re.sub(r"(?:[<>]=?|~|≈)?\s*\d+(?:\.\d+)?(?:\s*[-–]\s*\d+(?:\.\d+)?)?\s*(?:wt\.?\s*%|mass\s*%)\s*", "", name)
        return re.sub(r"\s+", " ", name).strip()

    def concatenate(self, others: object) -> None:  # before: concatenate_data
        # 같은 meta를 가지는 두 물질 정보를 합쳐서 하나의 물질 정보로 만들기 # should be revised
        s_formula, s_general = self.chemical_formula, self.is_general
        o_formula, o_general = others.chemical_formula, others.is_general
        if s_general:
            self.chemical_formula = s_formula

        if self.name == others.symbol:
            if others.name:
                self.name = others.name
            self.symbol = others.symbol

        if others.formula_source != "synthesis condition" and o_general:
            self.chemical_formula = o_formula
            self.formula_source = others.formula_source

        if not self.name:
            self.name = others.name
        if not self.symbol:
            self.symbol = others.symbol
        if not self.chemical_formula:
            self.chemical_formula = o_formula
            self.formula_source = others.formula_source
        if not self.synonyms:
            self.synonyms = others.synonyms
        if not self.refcode:
            self.refcode = others.refcode
        for field in ("sample_id", "role", "substrate_formula", "coating_formula", "coating_amount"):
            if not getattr(self, field):
                setattr(self, field, getattr(others, field))

    @staticmethod
    def _coating_amount(data):
        amount = data.get("coating amount", data.get("coating_amount"))
        name = data.get("name") or ""
        if not amount:
            match = re.search(r"((?:[<>]=?|~|≈)?\s*\d+(?:\.\d+)?(?:\s*[-–]\s*\d+(?:\.\d+)?)?)\s*(wt\.?\s*%|mass\s*%)", name, re.I)
            if match:
                amount = {"value": match.group(1), "unit": "wt.%"}
        if not amount:
            return None
        if not isinstance(amount, dict):
            return {"value": str(amount), "unit": ""}
        amount = dict(amount)
        value = str(amount.get("value", "")).strip()
        if not value:
            return None
        try:
            value = format(Decimal(value).normalize(), "f")
        except InvalidOperation:
            pass  # Keep ranges and qualifiers; do not invent a single loading.
        unit = str(amount.get("unit", "")).strip().lower()
        if re.fullmatch(r"(?:wt\.?|mass)\s*%", unit):
            unit = "wt.%"
        result = {"value": value, "unit": unit}
        for key in ("comparison", "is_approximate"):
            if amount.get(key):
                result[key] = amount[key]
        return result

    @classmethod
    def from_data(
        cls,
        data: Dict[str, Any],
        formula_source: Optional[str] = None,
        refcode: Optional[str] = None,
    ):
        """
        근데 이렇게 바로 넣으면 원래가 뭐였는지 확인이 좀 어렵더라.
        """
        if not formula_source:
            formula_source = data.get("formula source")
        chemical_formula, is_general = format_chemical_formula(
            data.get("chemical formula")
        )

        return cls(
            name=format_chemical_name(data.get("name")),
            symbol=format_chemical_name(data.get("symbol")),
            chemical_formula=chemical_formula,
            formula_source=formula_source,
            synonyms=data.get("synonyms"),
            refcode=refcode,
            is_general=is_general,
            sample_id=data.get("sample id") or data.get("sample_id") or None,
            role=data.get("role") or None,
            substrate_formula=data.get("substrate formula") or data.get("substrate_formula") or None,
            coating_formula=data.get("coating formula") or data.get("coating_formula") or None,
            coating_amount=cls._coating_amount(data),
        )

    def to_dict(
        self,
    ) -> Dict[str, Any]:
        return {
            "name": self.name,
            "symbol": self.symbol,
            "chemical_formula": self.chemical_formula,
            "formula_source": self.formula_source,
            "synonyms": self.synonyms,
            "refcode": self.refcode,
            "is_general": self.is_general,
            "sample_id": self.sample_id,
            "role": self.role,
            "substrate_formula": self.substrate_formula,
            "coating_formula": self.coating_formula,
            "coating_amount": self.coating_amount,
        }

    def to_json(self, filepath) -> Dict[str, Any]:
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(
            name=data["name"],
            symbol=data["symbol"],
            chemical_formula=data["chemical_formula"],
            formula_source=data["formula_source"],
            synonyms=data["synonyms"],
            refcode=data["refcode"],
            is_general=data["is_general"],
            sample_id=data.get("sample_id"),
            role=data.get("role"),
            substrate_formula=data.get("substrate_formula"),
            coating_formula=data.get("coating_formula"),
            coating_amount=cls._coating_amount(data),
        )

    @classmethod
    def from_json(cls, filepath):
        with open(filepath) as f:
            data = json.load(f)
        return cls.from_dict(data)


class MinedData(Mapping, BaseModel):
    material: Material
    data: Dict[str, Any]
    element_idx: List[str]
    origin_data: List[Dict[str, Any]] = list()
    doi: Optional[str] = None

    def __getitem__(self, key: str) -> Any:
        return self.data[key]

    def __iter__(self) -> iter:
        return self.data.__iter__()

    def __len__(self) -> int:
        return self.data.__len__()

    @property
    def name(
        self,
    ) -> str:
        return self.material.name

    @property
    def symbol(
        self,
    ) -> str:
        return self.material.symbol

    @property
    def chemical_formula(
        self,
    ) -> str:
        return self.material.chemical_formula

    # @property
    # def clean_chemical_formula(
    #     self,
    # ) -> str:
    #     return self.material.clean_chemical_formula

    @property
    def formula_source(
        self,
    ) -> str:
        return self.material.formula_source

    @property
    def synonyms(
        self,
    ) -> str:
        return self.material.synonyms

    @property
    def refcode(
        self,
    ) -> str:
        return self.material.refcode

    def _to_string(self, print_origin_data=False) -> str:
        string = (
            f"Name : {self.name}\n"
            f"Symbol : {self.symbol}\n"
            f"Chemical formula : {self.chemical_formula}\n"
            f"Synonyms : {self.synonyms}\n"
            f"Refcode : {self.refcode}\n"
            f"Data :\n{pprint.pformat(self.data, sort_dicts=False)}"
        )
        if print_origin_data:
            string += (
                f"\nOrigin data:\n{pprint.pformat(self.origin_data, sort_dicts=False)}"
            )
        return string

    def print(self, print_origin_data=False) -> None:
        print(self._to_string(print_origin_data))

    def is_equal(self, other: object) -> bool:  # before : isequal_meta
        return self.material.is_equal(other.material)

    def concatenate(self, others: object, overwrite: bool = False) -> None:
        self.material.concatenate(others.material)
        for key, value in others.data.items():
            if (not overwrite) and isinstance(self.data.get(key), list) and isinstance(value, list):
                self.data[key] = self.data[key] + [item for item in value if item not in self.data[key]]
            elif (not overwrite) and (key in self.data):
                idx = 1
                new_key = f"{key}_{idx}"
                while new_key in self.data:  # HAVE to fix.
                    idx += 1
                    new_key = f"{key}_{idx}"
                self.data[new_key] = value
            else:
                self.data[key] = value
        self.element_idx.extend(others.element_idx)
        self.origin_data.extend(others.origin_data)

    def to_dict(
        self,
    ) -> Dict[str, Any]:
        return {
            "material": self.material.to_dict(),
            "data": self.data,
            "element_idx": self.element_idx,
            "origin_data": self.origin_data,
            "doi": self.doi,
        }

    def to_json(self, filepath) -> Dict[str, Any]:
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> object:
        return cls(
            material=Material.from_dict(data["material"]),
            data=data["data"],
            element_idx=data["element_idx"],
            origin_data=data["origin_data"],
            doi=data.get("doi"),
        )

    @classmethod
    def from_data(
        cls,
        data: Dict[str, Any],
        formula_source: str = None,
        element_idx: Optional[List[str]] = None,
        doi: Optional[str] = None,
    ):
        if "meta" not in data:
            raise KeyError('data must include key "meta"')

        if not element_idx:
            element_idx = list()
        elif not isinstance(element_idx, list):
            element_idx = [str(element_idx)]

        return cls(
            material=Material.from_data(data["meta"], formula_source=formula_source),
            data={key: value for key, value in data.items() if key != "meta"},
            element_idx=element_idx,
            origin_data=[data],
            doi=doi,
        )

    @classmethod
    def from_json(cls, filepath):
        with open(filepath) as f:
            data = json.load(f)
        return cls.from_dict(data)


class Results(Sequence, BaseModel):
    results: List[MinedData]
    matching_dict: Dict[int, Any]
    doi: Optional[str]
    unassigned_data: List[MinedData] = Field(default_factory=list)

    def __getitem__(self, idx: int):
        return self.results[idx]

    def __len__(
        self,
    ) -> int:
        return len(self.results)

    def _to_string(self, print_origin_data=False) -> str:
        string = ""
        for data in self.results:
            string += data._to_string(print_origin_data)
            string += "\n" + "-" * 80 + "\n"
        return string

    def print(self, print_origin_data=False) -> None:
        print(self._to_string(print_origin_data))

    def append(self, data: MinedData, idx):  # before: categorize_by_equality
        if not (data.name or data.symbol or data.material.sample_id or data.chemical_formula):
            self.unassigned_data.append(data)
            return
        for jdx, value in enumerate(self.results):
            if jdx not in self.matching_dict.keys():
                self.matching_dict[jdx] = []
            if value.is_equal(data):
                value.concatenate(data)
                self.matching_dict[jdx].append(idx)
                return
        self.results.append(data)
        self.matching_dict.setdefault(len(self.results) - 1, [])

    def to_dict(
        self,
    ) -> Dict[str, Any]:
        return {
            "results": [d.to_dict() for d in self.results],
            "matching_dict": self.matching_dict,
            "doi": self.doi,
            "unassigned_data": [d.to_dict() for d in self.unassigned_data],
        }

    def to_json(self, filepath) -> Dict[str, Any]:
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> object:
        return cls(
            results=[MinedData.from_dict(d) for d in data["results"]],
            matching_dict=data["matching_dict"],
            doi=data["doi"],
            unassigned_data=[MinedData.from_dict(d) for d in data.get("unassigned_data", [])],
        )

    @classmethod
    def from_json(cls, filepath):
        with open(filepath) as f:
            data = json.load(f)
        return cls.from_dict(data)

    @classmethod
    def empty(cls, doi: Optional[str] = None):
        return cls(results=list(), matching_dict=dict(), doi=doi)
