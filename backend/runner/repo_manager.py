# runner/repo_manager.py

import subprocess
import tempfile
from pathlib import Path

def clone_repo(repo_url: str) -> Path:
    """
    Clone the given GitHub repo into an isolated temp directory.
    Returns local path to the repo.
    """

    # Create a unique temp directory per request
    base_dir = Path(tempfile.mkdtemp(prefix="sbfl_"))
    repo_path = base_dir / "repo"

    result = subprocess.run(
        ["git", "clone", repo_url, str(repo_path)],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Git clone failed:\n{result.stderr}")

    return repo_path