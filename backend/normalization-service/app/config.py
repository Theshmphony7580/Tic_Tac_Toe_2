from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    service_name: str = "talentintel-normalizer"
    
    # Core Infrastructure
    database_url: str = "postgresql://admin:changeme@localhost:5432/talentintel"
    redis_url: str = "redis://localhost:6379/0"
    
    # LLM Settings (for fallback classification)
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"
    llm_timeout_seconds: float = 20.0
    
    # Matching Settings
    fuzz_match_threshold: float = 85.0
    cache_ttl_seconds: int = 86400 # 24 hours

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

def get_settings() -> Settings:
    return Settings()
