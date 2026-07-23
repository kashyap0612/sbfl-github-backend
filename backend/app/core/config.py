import os

class Settings:
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "http://localhost:9000,http://localhost:5173")
    MAX_FILE_SIZE: int = 200_000  # 200 KB

settings = Settings()
