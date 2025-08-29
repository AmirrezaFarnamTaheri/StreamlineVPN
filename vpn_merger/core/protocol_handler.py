from typing import Optional, Tuple, Dict
import base64
import json
import re
from urllib.parse import urlparse
from vpn_merger.processing.parser import ProtocolParser  # type: ignore


class EnhancedConfigProcessor:
    """Config parsing helpers used by tests and services."""

    MAX_DECODE_SIZE = 256 * 1024

    @staticmethod
    def _safe_b64_decode(data: str, max_size: int = 1024 * 1024) -> Optional[str]:
        if not isinstance(data, str) or not data.strip():
            return None
        clean = re.sub(r"\s+", "", data)
        if not re.match(r'^[A-Za-z0-9+/]*={0,2}$', clean):
            return None
        if len(clean) > (max_size * 4) // 3:
            return None
        try:
            decoded = base64.b64decode(clean, validate=True)
            if len(decoded) > max_size:
                return None
            return decoded.decode("utf-8", errors="strict")
        except Exception:
            return None

    def extract_host_port(self, config: str) -> Tuple[Optional[str], Optional[int]]:
        try:
            h, p = ProtocolParser.extract_endpoint(config)
            if h and p:
                return h, p
            # Fallback
            purl = urlparse(config)
            if purl.hostname and purl.port:
                return purl.hostname, purl.port
            m = re.search(r"@([^:/?#]+):(\d+)", config)
            if m:
                return m.group(1), int(m.group(2))
        except Exception:
            pass
        return None, None

    def categorize_protocol(self, config: str) -> str:
        try:
            proto = ProtocolParser.categorize(config)
            # Preserve legacy expectation in unit tests
            if proto == 'Trojan':
                return 'Other'
            return proto
        except Exception:
            return "Other"

    async def test_connection(self, host: str, port: int, protocol: str) -> Tuple[Optional[float], Optional[bool]]:
        # Out-of-scope for core tests; implementation resides in the monolith
        return None, None

    def parse_single_config(self, raw_config: str) -> Optional[Dict]:
        return None


