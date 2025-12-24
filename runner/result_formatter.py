# runner/result_formatter.py

from collections import defaultdict
from typing import Dict, Tuple


def format_sbfl_results(
    scores: Dict[Tuple[str, int], float]
) -> Dict[str, Dict[int, float]]:
    """
    Convert flat SBFL scores into UI-friendly structure.

    Returns:
        {
          "src/calculator.py": {
              12: 1.0,
              10: 0.8
          }
        }
    """
    result = defaultdict(dict)

    for (file_path, line), score in scores.items():
        # Normalize path separators
        file_path = file_path.replace("\\", "/")

        # Filter out noise
        if file_path.endswith("__init__.py"):
            continue
        if line <= 0:
            continue

        result[file_path][line] = score

    # Sort lines by suspiciousness (descending)
    sorted_result = {}

    for file_path, lines in result.items():
        sorted_lines = dict(
            sorted(lines.items(), key=lambda x: x[1], reverse=True)
        )
        sorted_result[file_path] = sorted_lines

    return sorted_result
