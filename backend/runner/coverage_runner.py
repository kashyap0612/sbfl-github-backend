# runner/coverage_runner.py

import subprocess
from pathlib import Path
import coverage
import os
import sys


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

        # 🔒 Correct PYTHONPATH: repo root, not src/
        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo_root)

        # 🔒 Always use same python that runs backend
        cmd = [
            sys.executable,
            "-m",
            "coverage",
            "run",
            "--source",
            "src",
            "-m",
            "pytest",
            str(test_file.relative_to(repo_root)),
            "--quiet",
        ]

        completed = subprocess.run(
            cmd,
            cwd=repo_root,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        passed = completed.returncode == 0

        # 🔒 If coverage file does not exist, infra failure → skip
        if not coverage_file.exists():
            continue

        cov = coverage.Coverage(data_file=str(coverage_file))
        cov.load()

        data = cov.get_data()

        # 🔒 If no files measured, infra failure → skip
        if not data.measured_files():
            cov.erase()
            continue

        executed = set()

        for file_path in data.measured_files():
            file_path = Path(file_path)

            # Only consider src/
            if "src" not in file_path.parts:
                continue

            lines = data.lines(str(file_path))
            if not lines:
                continue

            rel_path = file_path.relative_to(repo_root)

            for line in lines:
                executed.add((str(rel_path).replace("\\", "/"), line))

        cov.erase()

        # 🔒 SBFL invariant: failing test MUST execute code
        if not passed and not executed:
            continue

        results.append(CoverageResult(test_file, passed, executed))

    return results
