from typing import Optional, Tuple, Dict
import base64
import json
import re
from urllib.parse import urlparse


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
            if isinstance(config, str) and config.startswith(("vmess://", "vless://")):
                try:
                    after = config.split("://", 1)[1]
                    decoded = self._safe_b64_decode(after, self.MAX_DECODE_SIZE)
                    if decoded is not None:
                        data = json.loads(decoded)
                        host = data.get("add") or data.get("host")
                        port = data.get("port")
                        return host, int(port) if port else None
                except Exception:
                    pass
            p = urlparse(config)
            if p.hostname and p.port:
                return p.hostname, p.port
            m = re.search(r"@([^:/?#]+):(\d+)", config)
            if m:
                return m.group(1), int(m.group(2))
        except Exception:
            pass
        return None, None

    def categorize_protocol(self, config: str) -> str:
        mapping = {
            "proxy://": "Proxy",
            "ss://": "Shadowsocks",
            "clash://": "Clash",
            "v2ray://": "V2Ray",
            "reality://": "Reality",
            "vmess://": "VMess",
            "xray://": "XRay",
            "wireguard://": "WireGuard",
            "ech://": "ECH",
            "vless://": "VLESS",
            "hysteria://": "Hysteria",
            "tuic://": "TUIC",
            "sing-box://": "Sing-Box",
            "singbox://": "SingBox",
            "shadowtls://": "ShadowTLS",
            "clashmeta://": "ClashMeta",
            "hysteria2://": "Hysteria2",
        }
        for prefix, proto in mapping.items():
            if isinstance(config, str) and config.startswith(prefix):
                return proto
        return "Other"

    async def test_connection(self, host: str, port: int, protocol: str) -> Tuple[Optional[float], Optional[bool]]:
        # Out-of-scope for core tests; implementation resides in the monolith
        return None, None

    def parse_single_config(self, raw_config: str) -> Optional[Dict]:
        return None


