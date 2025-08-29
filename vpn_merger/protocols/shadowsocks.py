from __future__ import annotations

import base64
import re
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse

from .base import ProtocolHandler


class ShadowsocksHandler(ProtocolHandler):
    """Shadowsocks handler supporting both URI and base64 notation.

    Formats:
      - ss://Y3hhOiFAcHcwcmQ=@host:port#tag  (base64 of method:password)
      - ss://method:password@host:port#tag    (plain)
    """

    def parse(self, raw: str) -> Optional[Dict]:
        if not isinstance(raw, str) or not raw.startswith("ss://"):
            return None
        payload = raw[len("ss://"):]
        # If contains '@', likely plain
        if '@' in payload:
            p = urlparse(raw)
            if p.hostname and p.port:
                return {"host": p.hostname, "port": p.port}
            return None
        # Otherwise treat as base64 credentials optionally followed by @host:port
        # Example: ss://BASE64@host:port
        m = re.search(r"^([^@#]+)/?@([^:/#]+):(\d+)", payload)
        if m:
            host, port = m.group(2), int(m.group(3))
            return {"host": host, "port": port}
        # Or ss://BASE64 only (no endpoint) -> cannot extract
        # Some distributions also encode as ss://BASE64 (method:pwd@host:port)
        try:
            decoded = base64.urlsafe_b64decode(payload + '==').decode('utf-8', 'ignore')
            m2 = re.search(r"@([^:/#]+):(\d+)", decoded)
            if m2:
                return {"host": m2.group(1), "port": int(m2.group(2))}
        except Exception:
            pass
        return None

    def validate(self, config: Dict) -> bool:
        try:
            host = config.get("host")
            port = int(config.get("port")) if config.get("port") is not None else None
            return bool(host) and isinstance(port, int) and 1 <= port <= 65535
        except Exception:
            return False

    def extract_endpoint(self, config: Dict) -> Tuple[str, int]:
        return config.get("host", ""), int(config.get("port") or 0)

    def to_uri(self, config: Dict) -> str:
        host, port = self.extract_endpoint(config)
        return f"ss://{host}:{port}"

    def to_clash(self, config: Dict) -> Dict:
        return {
            "type": "ss",
            "name": "ss",
            "server": config.get("host", ""),
            "port": int(config.get("port") or 0),
        }

    def to_singbox(self, config: Dict) -> Dict:
        return {
            "type": "shadowsocks",
            "server": config.get("host", ""),
            "server_port": int(config.get("port") or 0),
        }

