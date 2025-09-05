"""
Protocol-specific configuration parsers.
"""

from .vmess import parse_vmess
from .vless import parse_vless
from .trojan import parse_trojan
from .shadowsocks import parse_ss
from .shadowsocksr import parse_ssr

__all__ = [
    "parse_vmess",
    "parse_vless",
    "parse_trojan",
    "parse_ss",
    "parse_ssr",
]

