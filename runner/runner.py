import json
import subprocess
import sys
from pathlib import Path

import os
os.chdir("/repo")

OUTPUT_PATH = Path("/output/result.json")

import subprocess
import json

def discover_tests():
    try:
        result = subprocess.run(
            ["pytest", "--collect-only", "-q"],
            cwd="/repo",
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(result.stderr)
            return []

        tests = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        return tests

    except Exception as e:
        raise RuntimeError(f"Test discovery failed: {e}")

def run_test(test_name):
    """Run a single test with coverage and return (status, executed_lines)."""

    subprocess.run(["coverage", "erase"], check=True)

    proc = subprocess.run(
        ["coverage", "run", "-m", "pytest", test_name],
        capture_output=True,
        text=True
    )

    status = "pass" if proc.returncode == 0 else "fail"

    subprocess.run(
        ["coverage", "json", "-o", "coverage.json"],
        check=True
    )

    with open("coverage.json") as f:
        cov = json.load(f)

    executed = []
    for file, data in cov["files"].items():
        for line in data.get("executed_lines", []):
            executed.append(f"{file}:{line}")

    return status, executed

def main():
    # install repo + deps if present
    if Path("setup.py").exists() or Path("pyproject.toml").exists():
        subprocess.run(
            ["pip", "install", "-e", "."],
            check=True
        )

    results = []
    passed = failed = 0

    tests = discover_tests()

    for test in tests:
        try:
            status, lines = run_test(test)
        except Exception:
            status, lines = "fail", []

        if status == "pass":
            passed += 1
        else:
            failed += 1

        results.append({
            "name": test,
            "status": status,
            "executed_lines": lines
        })

    output = {
        "summary": {
            "total_tests": len(tests),
            "passed": passed,
            "failed": failed
        },
        "tests": results
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)


if __name__ == "__main__":
    main()
