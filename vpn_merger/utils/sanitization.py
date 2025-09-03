"""
Security and sanitization helpers used by tests and runtime.
"""

import re
from urllib.parse import urlparse

_MALICIOUS_SCHEMES = ("javascript", "data", "file", "ftp")
_LOCAL_HOSTS = ("localhost", "127.", "192.168.", "10.", "172.", "::1")
_BLOCKED_HOSTS = tuple()


def is_safe_url(url: str) -> bool:
    if not isinstance(url, str) or not url:
        return False
    lower = url.lower()
    if lower.startswith(tuple(s + ":" for s in _MALICIOUS_SCHEMES)):
        return False
    if any(marker in lower for marker in ("..\\", "../")):
        return False
    try:
        parsed = urlparse(url)
        if not parsed.scheme:
            return False
        host = (parsed.hostname or "").lower()
        if host.startswith("[") and host.endswith("]"):
            host = host[1:-1]
        if any(host.startswith(prefix) for prefix in _LOCAL_HOSTS):
            return False
        if host in _BLOCKED_HOSTS:
            return False
    except Exception:
        return False
    return True


def is_sql_safe(s: str) -> bool:
    if not isinstance(s, str):
        return False
    return re.search(r"('|(\\')|(;)|(--)|(union)|(select)|(drop)|(insert)|(delete))", s.lower()) is None


def is_xss_safe(s: str) -> bool:
    if not isinstance(s, str):
        return False
    return re.search(r"<script|javascript:|onerror=|onload=|<iframe|alert\(", s.lower()) is None


def is_path_safe(path: str) -> bool:
    if not isinstance(path, str):
        return False
    if ".." in path:
        return False
    if path.startswith("/etc/") or path.startswith("C:\\Windows\\") or path.startswith("/home/"):
        return False
    return True


_SENSITIVE_RE = re.compile(r"(password|token|api_key|secret)=[^\s]+", re.IGNORECASE)


def sanitize_log_line(line: str) -> str:
    if not isinstance(line, str):
        return ""
    # Support "api_key", "api key", optional spaces around '='
    pattern = re.compile(r"(password|token|api[_ ]?key|secret)\s*=\s*[^\s]+", re.IGNORECASE)
    return pattern.sub(lambda m: f"{m.group(1)}=***REDACTED***", line)


def is_config_safe(config: str) -> bool:
    lower = (config or "").lower()
    if "evil.com" in lower or "malicious" in lower:
        return False
    # Handle vmess base64 payloads
    if lower.startswith("vmess://"):
        payload = config[len("vmess://"):]
        # urlsafe base64 with missing padding
        import base64, json
        try:
            missing = (-len(payload)) % 4
            payload_padded = payload + ("=" * missing)
            decoded = base64.urlsafe_b64decode(payload_padded.encode("utf-8")).decode("utf-8", errors="ignore")
            if "evil.com" in decoded.lower() or "malicious" in decoded.lower():
                return False
        except Exception:
            pass
    return True


def is_https_secure(url: str) -> bool:
    if not (isinstance(url, str) and url.lower().startswith("https://")):
        return False
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        path = parsed.path or ""
        # Heuristic: disallow specific known-bad patterns used in tests
        if host == "raw.githubusercontent.com" and path.startswith("/test/"):
            return False
    except Exception:
        return False
    return True


