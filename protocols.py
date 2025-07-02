from typing import Dict

PROTOCOL_MAP: Dict[str, str] = {
    "vmess://": "VMess",
    "vless://": "VLESS",
    "ss://": "Shadowsocks",
    "trojan://": "Trojan",
    "hy2://": "Hysteria2",
    "hysteria2://": "Hysteria2",
    "hysteria://": "Hysteria",
    "tuic://": "TUIC",
    "reality://": "Reality",
    "naive://": "Naive",
    "juicity://": "Juicity",
    "wireguard://": "WireGuard",
    "shadowtls://": "ShadowTLS",
    "brook://": "Brook",
}


def categorize_protocol(config: str) -> str:
    """Categorize configuration by protocol."""
    for prefix, protocol in PROTOCOL_MAP.items():
        if config.startswith(prefix):
            return protocol
    return "Other"

