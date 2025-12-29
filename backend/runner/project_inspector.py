# runner/project_inspector.py

from pathlib import Path


class InvalidProjectError(Exception):
    pass


def _collect_py_files(root: Path):
    """
    Collect .py files under root, excluding __pycache__.
    """
    py_files = []
    for path in root.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        py_files.append(path)
    return py_files


def inspect_project(repo_path: Path):
    """
    Inspect a repo and return source & test files.

    Returns:
        {
            "src_files": List[Path],
            "test_files": List[Path],
            "root": Path
        }
    """
    src_dir = repo_path / "src"
    tests_dir = repo_path / "tests"

    if not src_dir.exists():
        raise InvalidProjectError("Missing 'src/' directory")

    if not tests_dir.exists():
        raise InvalidProjectError("Missing 'tests/' directory")

    src_files = _collect_py_files(src_dir)

    # 🔒 FIX: exclude conftest.py explicitly
    test_files = [
        p for p in _collect_py_files(tests_dir)
        if p.name != "conftest.py"
    ]

    if not src_files:
        raise InvalidProjectError("No Python source files found in src/")

    if not test_files:
        raise InvalidProjectError("No Python test files found in tests/")

    return {
        "root": repo_path,
        "src_files": src_files,
        "test_files": test_files,
    }
