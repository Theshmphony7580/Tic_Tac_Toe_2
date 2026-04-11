from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    service_name: str = "talentintel-matcher"

    # Database (Supabase Postgres)
    database_url: str = "postgresql://postgres:ipQSzoJqgTyjM2mK@db.gwsfdlnfrdasntqyffdo.supabase.co:5432/postgres"

    # Embedding model (sentence-transformers)
    embedding_model: str = "all-MiniLM-L6-v2"

    # Matching defaults
    default_threshold: float = 0.55   # lower than ideal — more candidates returned
    default_top_k: int = 10
    max_top_k: int = 50

    # Score weights defaults
    default_weight_skill_match: float = 0.5
    default_weight_experience_depth: float = 0.3
    default_weight_education_relevance: float = 0.2

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

def get_settings() -> Settings:
    return Settings()
