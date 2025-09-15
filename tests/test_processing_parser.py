import base64
import json

from streamline_vpn.core.processing.parser import ConfigurationParser
from streamline_vpn.models.configuration import Protocol


def b64(s: str) -> str:
    raw = s.encode("utf-8")
    enc = base64.b64encode(raw).decode("utf-8")
    return enc


def test_parse_vmess_valid_and_invalid():
    parser = ConfigurationParser()
    vmess_obj = {
        "add": "vmess.test-server.example",
        "port": 443,
        "id": "uuid-1",
        "net": "ws",
        "path": "/ws",
        "host": "host.test-server.example",
        "tls": "tls",
        "scy": "auto",
    }
    vmess_cfg = f"vmess://{b64(json.dumps(vmess_obj))}"
    cfg = parser.parse_configuration(vmess_cfg)
    assert cfg is not None
    assert cfg.protocol == Protocol.VMESS
    assert cfg.server == "vmess.test-server.example"
    assert cfg.tls is True

    assert parser.parse_configuration("") is None
    assert parser.parse_configuration("vmess://notbase64") is None


def test_parse_vless_trojan_ss_ssr():
    parser = ConfigurationParser()

    # VLESS
    vless_cfg = (
        "vless://user@vless.test-server.example:8443?type=ws&path=%2Fws&host=ex.com&security=tls"
    )
    cfg_vless = parser.parse_configuration(vless_cfg)
    assert cfg_vless is not None and cfg_vless.protocol == Protocol.VLESS
    assert cfg_vless.tls is True

    # Trojan
    trojan_cfg = "trojan://password@trojan.test-server.example:443#frag"
    cfg_trojan = parser.parse_configuration(trojan_cfg)
    assert cfg_trojan is not None and cfg_trojan.protocol == Protocol.TROJAN
    assert cfg_trojan.password == "password"

    # Shadowsocks
    ss_auth = "aes-256-gcm:pass@ss.test-server.example:8388"
    ss_cfg = f"ss://{b64(ss_auth)}"
    cfg_ss = parser.parse_configuration(ss_cfg)
    assert cfg_ss is not None and cfg_ss.protocol == Protocol.SHADOWSOCKS
    assert cfg_ss.encryption == "aes-256-gcm"

    # ShadowsocksR
    ssr_pwd_b64 = base64.b64encode(b"pass").decode("utf-8")
    ssr_main = f"ssr.test-server.example:443:tcp:aes-256-cfb:plain:{ssr_pwd_b64}"
    ssr_cfg = f"ssr://{b64(ssr_main)}"
    cfg_ssr = parser.parse_configuration(ssr_cfg)
    assert cfg_ssr is not None and cfg_ssr.protocol == Protocol.SHADOWSOCKSR

