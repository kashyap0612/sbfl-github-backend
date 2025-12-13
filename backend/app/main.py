from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import re
import requests
import base64
import os

app = FastAPI()

# -------------------- CONFIG (GUARDRAILS) --------------------

MAX_FILE_SIZE = 200_000  # 200 KB

ALLOWED_EXTENSIONS = {
    ".py", ".cpp", ".c", ".h", ".hpp",
    ".js", ".ts", ".java",
    ".go", ".rs",
    ".md", ".txt"
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

# -------------------- HELPERS --------------------

def parse_github_repo_url(url: str) -> tuple[str, str]:
    pattern = r"^https?://github\.com/([^/]+)/([^/]+)$"
    match = re.match(pattern, url)

    if not match:
        raise HTTPException(
            status_code=400,
            detail="Invalid GitHub repository URL format"
        )

    return match.group(1), match.group(2)

def fetch_repo_metadata(owner: str, repo: str) -> dict:
    url = f"https://api.github.com/repos/{owner}/{repo}"
    resp = requests.get(url)

    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="Repository not found")

    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="GitHub API error")

    return resp.json()

def fetch_repo_tree(owner: str, repo: str, branch: str) -> list[dict]:
    branch_url = f"https://api.github.com/repos/{owner}/{repo}/branches/{branch}"
    branch_resp = requests.get(branch_url)

    if branch_resp.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail="Failed to fetch branch info"
        )

    tree_sha = branch_resp.json()["commit"]["commit"]["tree"]["sha"]

    tree_url = (
        f"https://api.github.com/repos/{owner}/{repo}"
        f"/git/trees/{tree_sha}?recursive=1"
    )
    tree_resp = requests.get(tree_url)

    if tree_resp.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail="Failed to fetch repository tree"
        )

    return tree_resp.json()["tree"]

def fetch_blob_content(owner: str, repo: str, sha: str) -> str:
    url = f"https://api.github.com/repos/{owner}/{repo}/git/blobs/{sha}"
    resp = requests.get(url)

    if resp.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail="Failed to fetch file content"
        )

    blob = resp.json()

    # Guardrail: size limit
    if blob["size"] > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File too large to fetch"
        )

    # Guardrail: encoding check
    if blob.get("encoding") != "base64":
        raise HTTPException(
            status_code=415,
            detail="Unsupported file encoding"
        )

    decoded = base64.b64decode(blob["content"])
    text = decoded.decode("utf-8", errors="replace")

    # Guardrail: binary detection
    if "\x00" in text:
        raise HTTPException(
            status_code=415,
            detail="Binary file detected"
        )

    return text

# -------------------- ENDPOINTS --------------------

@app.post("/repo-info")
def repo_info(data: RepoRequest):
    owner, repo = parse_github_repo_url(data.repo_url)
    repo_data = fetch_repo_metadata(owner, repo)

    return {
        "name": repo_data["name"],
        "owner": repo_data["owner"]["login"],
        "description": repo_data["description"],
        "stars": repo_data["stargazers_count"],
        "forks": repo_data["forks_count"],
        "default_branch": repo_data["default_branch"],
    }

@app.post("/repo-files")
def repo_files(data: RepoRequest):
    owner, repo = parse_github_repo_url(data.repo_url)
    repo_data = fetch_repo_metadata(owner, repo)

    tree = fetch_repo_tree(owner, repo, repo_data["default_branch"])

    files = [
        item["path"]
        for item in tree
        if item["type"] == "blob"
    ]

    return {
        "total_files": len(files),
        "files": files[:100]  # intentional cap
    }

@app.post("/repo-file-content")
def repo_file_content(data: FileRequest):
    # Guardrail: path sanity
    if ".." in data.path or data.path.startswith("/"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file path"
        )

    owner, repo = parse_github_repo_url(data.repo_url)
    repo_data = fetch_repo_metadata(owner, repo)

    tree = fetch_repo_tree(owner, repo, repo_data["default_branch"])

    for item in tree:
        if item["type"] == "blob" and item["path"] == data.path:

            # Guardrail: extension filter
            _, ext = os.path.splitext(item["path"])
            if ext.lower() not in ALLOWED_EXTENSIONS:
                raise HTTPException(
                    status_code=415,
                    detail="File type not supported"
                )

            content = fetch_blob_content(owner, repo, item["sha"])

            return {
                "path": data.path,
                "size": item["size"],
                "content": content
            }

    raise HTTPException(
        status_code=404,
        detail="File not found in repository"
    )
