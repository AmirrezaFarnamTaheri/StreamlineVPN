"""
Settings and Runtime Overrides
==============================

Central place for system-wide defaults and helpers to apply environment-based
overrides at runtime without code changes.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Dict, List

from pydantic import Field
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class FetcherSettings(BaseSettings):
    max_concurrent: int = 50
    timeout_seconds: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0
    cb_failure_threshold: int = 5
    cb_recovery_timeout_seconds: int = 60
    rl_max_requests: int = 60
    rl_time_window_seconds: int = 60
    rl_burst_limit: int = 10

    model_config = SettingsConfigDict(env_prefix="STREAMLINE_FETCHER_")


class SecuritySettings(BaseSettings):
    suspicious_tlds: List[str] = [".tk", ".ml", ".ga", ".cf", ".pw"]
    safe_protocols: List[str] = [
        "http",
        "https",
        "vmess",
        "vless",
        "trojan",
        "ss",
        "ssr",
        "hysteria",
        "hysteria2",
        "tuic",
    ]
    safe_encryptions: List[str] = [
        "aes-256-gcm",
        "aes-128-gcm",
        "chacha20-poly1305",
        "aes-256-cfb",
        "aes-128-cfb",
        "rc4-md5",
        "none",
    ]
    safe_ports: List[int] = [
        80,
        443,
        8080,
        8443,
        53,
        853,
        123,
        993,
        995,
        587,
        465,
    ]
    suspicious_text_patterns: List[str] = [
        r"<script",
        r"javascript:",
        r"eval\s*\(",
        r"exec\s*\(",
        r"__import__",
        r"subprocess",
        r"os\.system",
        r"rm\s+-rf",
        r"wget\s+",
        r"curl\s+",
        r"nc\s+",
        r"netcat",
        r"bash\s+",
        r"sh\s+",
        r"powershell",
        r"cmd\s+",
        r"ftp\s+",
        r"telnet\s+",
        r"ssh\s+",
        r"scp\s+",
        r"rsync\s+",
    ]

    model_config = SettingsConfigDict(env_prefix="STREAMLINE_SECURITY_")


class RedisSettings(BaseSettings):
    nodes: List[Dict[str, str]] = [{"host": "redis", "port": "6379"}]

    model_config = SettingsConfigDict(env_prefix="STREAMLINE_REDIS_")


class Settings(BaseSettings):
    secret_key: str = "CHANGE_THIS_IN_PRODUCTION_USE_ENVIRONMENT_VARIABLE"  # WARNING: Change in production!
    fetcher: FetcherSettings = Field(default_factory=FetcherSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    supported_protocol_prefixes: List[str] = [
        "vmess://",
        "vless://",
        "trojan://",
        "ss://",
        "ssr://",
        "hysteria://",
        "hysteria2://",
        "tuic://",
    ]

    # CORS settings
    allowed_origins: List[str] = Field(default=["http://localhost:3000", "http://localhost:8000", "http://localhost:8080"], alias="ALLOWED_ORIGINS")  # WARNING: Restrict in production!
    allowed_methods: List[str] = Field(default=["GET", "POST", "PUT", "DELETE", "OPTIONS"], alias="ALLOWED_METHODS")
    allowed_headers: List[str] = Field(default=["Content-Type", "Authorization", "X-Requested-With"], alias="ALLOWED_HEADERS")
    allow_credentials: bool = Field(default=True, alias="ALLOW_CREDENTIALS")

    model_config = SettingsConfigDict(
        env_file=".env", env_nested_delimiter="__", extra="ignore"
    )

    # Accept comma-separated strings for list env vars for convenience
    @field_validator("allowed_origins", "allowed_methods", "allowed_headers", mode="before")
    @classmethod
    def _parse_comma_separated(cls, v):  # type: ignore[override]
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v


@lru_cache()
def get_settings() -> Settings:
    try:
        return Settings()
    except Exception:
        # In some environments (e.g., tests), .env may contain comma-separated
        # lists which pydantic-settings expects as JSON arrays. Attempt a
        # best-effort normalization by reading common keys and exporting JSON
        # equivalents into os.environ, then retry.
        import os
        from json import dumps

        def _normalize_env_list(key: str) -> None:
            val = os.environ.get(key)
            if not val:
                # Try reading from .env file directly
                try:
                    with open(".env", "r", encoding="utf-8") as fh:
                        for line in fh:
                            if line.strip().startswith(f"{key}="):
                                _, raw = line.split("=", 1)
                                val = raw.strip().strip('"').strip("'")
                                break
                except Exception:
                    val = None
            if val and not val.strip().startswith("["):
                items = [s.strip() for s in val.split(",") if s.strip()]
                os.environ[key] = dumps(items)

        for k in ("ALLOWED_ORIGINS", "ALLOWED_METHODS", "ALLOWED_HEADERS"):
            _normalize_env_list(k)

        # As a last resort, construct a Settings instance that ignores .env
        # file parsing to avoid complex type decoding during tests.
        class _SafeSettings(Settings):  # type: ignore
            model_config = SettingsConfigDict(env_file=None, env_nested_delimiter="__")

        return _SafeSettings()


def reset_settings_cache() -> None:
    """Reset cached Settings to pick up environment changes."""
    try:
        # Available on functools.lru_cache-wrapped callables
        get_settings.cache_clear()  # type: ignore[attr-defined]
    except Exception:
        # Be tolerant in environments where cache_clear isn't available
        pass
