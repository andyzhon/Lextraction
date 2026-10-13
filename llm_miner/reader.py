from collections import namedtuple
import warnings
import json
from typing import List, Any, Dict, Union, Iterable
from pydantic import BaseModel
from pathlib import Path

from llm_miner.schema import Paragraph, Elements
from llm_miner.parser import parser_dict, Metadata, BaseParser
from llm_miner.parser.utils import publisher_finder
from llm_miner.utils import merge_para_by_token
from llm_miner.error import ReaderError, ParserError
from llm_miner.config import config
from llm_miner.meta_collector import MetaCollector, Results

warnings.filterwarnings("ignore", category=UserWarning, module="bs4")

# JournalReader类，解析论文 XML/HTML，提取正文、表格、图注及元数据
class JournalReader(BaseModel):
    filepath: Path
    publisher: str
    elements: Elements
    cln_elements: Elements = Elements.empty() # 重组后内容
    result: Results = Results.empty()
    # result: Results = []
    metadata: Metadata

    @property # 获取论文基本信息
    def filename(self):
        return self.filepath.name.strip()

    @property
    def doi(self):
        if isinstance(self.metadata.doi, str):
            return self.metadata.doi.strip()
        return self.metadata.doi

    @property
    def title(self):
        if isinstance(self.metadata.title, str):
            return self.metadata.title.strip()
        return self.metadata.title

    @property
    def url(self):
        return f"https://doi.org/{self.doi}"

    def get_tables(self) -> List[Paragraph]: # 获取特定类型的内容；类型注释，这个方法预期返回一个列表，其中每个元素都是Paragraph对象
        if self.cln_elements: # 是否存在重组后的内容
            return self.cln_elements.get_tables()
        else:
            return self.elements.get_tables()

    def get_texts(self) -> List[Paragraph]:
        if self.cln_elements:
            return self.cln_elements.get_texts()
        else:
            return self.elements.get_texts()

    def get_figures(self) -> List[Paragraph]:
        if self.cln_elements:
            return self.cln_elements.get_figures()
        else:
            return self.elements.get_figures()

    def get_synthesis_conditions(self) -> List[Paragraph]:
        if self.cln_elements:
            return self.cln_elements.get_synthesis_conditions()
        else:
            return self.elements.get_synthesis_conditions()

    def get_properties(self) -> List[Paragraph]: # 获取分类结果为property的段落，分类工作已由CategorizeAgent完成
        if self.cln_elements:
            return self.cln_elements.get_properties()
        else:
            return self.elements.get_properties()
    
    # 在这里考虑添加正极材料与包覆物对

    def get_idx(self, idx: Union[int, Iterable[int]]) -> Paragraph: # 根据编号获取论文段落
        if isinstance(idx, int):
            for element in self.elements:
                if int(element.idx) == idx:
                    return element
            raise IndexError(f"There are no idx {idx} in elements.")
        else: # 段落合并
            ls_para = [self.get_idx(i).copy() for i in idx]
            b_para = ls_para[0]
            for para in ls_para[1:]:
                b_para.merge(para, merge_idx=True)
            return b_para

    def to_dict( # 将JournalReader对象转化为python字典
        self,
    ) -> Dict[str, Any]:
        return {
            "filepath": str(self.filepath),
            "publisher": self.publisher,
            "elements": self.elements.to_dict(),
            "cln_elements": self.cln_elements.to_dict(),
            "metadata": self.metadata.to_dict(),
            "result": self.result.to_dict(),
        }

    def to_json(self, filepath):
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f)

    def reconstruct(self, model_name: str = "gpt-4") -> None: # 重新组织论文段落
        if self.cln_elements:  # clear cln_elements
            self.cln_elements = Elements.empty()

        merge_para_by_token(
            ls_para=self.elements.get_synthesis_conditions(),
            classification="synthesis condition",
            max_tokens=config["input_max_tokens_synthesis"],
            model_name=model_name,
            elements=self.cln_elements,
        )

        merge_para_by_token( # 根据Token数量限制合并材料性质段落
            ls_para=self.elements.get_properties(),
            classification="property",
            max_tokens=config["input_max_tokens_property"],
            model_name=model_name,
            elements=self.cln_elements,
        )

        for table in self.elements.get_tables(): # 表直接复制 
            self.cln_elements.append(table.copy())

        for figure in self.elements.get_figures():
            self.cln_elements.append(figure.copy())

    @classmethod
    def from_file(cls, filepath: str, publisher: str = None): # 类方法，入口方法
        if publisher is None:
            raise NotImplementedError("publisher finder is not implemented.")
            # publisher = publisher_finder(filepath)

        publisher = publisher.lower()
        if publisher not in parser_dict:
            raise ReaderError(
                f"publisher must be one of [`acs`, `rsc`, `elsevier`, `springer], not {publisher}"
            )

        parser: BaseParser = parser_dict[publisher] # 不同出版社使用不同的文件解析器
        try:
            file_bs = parser.open_file(filepath) # 打开文件
            elements = parser.parsing(file_bs) # 解析论文内容
            metadata = parser.get_metadata(file_bs) # 解析论文元数据
        except Exception as e:
            raise ParserError(e)

        return cls( # 返回JournalReader对象，这里的cls()实际上就是创建JournalReader实例
            filepath=Path(filepath),
            publisher=publisher,
            elements=Elements(elements=elements),
            metadata=metadata,
        )

    @classmethod
    def from_dict(cls, data): # 把python字典转化为JournalReader对象
        if "cln_elements" in data:
            cln_elements = Elements.from_dict(data["cln_elements"])
        else:
            cln_elements = Elements.empty()

        if "result" in data:
            result = Results.from_dict(data["result"])
        else:
            result = Results.empty()

        return cls(
            filepath=Path(data["filepath"]),
            publisher=data["publisher"],
            elements=Elements.from_dict(data["elements"]),
            cln_elements=cln_elements,
            result=result,
            metadata=Metadata.from_dict(data["metadata"]),
        )

    @classmethod
    def from_json(cls, filepath):
        with open(filepath) as f:
            data = json.load(f) # 从JSON文件读取python字典
        return cls.from_dict(data) # 将字典转换为JournalReader对象
