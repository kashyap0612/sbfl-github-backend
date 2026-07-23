import re
import base64
import requests
from pathlib import Path
from fastapi import HTTPException
from app.core.config import settings

ALLOWED_EXTENSIONS = {
    ".py", ".java", ".js", ".ts", ".cpp", ".c", ".go", ".rs", ".kt", ".scala",
    ".cs", ".php", ".rb", ".swift",
    ".h", ".hpp",
    ".json", ".yaml", ".yml", ".toml", ".xml", ".ini", ".cfg",
    ".sh", ".dockerfile",
    ".md"
}

class GitHubClient:
    def __init__(self):
        self.headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "sbfl-analyzer",
            "Authorization": f"Bearer {settings.GITHUB_TOKEN}"
        }

    @staticmethod
    def parse_repo_url(url: str) -> tuple[str, str]:
        match = re.match(r"^https?://github\.com/([^/]+)/([^/]+)", url)
        if not match:
            raise HTTPException(status_code=400, detail="Invalid GitHub repo URL")
        return match.group(1), match.group(2)

    def _make_request(self, url: str) -> dict:
        resp = requests.get(url, headers=self.headers, timeout=10)
        
        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail="Not found or private")
        if resp.status_code == 403:
            raise HTTPException(status_code=403, detail="Rate limit exceeded or unauthorized")
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail=f"API error: {resp.status_code}")
            
        return resp.json()

    def fetch_repo_metadata(self, owner: str, repo: str) -> dict:
        return self._make_request(f"https://api.github.com/repos/{owner}/{repo}")

    def fetch_repo_tree(self, owner: str, repo: str, branch: str) -> list[dict]:
        branch_data = self._make_request(f"https://api.github.com/repos/{owner}/{repo}/branches/{branch}")
        tree_sha = branch_data["commit"]["commit"]["tree"]["sha"]
        
        tree_data = self._make_request(f"https://api.github.com/repos/{owner}/{repo}/git/trees/{tree_sha}?recursive=1")
        return tree_data.get("tree", [])

    def fetch_blob_content(self, owner: str, repo: str, sha: str) -> str:
        blob = self._make_request(f"https://api.github.com/repos/{owner}/{repo}/git/blobs/{sha}")
        
        if blob.get("size", 0) > settings.MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large")

        if blob.get("encoding") != "base64":
            raise HTTPException(status_code=415, detail="Unsupported encoding")

        decoded = base64.b64decode(blob["content"]).decode("utf-8", errors="replace")

        if "\x00" in decoded:
            raise HTTPException(status_code=415, detail="Binary file detected")

        return decoded
