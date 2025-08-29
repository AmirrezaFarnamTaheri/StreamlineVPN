from __future__ import annotations

import ipaddress
import re
from pathlib import Path
from typing import Optional


class SecurityError(ValueError):
    pass


class SecurityManager:
    """Centralized input/path/url validation helpers."""

    _DOMAIN_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*$")

    @staticmethod
    def sanitize_host(host: Optional[str]) -> Optional[str]:
        if not host or not isinstance(host, str):
            return None
        h = host.strip().strip('[]')
        # Reject any internal whitespace characters
        if re.search(r"[\t\r\n\v\f ]", h):
            raise SecurityError(f"Invalid host (whitespace): {host!r}")
        if not h:
            return None
        # IP check
        try:
            ipaddress.ip_address(h)
            return h
        except ValueError:
            # domain
            if len(h) > 253 or not SecurityManager._DOMAIN_RE.match(h):
                raise SecurityError(f"Invalid host: {h}")
            return h

    @staticmethod
    def sanitize_port(port: Optional[int]) -> Optional[int]:
        try:
            p = int(port) if port is not None else None
        except Exception:
            return None
        if p is None or p < 1 or p > 65535:
            return None
        return p

    @staticmethod
    def secure_path(base_dir: Path, *parts: str) -> Path:
        base = base_dir.resolve()
        target = base.joinpath(*parts).resolve()
        try:
            target.relative_to(base)
        except ValueError:
            raise SecurityError(f"Path traversal attempt: {target}")
        return target
