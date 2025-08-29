from __future__ import annotations

from typing import Optional, Tuple, Dict

from vpn_merger.protocols.base import ProtocolHandler
from vpn_merger.protocols.factory import get_handler


class ProtocolParser:
    """Central parser that delegates to protocol handlers.

    Provides static helpers so callers don’t need to instantiate.
    """

    _HANDLERS: Dict[str, ProtocolHandler] = {}

    @staticmethod
    def categorize(raw: str) -> str:
        mapping = {
            "proxy://": "Proxy",
            "ss://": "Shadowsocks",
            "trojan://": "Trojan",
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
        if not isinstance(raw, str):
            return "Other"
        for prefix, proto in mapping.items():
            if raw.startswith(prefix):
                return proto
        return "Other"

    @staticmethod
    def extract_endpoint(raw: str) -> Tuple[Optional[str], Optional[int]]:
        if not isinstance(raw, str) or len(raw) < 6:
            return None, None
        # Use factory to resolve handler by scheme
        try:
            scheme = raw.split("://", 1)[0].lower() + "://"
        except Exception:
            scheme = ""
        proto = scheme.replace("://", "")
        handler = get_handler(proto)
        if handler:
            parsed = handler.parse(raw)  # type: ignore[attr-defined]
            try:
                valid = handler.validate(parsed)  # type: ignore[attr-defined]
            except Exception:
                valid = False
            if parsed and valid:
                try:
                    host, port = handler.extract_endpoint(parsed)  # type: ignore[attr-defined]
                    return host or None, int(port) if port else None
                except Exception:
                    pass
        # Fallback: no dedicated handler matched or parse failed
        try:
            from urllib.parse import urlparse
            import re
            p = urlparse(raw)
            if p.hostname and p.port:
                return p.hostname, p.port
            m = re.search(r"@([^:/?#]+):(\d+)", raw)
            if m:
                return m.group(1), int(m.group(2))
        except Exception:
            pass
        return None, None
