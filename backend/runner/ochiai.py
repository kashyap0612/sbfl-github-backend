# runner/ochiai.py

import math
from typing import Dict, Tuple


def ochiai_score(ef: int, ep: int, nf: int, np: int) -> float:
    if ef == 0:
        return 0.0

    denom = (ef + nf) * (ef + ep)
    if denom == 0:
        return 0.0

    return ef / math.sqrt(denom)


def compute_ochiai_scores(
    coverage_matrix: Dict[Tuple[str, int], Dict[str, int]]
) -> Dict[Tuple[str, int], float]:
    scores = {}

    for stmt, counts in coverage_matrix.items():
        scores[stmt] = ochiai_score(
            counts["ef"],
            counts["ep"],
            counts["nf"],
            counts["np"],
        )

    return scores
