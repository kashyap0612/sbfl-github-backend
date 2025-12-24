# runner/repo_manager.py

import hashlib
import subprocess
from pathlib import Path

REPOS_DIR = Path(__file__).resolve().parents[1] / "repos"
REPOS_DIR.mkdir(exist_ok=True)


def _repo_hash(repo_url: str) -> str:
    return hashlib.sha1(repo_url.encode()).hexdigest()


def clone_repo(repo_url: str) -> Path:
    """
    Clone the given GitHub repo if not already cloned.
    Returns local path to the repo.
    """
    repo_id = _repo_hash(repo_url)
    repo_path = REPOS_DIR / repo_id

    if repo_path.exists():
        return repo_path

    result = subprocess.run(
        ["git", "clone", repo_url, str(repo_path)],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Git clone failed:\n{result.stderr}"
        )

    return repo_path
