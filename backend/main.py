import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import re
import requests
import base64
from pathlib import Path

from runner.repo_manager import clone_repo
from runner.project_inspector import inspect_project
from runner.coverage_runner import run_tests_with_coverage
from runner.matrix_builder import build_coverage_matrix
from runner.ochiai import compute_ochiai_scores
from runner.result_formatter import format_sbfl_results

# -------------------- APP INIT --------------------

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sbfl-github-frontend.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- CONFIG --------------------

MAX_FILE_SIZE = 200_000  # 200 KB

GITHUB_HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "sbfl-analyzer",
    "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}"
}

ALLOWED_EXTENSIONS = {
    ".py", ".java", ".js", ".ts", ".cpp", ".c", ".go", ".rs", ".kt", ".scala",
    ".cs", ".php", ".rb", ".swift",
    ".h", ".hpp",
    ".json", ".yaml", ".yml", ".toml", ".xml", ".ini", ".cfg",
    ".sh", ".dockerfile",
    ".md"
}

# -------------------- MODELS --------------------

class RepoRequest(BaseModel):
    repo_url: str

class FileRequest(BaseModel):
    repo_url: str
    path: str

# -------------------- HEALTH --------------------

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"message": "SBFL backend running"}

# -------------------- HELPERS --------------------

def parse_github_repo_url(url: str) -> tuple[str, str]:
    match = re.match(r"^https?://github\.com/([^/]+)/([^/]+)", url)
    if not match:
        raise HTTPException(status_code=400, detail="Invalid GitHub repo URL")
    return match.group(1), match.group(2)

def fetch_repo_metadata(owner: str, repo: str) -> dict:
    resp = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}",
        headers=GITHUB_HEADERS,
        timeout=10
    )

    if resp.status_code == 404:
        raise HTTPException(
            status_code=404,
            detail="Repository not found or is private"
        )

    if resp.status_code == 403:
        raise HTTPException(
            status_code=403,
            detail="GitHub API rate limit exceeded or unauthorized"
        )

    if resp.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=f"GitHub API error: {resp.status_code}"
        )

    return resp.json()


def fetch_repo_tree(owner: str, repo: str, branch: str) -> list[dict]:
    branch_resp = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/branches/{branch}",
        headers=GITHUB_HEADERS,
        timeout=10
    )

    if branch_resp.status_code == 403:
        raise HTTPException(
            status_code=403,
            detail="GitHub API rate limit exceeded or unauthorized"
        )

    if branch_resp.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=f"GitHub API error: {branch_resp.status_code}"
        )

    tree_sha = branch_resp.json()["commit"]["commit"]["tree"]["sha"]

    tree_resp = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/git/trees/{tree_sha}?recursive=1",
        headers=GITHUB_HEADERS,
        timeout=10
    )

    if tree_resp.status_code == 403:
        raise HTTPException(
            status_code=403,
            detail="GitHub API rate limit exceeded or unauthorized"
        )

    if tree_resp.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=f"GitHub API error: {tree_resp.status_code}"
        )

    return tree_resp.json()["tree"]

def fetch_blob_content(owner: str, repo: str, sha: str) -> str:
    resp = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/git/blobs/{sha}",
        headers=GITHUB_HEADERS,
        timeout=10
    )

    if resp.status_code == 403:
        raise HTTPException(
            status_code=403,
            detail="GitHub API rate limit exceeded or unauthorized"
        )

    if resp.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=f"GitHub API error: {resp.status_code}"
        )

    blob = resp.json()

    if blob["size"] > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")

    if blob.get("encoding") != "base64":
        raise HTTPException(status_code=415, detail="Unsupported encoding")

    decoded = base64.b64decode(blob["content"]).decode("utf-8", errors="replace")

    if "\x00" in decoded:
        raise HTTPException(status_code=415, detail="Binary file detected")

    return decoded

# -------------------- GITHUB BROWSING ENDPOINTS --------------------

@app.post("/repo-info")
def repo_info(data: RepoRequest):
    try:
        owner, repo = parse_github_repo_url(data.repo_url)
        meta = fetch_repo_metadata(owner, repo)

        return {
            "name": meta["name"],
            "owner": meta["owner"]["login"],
            "description": meta["description"],
            "default_branch": meta["default_branch"],
            "visibility": "private" if meta.get("private", False) else "public"
        }

    except HTTPException:
        raise
    except Exception as e:
        print("repo-info error:", repr(e))
        raise HTTPException(
            status_code=400,
            detail="Failed to fetch repository info"
        )


@app.post("/repo-files")
def repo_files(data: RepoRequest):
    owner, repo = parse_github_repo_url(data.repo_url)
    meta = fetch_repo_metadata(owner, repo)
    tree = fetch_repo_tree(owner, repo, meta["default_branch"])

    files = []

    for item in tree:
        if item["type"] != "blob":
            continue

        ext = Path(item["path"]).suffix.lower()
        if ext in ALLOWED_EXTENSIONS:
            files.append({
                "path": item["path"],
                "extension": ext,
                "size": item.get("size", 0)
            })

    return {
        "total_files": len(files),
        "files": files[:100]
    }

@app.post("/repo-file-content")
def repo_file_content(data: FileRequest):
    if ".." in data.path or data.path.startswith("/"):
        raise HTTPException(status_code=400, detail="Invalid file path")

    owner, repo = parse_github_repo_url(data.repo_url)
    meta = fetch_repo_metadata(owner, repo)
    tree = fetch_repo_tree(owner, repo, meta["default_branch"])

    for item in tree:
        if item["type"] == "blob" and item["path"] == data.path:
            ext = Path(item["path"]).suffix.lower()
            if ext not in ALLOWED_EXTENSIONS:
                raise HTTPException(status_code=415, detail="File type not supported")

            content = fetch_blob_content(owner, repo, item["sha"])

            return {
                "path": data.path,
                "extension": ext,
                "size": item.get("size", 0),
                "content": content
            }

    raise HTTPException(status_code=404, detail="File not found")

@app.post("/run-sbfl")
def run_sbfl(data: RepoRequest):
    try:
        repo_path = clone_repo(data.repo_url)
        info = inspect_project(repo_path)

        cov_results = run_tests_with_coverage(repo_path, info["test_files"])
        matrix = build_coverage_matrix(cov_results)
        scores = compute_ochiai_scores(matrix)
        formatted = format_sbfl_results(scores)

        return formatted

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="SBFL execution failed"
        )