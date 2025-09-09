from __future__ import annotations

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore",
        env_parse_none_str="None"
    )

    HOST: str = "0.0.0.0"
    PORT: int = 8000
    STATIC_DIR: str = "docs"
    API_BASE: str = "http://localhost:8080"
    UPDATE_INTERVAL: int = 28800  # 8 hours in seconds

    # CORS settings for static server
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000", "http://localhost:8080"]
    ALLOWED_METHODS: list[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    ALLOWED_HEADERS: list[str] = ["Content-Type", "Authorization", "X-Requested-With"]
    ALLOW_CREDENTIALS: bool = True
    
    @field_validator('ALLOWED_ORIGINS', mode='before')
    @classmethod
    def parse_allowed_origins(cls, v):
        """Parse comma-separated origins string into list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v
    
    @field_validator('ALLOWED_METHODS', mode='before')
    @classmethod
    def parse_allowed_methods(cls, v):
        """Parse comma-separated methods string into list."""
        if isinstance(v, str):
            return [method.strip() for method in v.split(',') if method.strip()]
        return v
    
    @field_validator('ALLOWED_HEADERS', mode='before')
    @classmethod
    def parse_allowed_headers(cls, v):
        """Parse comma-separated headers string into list."""
        if isinstance(v, str):
            return [header.strip() for header in v.split(',') if header.strip()]
        return v


# Lazy initialization to avoid import-time errors
_settings_instance = None

def get_settings():
    """Get settings instance with lazy initialization."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance
