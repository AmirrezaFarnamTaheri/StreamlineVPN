"""
Central input validation and sanitization utilities.
Builds on simple policies and provides helpers for URLs, hosts, and config lines.
"""

from __future__ import annotations

import re

from . import policies

HOST_RE = re.compile(r"^[a-zA-Z0-9.-]{1,253}$")


def sanitize_log(value: str) -> str:
    return policies.sanitize_log(value)


def validate_url(url: str) -> str | None:
    if not url or policies.is_malicious_url(url):
        return None
    if policies.has_sql_injection(url) or policies.has_xss_payload(url):
        return None
    return url


def validate_host(host: str) -> str | None:
    if not host:
        return None
    if not HOST_RE.match(host):
        return None
    return host


def validate_config_line(line: str) -> str | None:
    if not line or len(line) > 8192:
        return None
    if policies.contains_malicious_config(line):
        return None
    return line.strip()
