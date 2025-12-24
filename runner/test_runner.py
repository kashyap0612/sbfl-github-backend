# runner/test_runner.py

import subprocess
from pathlib import Path


class TestResult:
    def __init__(self, test_path: Path, passed: bool):
        self.test_path = test_path
        self.passed = passed

    def __repr__(self):
        return f"<TestResult {self.test_path.name} passed={self.passed}>"



def run_tests(repo_root: Path, test_files: list[Path]) -> list[TestResult]:
    """
    Run pytest on each test file individually.
    Returns list of TestResult objects.
    """
    results = []

    test_files = [
    t for t in test_files
    if t.name != "conftest.py"
    ]   

    for test_file in test_files:
        cmd = [
            "pytest",
            str(test_file.relative_to(repo_root)),
            "--quiet"
        ]

        completed = subprocess.run(
            cmd,
            cwd=repo_root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        passed = completed.returncode == 0
        results.append(TestResult(test_file, passed))

    return results