"""
Settings and Runtime Overrides
==============================

Central place for system-wide defaults and helpers to apply environment-based
overrides at runtime without code changes.
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import List

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

    model_config = SettingsConfigDict(env_prefix='STREAMLINE_FETCHER_')


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
    safe_ports: List[int] = [80, 443, 8080, 8443, 53, 853, 123, 993, 995, 587, 465, 993, 995]
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

    model_config = SettingsConfigDict(env_prefix='STREAMLINE_SECURITY_')


from pydantic import Field

class Settings(BaseSettings):
    fetcher: FetcherSettings = Field(default_factory=FetcherSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
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

    model_config = SettingsConfigDict(env_file='.env', env_nested_delimiter='__')


@lru_cache()
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    """Reset cached Settings to pick up environment changes."""
    try:
        # Available on functools.lru_cache-wrapped callables
        get_settings.cache_clear()  # type: ignore[attr-defined]
    except Exception:
        # Be tolerant in environments where cache_clear isn't available
        pass
