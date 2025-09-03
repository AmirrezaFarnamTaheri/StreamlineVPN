"""
Tunnel Bridge Merger
===================

Parser for tunnel bridge configurations.
"""

import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def parse_line(line: str) -> str:
    """Validate and normalize proxy URI lines like ssh://, socks5://.
    Returns normalized URI string or raises on invalid.
    """
    if not isinstance(line, str):
        raise TypeError("line must be a string")
    s = line.strip()
    if not s:
        raise ValueError("empty line")
    s = s.lower() if s.split("://", 1)[0].isupper() else s
    parsed = urlparse(s)
    if not parsed.scheme:
        raise ValueError("missing scheme")
    if parsed.scheme not in ("ssh", "socks5"):
        raise ValueError("unsupported scheme")
    # host and port validation
    if not parsed.hostname or not parsed.port:
        raise ValueError("missing host/port")
    # rebuild normalized
    auth = parsed.username or ""
    if parsed.password:
        auth = f"{parsed.username}:{parsed.password}"
    netloc = f"{auth + '@' if auth else ''}{parsed.hostname}:{parsed.port}"
    return f"{parsed.scheme}://{netloc}"
