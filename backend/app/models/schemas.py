from pydantic import BaseModel

class RepoRequest(BaseModel):
    repo_url: str
    metric: str = "ochiai"

class FileRequest(BaseModel):
    repo_url: str
    path: str

class ChatRequest(BaseModel):
    file_content: str
    question: str
