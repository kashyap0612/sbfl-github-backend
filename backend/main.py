import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import re
import requests
import base64
import os
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
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- CONFIG --------------------

MAX_FILE_SIZE = 200_000  # 200 KB

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

# -------------------- HELPERS --------------------

def parse_github_repo_url(url: str) -> tuple[str, str]:
    match = re.match(r"^https?://github\.com/([^/]+)/([^/]+)", url)
    if not match:
        raise HTTPException(status_code=400, detail="Invalid GitHub repo URL")
    return match.group(1), match.group(2)

def fetch_repo_metadata(owner: str, repo: str) -> dict:
    resp = requests.get(f"https://api.github.com/repos/{owner}/{repo}")
    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="Repository not found")
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="GitHub API error")
    return resp.json()

def fetch_repo_tree(owner: str, repo: str, branch: str) -> list[dict]:
    branch_resp = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/branches/{branch}"
    )
    if branch_resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to fetch branch info")

    tree_sha = branch_resp.json()["commit"]["commit"]["tree"]["sha"]

    tree_resp = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/git/trees/{tree_sha}?recursive=1"
    )
    if tree_resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to fetch repo tree")

    return tree_resp.json()["tree"]

def fetch_blob_content(owner: str, repo: str, sha: str) -> str:
    resp = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/git/blobs/{sha}"
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to fetch file content")

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
    owner, repo = parse_github_repo_url(data.repo_url)
    meta = fetch_repo_metadata(owner, repo)
    return {
        "name": meta["name"],
        "owner": meta["owner"]["login"],
        "description": meta["description"],
        "stars": meta["stargazers_count"],
        "forks": meta["forks_count"],
        "default_branch": meta["default_branch"],
    }

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

# -------------------- SBFL ENDPOINT --------------------

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

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# OpenAI client
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -------------------- CHAT WITH FILE --------------------

# @app.post("/chat-file")
# def chat_file(data: ChatFileRequest):
#     if not os.getenv("OPENAI_API_KEY"):
#         raise HTTPException(status_code=500, detail="OpenAI API key not set")

#     messages = [
#         {
#             "role": "system",
#             "content": (
#                 "You are a code assistant. "
#                 "Answer ONLY using the given file content. "
#                 "If the answer is not in the file, say you cannot find it."
#             )
#         },
#         {
#             "role": "user",
#             "content": f"FILE CONTENT:\n{data.file_content}"
#         },
#         {
#             "role": "user",
#             "content": data.question
#         }
#     ]

#     response = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=messages,
#         temperature=0
#     )

#     return {
#         "answer": response.choices[0].message.content
#     }
