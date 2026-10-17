import os
from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://ai:ai@localhost:5432/ai"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    AES_KEY: str = "0123456789abcdef0123456789abcdef"

    SKILLS_STORAGE_PATH: str = str(_BACKEND_DIR / "data" / "skills")
    PDF_STORAGE_PATH: str = str(_BACKEND_DIR / "data" / "pdfs")
    MAX_PDF_SIZE_MB: int = 100

    LLM_DEFAULT_BASE_URL: str = "https://api-inference.modelscope.cn/v1/"
    LLM_DEFAULT_API_KEY: str = ""
    LLM_DEFAULT_MODEL_ID: str = "Qwen/Qwen2.5-Coder-32B-Instruct"
    LLM_TIMEOUT_SECONDS: int = 600

    HF_ENDPOINT: str = "https://hf-mirror.com"

    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def model_post_init(self, __context) -> None:
        os.environ.setdefault("HF_ENDPOINT", self.HF_ENDPOINT)


@lru_cache()
def get_settings() -> Settings:
    return Settings()
