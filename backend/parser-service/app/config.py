from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    groq_api_key: str
    supabase_url: str | None = None
    supabase_key: str | None = None
    groq_model: str = "llama-3.1-8b-instant"
    max_file_size_mb: int = 10
    parser_timeout_seconds: int = 30
    service_name: str = "parser-service"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

@lru_cache
def get_settings():
    return Settings()

settings = get_settings()
