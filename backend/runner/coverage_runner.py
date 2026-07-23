# runner/coverage_runner.py

import subprocess
from pathlib import Path
import coverage
import os
import sys

# Security: Conditionally define resource limits for Linux environments (like Render)
def set_limits():
    import resource
    # Limit CPU time to 30 seconds
    resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
    # Limit memory to 512MB
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
    # Limit number of processes (prevent fork bombs)
    resource.setrlimit(resource.RLIMIT_NPROC, (20, 20))

class CoverageResult:
    def __init__(self, test_node: str, passed: bool, covered_lines: set):
        self.test_node = test_node
        self.passed = passed
        self.covered_lines = covered_lines

    def __repr__(self):
        return (
            f"<CoverageResult {self.test_node} "
            f"passed={self.passed} "
            f"lines={len(self.covered_lines)}>"
        )


def run_tests_with_coverage(repo_root: Path, test_files: list[Path]) -> list[CoverageResult]:
    results = []
    
    # Security: Strip environment of all secrets (like GITHUB_TOKEN)
    env = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": str(repo_root)
    }
    # Required for Python/pytest on Windows to function without crashing
    if "SYSTEMROOT" in os.environ:
        env["SYSTEMROOT"] = os.environ["SYSTEMROOT"]
    if "TEMP" in os.environ:
        env["TEMP"] = os.environ["TEMP"]
    if "TMP" in os.environ:
        env["TMP"] = os.environ["TMP"]

    # Security: Apply POSIX resource limits only on non-Windows platforms
    kwargs = {}
    if sys.platform != "win32":
        kwargs["preexec_fn"] = set_limits

    for test_file in test_files:
        # Collect individual test nodes
        collect_cmd = [
            sys.executable,
            "-m",
            "pytest",
            str(test_file.relative_to(repo_root)),
            "--collect-only",
            "-q",
        ]
        
        try:
            collect_completed = subprocess.run(
                collect_cmd,
                cwd=repo_root,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,  # Security: 10s timeout for node collection
                **kwargs
            )
        except subprocess.TimeoutExpired:
            continue
            
        # Parse test nodes (e.g., tests/test_math.py::test_addition)
        test_nodes = []
        for line in collect_completed.stdout.splitlines():
            line = line.strip()
            if "::" in line and not line.startswith("="):
                test_nodes.append(line)

        # Run coverage for each individual test node
        for test_node in test_nodes:
            coverage_file = repo_root / ".coverage"

            if coverage_file.exists():
                coverage_file.unlink()

            cmd = [
                sys.executable,
                "-m",
                "coverage",
                "run",
                "--source",
                ".",
                "-m",
                "pytest",
                test_node,
                "--quiet",
            ]

            try:
                completed = subprocess.run(
                    cmd,
                    cwd=repo_root,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=30,  # Security: 30s timeout for individual test execution
                    **kwargs
                )
                passed = completed.returncode == 0
            except subprocess.TimeoutExpired:
                # Security: Treat timeouts as test failures, but allow pipeline to continue
                passed = False

            # If coverage file does not exist, infra failure → skip
            if not coverage_file.exists():
                continue

            cov = coverage.Coverage(data_file=str(coverage_file))
            cov.load()
            data = cov.get_data()

            # If no files measured, infra failure → skip
            if not data.measured_files():
                cov.erase()
                continue

            executed = set()

            for file_path in data.measured_files():
                file_path = Path(file_path)

                # Filter out test files and virtual environments from coverage tracking
                parts = file_path.parts
                if "tests" in parts or "test" in parts or file_path.name.startswith("test_") or file_path.name.endswith("_test.py"):
                    continue
                if "venv" in parts or ".venv" in parts:
                    continue

                lines = data.lines(str(file_path))
                if not lines:
                    continue

                rel_path = file_path.relative_to(repo_root)
                for line in lines:
                    executed.add((str(rel_path).replace("\\", "/"), line))

            cov.erase()

            # SBFL invariant: failing test MUST execute code
            if not passed and not executed:
                continue

            results.append(CoverageResult(test_node, passed, executed))

    return results
