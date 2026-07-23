import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException

from app.models.schemas import RepoRequest, FileRequest
from app.services.github_client import GitHubClient, ALLOWED_EXTENSIONS

from runner.repo_manager import clone_repo
from runner.project_inspector import inspect_project
from runner.coverage_runner import run_tests_with_coverage
from runner.matrix_builder import build_coverage_matrix
from runner.ochiai import compute_ochiai_scores
from runner.result_formatter import format_sbfl_results

router = APIRouter()
github = GitHubClient()
logger = logging.getLogger(__name__)

@router.get("/health")
def health_check():
    return {"status": "ok"}

@router.get("/")
def root():
    return {"message": "SBFL backend running"}

@router.post("/repo-info")
def repo_info(data: RepoRequest):
    owner, repo = github.parse_repo_url(data.repo_url)
    meta = github.fetch_repo_metadata(owner, repo)
    return {
        "name": meta.get("name"),
        "owner": meta.get("owner", {}).get("login"),
        "description": meta.get("description"),
        "default_branch": meta.get("default_branch"),
        "visibility": "private" if meta.get("private", False) else "public"
    }

@router.post("/repo-files")
def repo_files(data: RepoRequest):
    owner, repo = github.parse_repo_url(data.repo_url)
    meta = github.fetch_repo_metadata(owner, repo)
    tree = github.fetch_repo_tree(owner, repo, meta["default_branch"])

    files = []
    for item in tree:
        if item.get("type") == "blob":
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

@router.post("/repo-file-content")
def repo_file_content(data: FileRequest):
    if ".." in data.path or data.path.startswith("/"):
        raise HTTPException(status_code=400, detail="Invalid file path")

    owner, repo = github.parse_repo_url(data.repo_url)
    meta = github.fetch_repo_metadata(owner, repo)
    tree = github.fetch_repo_tree(owner, repo, meta["default_branch"])

    for item in tree:
        if item.get("type") == "blob" and item.get("path") == data.path:
            ext = Path(item["path"]).suffix.lower()
            if ext not in ALLOWED_EXTENSIONS:
                raise HTTPException(status_code=415, detail="File type not supported")
            
            content = github.fetch_blob_content(owner, repo, item["sha"])
            return {
                "path": data.path,
                "extension": ext,
                "size": item.get("size", 0),
                "content": content
            }

    raise HTTPException(status_code=404, detail="File not found")

@router.post("/run-sbfl")
def run_sbfl(data: RepoRequest):
    try:
        logger.info("SBFL: cloning repo")
        repo_path = clone_repo(data.repo_url)

        logger.info("SBFL: inspecting project")
        info = inspect_project(repo_path)

        logger.info("SBFL: running tests with coverage")
        cov_results = run_tests_with_coverage(repo_path, info["test_files"])

        matrix = build_coverage_matrix(cov_results)
        scores = compute_ochiai_scores(matrix)
        formatted = format_sbfl_results(scores)

        return formatted

    except Exception as e:
        logger.exception("SBFL execution failed")
        raise HTTPException(status_code=500, detail="SBFL execution failed")
