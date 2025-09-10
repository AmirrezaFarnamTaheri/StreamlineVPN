from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    HOST: str = "0.0.0.0"
    PORT: int = 8000
    STATIC_DIR: str = "docs"
    # Support both API_BASE and API_BASE_URL environment variables
    API_BASE: str = Field(default="http://localhost:8080", alias="API_BASE_URL")
    UPDATE_INTERVAL: int = 28800  # 8 hours in seconds

    # CORS settings for static server
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000", "http://localhost:8080"]
    ALLOWED_METHODS: list[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    ALLOWED_HEADERS: list[str] = ["Content-Type", "Authorization", "X-Requested-With"]
    ALLOW_CREDENTIALS: bool = True


settings = Settings()
