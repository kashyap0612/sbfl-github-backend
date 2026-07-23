from pydantic import BaseModel

class RepoRequest(BaseModel):
    repo_url: str

class FileRequest(BaseModel):
    repo_url: str
    path: str
