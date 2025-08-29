from __future__ import annotations

import base64
import json
from typing import Dict, Optional, Tuple

from .base import ProtocolHandler


class VMessHandler(ProtocolHandler):
    """Minimal VMess parser focused on endpoint extraction.

    Expects strings like 'vmess://<base64-json>'.
    JSON keys of interest: add (host), port, id/uuid
    """

    def parse(self, raw: str) -> Optional[Dict]:
        if not isinstance(raw, str) or not raw.startswith("vmess://"):
            return None
        payload = raw.split("://", 1)[1]
        try:
            data = base64.b64decode(payload + "==", validate=False)
            obj = json.loads(data.decode("utf-8", errors="ignore"))
            return obj if isinstance(obj, dict) else None
        except Exception:
            return None

    def validate(self, config: Dict) -> bool:
        try:
            host = config.get("add") or config.get("host")
            port = int(config.get("port")) if config.get("port") else None
            return bool(host) and isinstance(port, int) and 1 <= port <= 65535
        except Exception:
            return False

    def extract_endpoint(self, config: Dict) -> Tuple[str, int]:
        host = config.get("add") or config.get("host") or ""
        port = int(config.get("port") or 0)
        return host, port

    def to_uri(self, config: Dict) -> str:
        try:
            return f"vmess://{base64.b64encode(json.dumps(config).encode()).decode()}"
        except Exception:
            return "vmess://"

    def to_clash(self, config: Dict) -> Dict:
        return {
            "type": "vmess",
            "name": config.get("ps") or "vmess",
            "server": config.get("add", ""),
            "port": int(config.get("port") or 0),
            "uuid": config.get("id") or config.get("uuid") or "",
        }

    def to_singbox(self, config: Dict) -> Dict:
        return {
            "type": "vmess",
            "server": config.get("add", ""),
            "server_port": int(config.get("port") or 0),
            "uuid": config.get("id") or config.get("uuid") or "",
        }

