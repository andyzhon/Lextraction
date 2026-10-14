import re
from typing import List, Union

from ase.data import chemical_symbols
from ase.formula import Formula

chemical_symbols = set(chemical_symbols) - {"X"} | {"D", "T"}


def format_chemical_name(input_string: str) -> str:
    if not input_string:
        return None
    # Remove HTML tags like <sub>, <italic>, etc., and keep their inner content
    formatted_string = re.sub(r"<[^>]+?>", "", input_string)
    # Replace special characters like · with the appropriate symbol
    formatted_string = formatted_string.replace("⋅", "·")

    subscript_mapping = {
        "\u2080": "0",
        "\u2081": "1",
        "\u2082": "2",
        "\u2083": "3",
        "\u2084": "4",
        "\u2085": "5",
        "\u2086": "6",
        "\u2087": "7",
        "\u2088": "8",
        "\u2089": "9",
    }
    for sub, normal in subscript_mapping.items():
        formatted_string = formatted_string.replace(sub, normal)

    # Rule 1: Keep only digits if preceded by "MOF", "Complex", or "Compound"
    name = re.sub(
        r"([Mm]OF|[Cc]omplex|[Cc]ompound|[Ss]tructure)\s*(\d+)", r"\2", formatted_string
    )
    name = re.sub(r"(\d+)\s*([Mm]OF|[Cc]omplex|[Cc]ompound|[Ss]tructure)", r"\1", name)

    # Rule 2: Remove 'H2O' 보통 점 뒤에 solvent가 오는 모양인데, H2O는 기본적인 거 같아서 이 경우에만 지움.
    if "}" not in name:
        name = re.sub(r"([^\s·]+)\s*·\s*(\d*|n)H2O.*", r"\1", name)
    else:
        tmp = re.split(r"(?<=\})", name)
        tmp[-1] = re.sub(r"([^\s·]+)\s*·\s*(\d*|n)H2O.*", r"\1", "a" + tmp[-1])
        tmp[-1] = tmp[-1][1:]
        name = "".join(tmp)
    return name


def format_chemical_formula(_s):
    if not _s:
        return None, None

    if _s.lower() == "unknown":
        return "", False

    # 일반적인 형태에는 없어야 하는 기호들
    exception_l = ["‘", "0-D", "+", ",", "∝"]
    for item in exception_l:
        if item in _s:
            return _s, False

    s = _s[:]
    s = re.sub(r"<[^>]+?>", "", s)

    subscript_mapping = {
        "\u2080": "0",
        "\u2081": "1",
        "\u2082": "2",
        "\u2083": "3",
        "\u2084": "4",
        "\u2085": "5",
        "\u2086": "6",
        "\u2087": "7",
        "\u2088": "8",
        "\u2089": "9",
    }
    for sub, normal in subscript_mapping.items():
        s = s.replace(sub, normal)

    s = re.sub(r"\s+", "", s)
    # Preserve composite, coating, hydrate and non-stoichiometric notation.
    # A bag of regex matches cannot establish a single chemical formula.
    if not re.fullmatch(r"(?:[A-Z][a-z]?\d*|\(|\)\d*)+", s):
        return _s, False
    try:
        counts = Formula(s).count()
    except (ValueError, AssertionError, IndexError):
        return _s, False
    if not counts or any(elem not in chemical_symbols or count <= 0
                         for elem, count in counts.items()):
        return _s, False
    return " ".join(f"{elem}{count}" for elem, count in sorted(counts.items())), True


def flatten_list_of_dicts(data: List[Union[dict, list]]) -> List[dict]:
    """
    Flattens a list that may contain dictionaries or lists of dictionaries
    into a single list of dictionaries.

    Args:
    data (List[Union[dict, List[dict]]]): The input list containing dictionaries
                                          or lists of dictionaries.

    Returns:
    List[dict]: A flattened list of dictionaries.
    """
    flattened_list = []
    for item in data:
        if isinstance(item, dict):
            flattened_list.append(item)
        elif isinstance(item, list):
            if not item:
                continue
            contain_ = True
            while isinstance(item[0], list):
                item = item[0]
                if not item:
                    contain_ = False
                    break
            if not contain_:
                continue
            flattened_list.extend(item)
        elif isinstance(item, str):
            continue  # ['No properties found'] 예외 뜨는 아이템들.
        elif not item:
            continue
        elif item == "Bond & Angle type of table is not target":
            continue
        else:
            raise TypeError(
                f"All items in the list must be dict or list, not {type(item)}: {item}"
            )
    return flattened_list
