"""
Security Policies Helpers
=========================

Lightweight helpers used by tests for detecting risky inputs and sanitizing logs.
"""

import re
from typing import List


FORBIDDEN_URL_PREFIXES = ("javascript:", "data:", "file:", "ftp:")
LOCAL_HOST_MARKERS = ("localhost", "127.0.0.1", "192.168.", "10.", "172.")


def is_malicious_url(url: str) -> bool:
    u = (url or "").lower()
    if u.startswith(FORBIDDEN_URL_PREFIXES):
        return True
    if any(m in u for m in LOCAL_HOST_MARKERS):
        return True
    if "../" in u or "..\\" in u:
        return True
    return False


SQLI_RE = re.compile(r"('|(\\')|(;)|(--)|(union)|(select)|(drop)|(insert)|(delete))", re.I)
XSS_RE = re.compile(r"<script|javascript:|onerror=|onload=|<iframe", re.I)


def has_sql_injection(s: str) -> bool:
    return bool(SQLI_RE.search((s or "").lower()))


def has_xss_payload(s: str) -> bool:
    return bool(XSS_RE.search((s or "").lower()))


def contains_malicious_config(cfg: str) -> bool:
    c = (cfg or "").lower()
    if "evil.com" in c:
        return True
    if "malicious" in c:
        return True
    return False


def sanitize_log(line: str) -> str:
    return re.sub(r"(password|token|api_key|secret)=[^\s]+", r"\1=***REDACTED***", line or "")


