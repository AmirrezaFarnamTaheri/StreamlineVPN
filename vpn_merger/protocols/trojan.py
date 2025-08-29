from __future__ import annotations

from typing import Dict, Optional, Tuple
from urllib.parse import urlparse

from .base import ProtocolHandler


class TrojanHandler(ProtocolHandler):
    """Trojan handler using URI parsing (trojan://user@host:port)."""

    def parse(self, raw: str) -> Optional[Dict]:
        if not isinstance(raw, str) or not raw.startswith("trojan://"):
            return None
        p = urlparse(raw)
        if not p.hostname or not p.port:
            return None
        return {"host": p.hostname, "port": p.port}

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
        return f"trojan://{host}:{port}"

    def to_clash(self, config: Dict) -> Dict:
        return {
            "type": "trojan",
            "name": "trojan",
            "server": config.get("host", ""),
            "port": int(config.get("port") or 0),
        }

    def to_singbox(self, config: Dict) -> Dict:
        return {
            "type": "trojan",
            "server": config.get("host", ""),
            "server_port": int(config.get("port") or 0),
        }

