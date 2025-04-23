from typing import List
from agents.types import FunctionInfo


def score_function(fn: FunctionInfo) -> int:
    score = 0

    # Fan-in (çağrılan yer sayısı) önemlidir
    score += fn.get("fan_in", 0) * 2

    # Fan-out (başkalarını çağırma) da bir miktar değerli olabilir
    score += fn.get("fan_out", 0)

    # Entry point fonksiyonlar ekstra puan alır
    if fn.get("is_entry_point"):
        score += 5

    # Docstring varsa biraz daha anlamlıdır
    if fn.get("docstring"):
        score += 2

    return score


def select_key_functions(functions: List[FunctionInfo], top_n: int = 3) -> List[FunctionInfo]:
    sorted_fns = sorted(functions, key=score_function, reverse=True)
    return sorted_fns[:top_n]
