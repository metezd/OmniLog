from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    
    # === Database ===
    database_url: str = "postgresql://omnilog:omnilog_password@localhost:5432/omnilog_db"
    database_echo: bool = False
    
    # === Redis ===
    redis_url: str = "redis://localhost:6379/0"
    
    # === JWT & Security ===
    secret_key: str = "your-super-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # === External APIs ===
    igdb_client_id: Optional[str] = None
    igdb_client_secret: Optional[str] = None
    tmdb_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    
    igdb_base_url: str = "https://api.igdb.com/v4"
    tmdb_base_url: str = "https://api.themoviedb.org/3"
    
    # === Application ===
    debug: bool = True
    environment: str = "development"
    log_level: str = "INFO"
    
    # === CORS ===
    allowed_origins: list = ["http://localhost:3000", "http://localhost:8000"]
    
    # === App Info ===
    app_name: str = "OmniLog API"
    app_version: str = "1.0.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get settings singleton instance (cached)"""
    return Settings()
