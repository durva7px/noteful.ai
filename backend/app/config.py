from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    pinecone_api_key: str = ""
    anthropic_api_key: str = ""

    pinecone_index: str = "noteful"
    pinecone_cloud: str = "aws"
    pinecone_region: str = "us-east-1"
    pinecone_namespace: str = "default"
    embedding_model: str = "llama-text-embed-v2"
    embedding_dim: int = 1024

    llm_model: str = "claude-sonnet-5-5"
    # Sonnet 5.5 rejects custom temperature; effort controls depth instead (low | medium | high).
    llm_effort: str = "medium"
    # Adaptive thinking counts toward this budget, so leave headroom beyond the visible answer.
    llm_max_tokens: int = 16000

    chunk_size: int = 1000
    chunk_overlap: int = 150
    retrieval_k: int = 6
    score_threshold: float = 0.3
    history_turns: int = 6

    max_upload_mb: int = 25
    upload_dir: Path = BACKEND_DIR / "uploads"
    database_url: str = f"sqlite:///{(BACKEND_DIR / 'noteful.db').as_posix()}"
    cors_origins: list[str] = ["http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
