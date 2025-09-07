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


settings = Settings()
