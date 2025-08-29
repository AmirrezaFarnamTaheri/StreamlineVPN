from __future__ import annotations

from typing import Dict, Optional

from .vmess import VMessHandler
from .vless import VLESSHandler
from .trojan import TrojanHandler
from .shadowsocks import ShadowsocksHandler
from .reality import RealityHandler
from .hysteria2 import Hysteria2Handler
from .tuic import TUICHandler


_MAP: Dict[str, object] = {
    "vmess": VMessHandler(),
    "vless": VLESSHandler(),
    "trojan": TrojanHandler(),
    "ss": ShadowsocksHandler(),
    "reality": RealityHandler(),
    "hysteria2": Hysteria2Handler(),
    "tuic": TUICHandler(),
}


def get_handler(proto: str) -> Optional[object]:
    return _MAP.get(proto.lower())

