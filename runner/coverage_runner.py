# runner/coverage_runner.py

import subprocess
from pathlib import Path
import coverage
import os


class CoverageResult:
    def __init__(self, test_path: Path, passed: bool, covered_lines: set):
        self.test_path = test_path
        self.passed = passed
        self.covered_lines = covered_lines

    def __repr__(self):
        return (
            f"<CoverageResult {self.test_path.name} "
            f"passed={self.passed} "
            f"lines={len(self.covered_lines)}>"
        )


def run_tests_with_coverage(repo_root: Path, test_files: list[Path]) -> list[CoverageResult]:
    results = []

    for test_file in test_files:
        coverage_file = repo_root / ".coverage"

        if coverage_file.exists():
            coverage_file.unlink()

        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo_root / "src")

        completed = subprocess.run(
            [
                "coverage",
                "run",
                "--source", "src",
                "-m",
                "pytest",
                str(test_file.relative_to(repo_root)),
                "--quiet"
            ],
            cwd=repo_root,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        passed = completed.returncode == 0

        cov = coverage.Coverage(data_file=str(coverage_file))
        cov.load()

        executed = set()
        data = cov.get_data()

        for file_path in data.measured_files():
            if not str(file_path).startswith(str(repo_root / "src")):
                continue

            lines = data.lines(file_path)
            if lines:
                rel_path = Path(file_path).relative_to(repo_root)
                for line in lines:
                    executed.add((str(rel_path), line))

        results.append(CoverageResult(test_file, passed, executed))

        cov.erase()

    return results
