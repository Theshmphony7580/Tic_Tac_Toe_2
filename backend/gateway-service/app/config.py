"""
Gateway Service Configuration
Centralized settings for the API Gateway
"""
import os
from typing import Optional


class Settings:
    """Application settings loaded from environment variables"""
    
    # Server
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://admin:password@localhost:5432/talentintel"
    )
    
    # Redis
    REDIS_URL: str = os.getenv(
        "REDIS_URL",
        "redis://localhost:6379/0"
    )
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    
    # API Key Settings
    API_KEY_PREFIX: str = "sk_"
    API_KEY_LENGTH: int = 32
    
    # CORS
    CORS_ORIGINS: list = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")
    
    # Microservices URLs
    PARSER_SERVICE_URL: str = os.getenv(
        "PARSER_SERVICE_URL",
        "http://parser:8001"
    )
    
    NORMALIZATION_SERVICE_URL: str = os.getenv(
        "NORMALIZATION_SERVICE_URL",
        "http://normalizer:8002"
    )
    
    MATCHING_SERVICE_URL: str = os.getenv(
        "MATCHING_SERVICE_URL",
        "http://matcher:8003"
    )
    
    ORCHESTRATOR_SERVICE_URL: str = os.getenv(
        "ORCHESTRATOR_SERVICE_URL",
        "http://orchestrator:8004"
    )
    
    # File Upload Settings
    MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024  # 10MB
    MAX_BATCH_SIZE_BYTES: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_FILE_TYPES: list = ["pdf", "docx", "txt"]
    
    # Supabase (File Storage)
    SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")
    SUPABASE_KEY: Optional[str] = os.getenv("SUPABASE_KEY")
    
    # API Documentation
    API_TITLE: str = "TalentIntel API Gateway"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "API Gateway for Resume Parsing, Skill Matching & Talent Intelligence"
    
    @classmethod
    def log_startup(cls):
        """Log startup configuration (non-sensitive values)"""
        print("\n🚀 TalentIntel Gateway Configuration:")
        print(f"   Debug Mode: {cls.DEBUG}")
        print(f"   Rate Limit: {cls.RATE_LIMIT_PER_MINUTE} req/min")
        print(f"   Database: {cls.DATABASE_URL.split('@')[1] if '@' in cls.DATABASE_URL else 'localhost'}")
        print(f"   Redis: {cls.REDIS_URL.split('@')[1] if '@' in cls.REDIS_URL else 'localhost'}")
        print(f"   Max File Size: {cls.MAX_FILE_SIZE_BYTES / (1024*1024):.1f}MB")
        print(f"   Microservices: Parser={cls.PARSER_SERVICE_URL}")
        print(f"                  Normalizer={cls.NORMALIZATION_SERVICE_URL}")
        print(f"                  Matcher={cls.MATCHING_SERVICE_URL}")
        print()


# Create singleton settings instance
settings = Settings()
