from __future__ import annotations

from typing import Optional, Tuple, Dict

from vpn_merger.protocols.base import ProtocolHandler
from vpn_merger.protocols.vmess import VMessHandler
from vpn_merger.protocols.vless import VLESSHandler
from vpn_merger.protocols.trojan import TrojanHandler
from vpn_merger.protocols.shadowsocks import ShadowsocksHandler
from vpn_merger.protocols.hysteria2 import Hysteria2Handler
from vpn_merger.protocols.tuic import TUICHandler
from vpn_merger.protocols.reality import RealityHandler


class ProtocolParser:
    """Central parser that delegates to protocol handlers.

    Provides static helpers so callers don’t need to instantiate.
    """

    _HANDLERS: Dict[str, ProtocolHandler] = {
        "vmess://": VMessHandler(),
        "vless://": VLESSHandler(),
        "trojan://": TrojanHandler(),
        "ss://": ShadowsocksHandler(),
        "hysteria2://": Hysteria2Handler(),
        "tuic://": TUICHandler(),
        "reality://": RealityHandler(),
    }

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
        for prefix, handler in ProtocolParser._HANDLERS.items():
            if raw.startswith(prefix):
                parsed = handler.parse(raw)
                if parsed and handler.validate(parsed):
                    host, port = handler.extract_endpoint(parsed)
                    return host or None, int(port) if port else None
                break
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
