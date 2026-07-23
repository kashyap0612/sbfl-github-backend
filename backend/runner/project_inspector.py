# runner/project_inspector.py

from pathlib import Path

class InvalidProjectError(Exception):
    pass

def _collect_py_files(root: Path):
    """
    Collect .py files under root, excluding __pycache__ and venv.
    """
    py_files = []
    for path in root.rglob("*.py"):
        parts = path.parts
        if "__pycache__" in parts or "venv" in parts or ".venv" in parts or ".tox" in parts or ".git" in parts or "node_modules" in parts:
            continue
        py_files.append(path)
    return py_files

def inspect_project(repo_path: Path):
    """
    Inspect a repo and return source & test files.
    Dynamically infers test files without hardcoding src/ or tests/ directories.
    """
    all_py_files = _collect_py_files(repo_path)
    
    src_files = []
    test_files = []

    for f in all_py_files:
        # Heuristic for test files
        if "tests" in f.parts or "test" in f.parts or f.name.startswith("test_") or f.name.endswith("_test.py"):
            if f.name != "conftest.py" and f.name != "__init__.py":
                test_files.append(f)
        else:
            if f.name not in ["setup.py", "conftest.py"]:
                src_files.append(f)

    if not src_files:
        raise InvalidProjectError("No Python source files found.")

    if not test_files:
        raise InvalidProjectError("No Python test files found.")

    return {
        "root": repo_path,
        "src_files": src_files,
        "test_files": test_files,
    }
