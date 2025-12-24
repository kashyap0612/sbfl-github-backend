# runner/matrix_builder.py

from collections import defaultdict
from typing import Dict, Tuple, List

from runner.coverage_runner import CoverageResult


def build_coverage_matrix(
    coverage_results: List[CoverageResult],
) -> Dict[Tuple[str, int], Dict[str, int]]:
    """
    Build SBFL coverage matrix.

    Returns:
        {
          (file, line): {
              "ef": int,
              "ep": int,
              "nf": int,
              "np": int
          }
        }
    """
    matrix = defaultdict(lambda: {"ef": 0, "ep": 0, "nf": 0, "np": 0})

    total_failing = sum(1 for r in coverage_results if not r.passed)
    total_passing = sum(1 for r in coverage_results if r.passed)

    # First pass: count executions
    for result in coverage_results:
        for stmt in result.covered_lines:
            if result.passed:
                matrix[stmt]["ep"] += 1
            else:
                matrix[stmt]["ef"] += 1

    # Second pass: derive non-executions
    for stmt, counts in matrix.items():
        counts["nf"] = total_failing - counts["ef"]
        counts["np"] = total_passing - counts["ep"]

    return dict(matrix)
