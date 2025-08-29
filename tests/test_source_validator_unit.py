import pytest

from vpn_merger.sources.validator import SourceValidator


def test_estimate_configs_counts_known_prefixes():
    sv = SourceValidator()
    content = "\n".join([
        "vmess://abc",
        "vless://def",
        " trojan://ghi",  # leading space should be ignored
        "ss://jkl",
        "random text",
        "hysteria2://mno",
        "tuic://pqr",
    ])
    assert sv._estimate_configs(content) == 6


def test_detect_protocols_maps_to_names():
    sv = SourceValidator()
    content = "vmess://x vless://y trojan://z ss://w ssr://v hysteria://h hysteria2://h2 tuic://t"
    protos = set(sv._detect_protocols(content))
    assert {
        "vmess",
        "vless",
        "trojan",
        "shadowsocks",
        "shadowsocksr",
        "hysteria",
        "hysteria2",
        "tuic",
    }.issubset(protos)

