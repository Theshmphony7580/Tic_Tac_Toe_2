from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    service_name: str = "talentintel-orchestrator"

    # Supabase PostgreSQL — same DB used by Normalizer + Matcher
    database_url: str = "postgresql://postgres:ipQSzoJqgTyjM2mK@db.gwsfdlnfrdasntqyffdo.supabase.co:5432/postgres"

    # Redis — Celery broker + result backend
    redis_url: str = "redis://localhost:6379/0"

    # Internal service URLs (local dev)
    # Note: Parser runs on 8005, NOT 8001 (8001 is hijacked by Docker)
    parser_url: str = "http://localhost:8005"
    normalizer_url: str = "http://localhost:8002"

    # Embedding model — same as Matcher Service
    embedding_model: str = "all-MiniLM-L6-v2"

    # HTTP timeouts
    parser_timeout_seconds: float = 60.0
    normalizer_timeout_seconds: float = 30.0

    # Max retry attempts per LangGraph node before giving up
    max_retries: int = 3

    # Local testing: Enable Celery Eager mode to bypass Redis dependency
    celery_task_always_eager: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
