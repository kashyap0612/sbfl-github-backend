from runner.matrix_builder import build_coverage_matrix
from runner.coverage_runner import CoverageResult

def test_build_coverage_matrix():
    r1 = CoverageResult(test_node="test_1", passed=False, covered_lines={("src/main.py", 10), ("src/main.py", 11)})
    r2 = CoverageResult(test_node="test_2", passed=True, covered_lines={("src/main.py", 10)})
    
    matrix = build_coverage_matrix([r1, r2])
    
    # Line 10: hit by failing (test_1) and passing (test_2)
    assert matrix[("src/main.py", 10)]["ef"] == 1
    assert matrix[("src/main.py", 10)]["ep"] == 1
    assert matrix[("src/main.py", 10)]["nf"] == 0
    assert matrix[("src/main.py", 10)]["np"] == 0
    
    # Line 11: hit by failing (test_1) only
    assert matrix[("src/main.py", 11)]["ef"] == 1
    assert matrix[("src/main.py", 11)]["ep"] == 0
    assert matrix[("src/main.py", 11)]["nf"] == 0
    assert matrix[("src/main.py", 11)]["np"] == 1
