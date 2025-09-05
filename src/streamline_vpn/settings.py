"""
Settings and Runtime Overrides
==============================

Central place for system-wide defaults and helpers to apply environment-based
overrides at runtime without code changes.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List


def _split_csv_env(name: str) -> List[str]:
    v = os.getenv(name)
    if not v:
        return []
    return [item.strip() for item in v.split(",") if item.strip()]


def _split_csv_int_env(name: str) -> List[int]:
    items = _split_csv_env(name)
    out: List[int] = []
    for it in items:
        try:
            out.append(int(it))
        except ValueError:
            continue
    return out


# Defaults
FETCHER_MAX_CONCURRENT_DEFAULT = 50
FETCHER_TIMEOUT_SECONDS_DEFAULT = 30
FETCHER_RETRY_ATTEMPTS_DEFAULT = 3
FETCHER_RETRY_DELAY_DEFAULT = 1.0

FETCHER_CB_FAILURE_THRESHOLD_DEFAULT = 5
FETCHER_CB_RECOVERY_TIMEOUT_SECONDS_DEFAULT = 60

FETCHER_RL_MAX_REQUESTS_DEFAULT = 60
FETCHER_RL_TIME_WINDOW_SECONDS_DEFAULT = 60
FETCHER_RL_BURST_LIMIT_DEFAULT = 10

SECURITY_SUSPICIOUS_TLDS_DEFAULT = [".tk", ".ml", ".ga", ".cf", ".pw"]
SECURITY_SAFE_PROTOCOLS_DEFAULT = [
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
SECURITY_SAFE_ENCRYPTIONS_DEFAULT = [
    "aes-256-gcm",
    "aes-128-gcm",
    "chacha20-poly1305",
    "aes-256-cfb",
    "aes-128-cfb",
    "rc4-md5",
    "none",
]
SECURITY_SAFE_PORTS_DEFAULT = [80, 443, 8080, 8443, 53, 853, 123, 993, 995, 587, 465, 993, 995]
SECURITY_SUSPICIOUS_TEXT_PATTERNS_DEFAULT = [
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
SUPPORTED_VPN_PROTOCOL_PREFIXES_DEFAULT = [
    "vmess://",
    "vless://",
    "trojan://",
    "ss://",
    "ssr://",
    "hysteria://",
    "hysteria2://",
    "tuic://",
]


@dataclass
class FetcherSettings:
    max_concurrent: int
    timeout_seconds: int
    retry_attempts: int
    retry_delay: float
    cb_failure_threshold: int
    cb_recovery_timeout_seconds: int
    rl_max_requests: int
    rl_time_window_seconds: int
    rl_burst_limit: int


def get_fetcher_settings() -> FetcherSettings:
    return FetcherSettings(
        max_concurrent=int(os.getenv("STREAMLINE_FETCHER_MAX_CONCURRENT", FETCHER_MAX_CONCURRENT_DEFAULT)),
        timeout_seconds=int(os.getenv("STREAMLINE_FETCHER_TIMEOUT_SECONDS", FETCHER_TIMEOUT_SECONDS_DEFAULT)),
        retry_attempts=int(os.getenv("STREAMLINE_FETCHER_RETRY_ATTEMPTS", FETCHER_RETRY_ATTEMPTS_DEFAULT)),
        retry_delay=float(os.getenv("STREAMLINE_FETCHER_RETRY_DELAY", FETCHER_RETRY_DELAY_DEFAULT)),
        cb_failure_threshold=int(
            os.getenv("STREAMLINE_FETCHER_CB_FAILURE_THRESHOLD", FETCHER_CB_FAILURE_THRESHOLD_DEFAULT)
        ),
        cb_recovery_timeout_seconds=int(
            os.getenv(
                "STREAMLINE_FETCHER_CB_RECOVERY_TIMEOUT_SECONDS",
                FETCHER_CB_RECOVERY_TIMEOUT_SECONDS_DEFAULT,
            )
        ),
        rl_max_requests=int(os.getenv("STREAMLINE_FETCHER_RL_MAX_REQUESTS", FETCHER_RL_MAX_REQUESTS_DEFAULT)),
        rl_time_window_seconds=int(
            os.getenv("STREAMLINE_FETCHER_RL_TIME_WINDOW_SECONDS", FETCHER_RL_TIME_WINDOW_SECONDS_DEFAULT)
        ),
        rl_burst_limit=int(os.getenv("STREAMLINE_FETCHER_RL_BURST_LIMIT", FETCHER_RL_BURST_LIMIT_DEFAULT)),
    )


@dataclass
class SecuritySettings:
    suspicious_tlds: List[str]
    safe_protocols: List[str]
    safe_encryptions: List[str]
    safe_ports: List[int]
    suspicious_text_patterns: List[str]


def get_security_settings() -> SecuritySettings:
    tlds = _split_csv_env("STREAMLINE_SECURITY_SUSPICIOUS_TLDS") or SECURITY_SUSPICIOUS_TLDS_DEFAULT
    protocols = _split_csv_env("STREAMLINE_SECURITY_SAFE_PROTOCOLS") or SECURITY_SAFE_PROTOCOLS_DEFAULT
    encryptions = _split_csv_env("STREAMLINE_SECURITY_SAFE_ENCRYPTIONS") or SECURITY_SAFE_ENCRYPTIONS_DEFAULT
    ports = _split_csv_int_env("STREAMLINE_SECURITY_SAFE_PORTS") or SECURITY_SAFE_PORTS_DEFAULT
    patterns = _split_csv_env("STREAMLINE_SECURITY_SUSPICIOUS_TEXT_PATTERNS") or SECURITY_SUSPICIOUS_TEXT_PATTERNS_DEFAULT
    return SecuritySettings(tlds, protocols, encryptions, ports, patterns)


def get_supported_protocol_prefixes() -> List[str]:
    vals = _split_csv_env("STREAMLINE_SUPPORTED_PROTOCOL_PREFIXES")
    return vals or SUPPORTED_VPN_PROTOCOL_PREFIXES_DEFAULT
