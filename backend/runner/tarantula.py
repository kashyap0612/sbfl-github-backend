# runner/tarantula.py

from typing import Dict, Tuple

def tarantula_score(ef: int, ep: int, nf: int, np: int) -> float:
    total_f = ef + nf
    total_p = ep + np
    
    if total_f == 0:
        return 0.0
        
    susp_f = ef / total_f
    susp_p = (ep / total_p) if total_p > 0 else 0.0
    
    if susp_f + susp_p == 0:
        return 0.0
        
    return susp_f / (susp_f + susp_p)

def compute_tarantula_scores(
    coverage_matrix: Dict[Tuple[str, int], Dict[str, int]]
) -> Dict[Tuple[str, int], float]:
    scores = {}
    for stmt, counts in coverage_matrix.items():
        scores[stmt] = tarantula_score(
            counts["ef"], counts["ep"], counts["nf"], counts["np"]
        )
    return scores
