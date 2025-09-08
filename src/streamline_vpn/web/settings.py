from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    HOST: str = "0.0.0.0"
    PORT: int = 8000
    STATIC_DIR: str = "docs"
    API_BASE: str = "http://localhost:8080"
    UPDATE_INTERVAL: int = 28800  # 8 hours in seconds

    # CORS settings for static server
    ALLOWED_ORIGINS: list[str] = ["*"]
    ALLOWED_METHODS: list[str] = ["GET"]
    ALLOWED_HEADERS: list[str] = ["Content-Type"]
    ALLOW_CREDENTIALS: bool = False


settings = Settings()
