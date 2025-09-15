import asyncio
import pytest

from streamline_vpn.core.processing.parsers.shadowsocks2022_parser import (
    Shadowsocks2022Parser,
    parse_ss2022_async,
    get_ss2022_parser_stats,
)
from streamline_vpn.models.configuration import Protocol


@pytest.mark.asyncio
async def test_ss2022_parser_valid_uri():
    parser = Shadowsocks2022Parser()
    uri = "ss://2022-aes-256-gcm:passw0rd@test-server.example:8388?plugin=none"
    cfg = await parser.parse(uri)
    assert cfg is not None
    assert cfg.protocol == Protocol.SHADOWSOCKS
    assert cfg.server == "test-server.example"
    assert cfg.port == 8388
    assert cfg.password == "passw0rd"
    assert cfg.encryption == "aes-256-gcm"
    meta = cfg.metadata
    assert meta.get("parser") == "optimized_ss2022"
    assert meta.get("aead_support") is True
    assert parser.get_performance_stats()["parse_count"] >= 1


@pytest.mark.asyncio
async def test_ss2022_parser_invalid_uri_returns_none():
    parser = Shadowsocks2022Parser()
    # Missing 2022- prefix and malformed components
    invalid = [
        "ss://aes-256-gcm:pass@host:8388",
        "ss://2022-:pass@host:port",
        "not-ss://something",
    ]
    for u in invalid:
        assert await parser.parse(u) is None
    # Non-string input exercises exception path
    assert await parser.parse(None) is None  # type: ignore[arg-type]


def test_ss2022_security_and_aead_helpers():
    p = Shadowsocks2022Parser()
    assert p._get_security_level("aes-256-gcm") == "high"
    assert p._get_security_level("aes-128-gcm") == "medium"
    assert p._get_security_level("unknown") == "standard"
    assert p._supports_aead("xchacha20-poly1305") is True
    assert p._supports_aead("rc4-md5") is False


@pytest.mark.asyncio
async def test_ss2022_module_level_helpers():
    # Ensure global helpers execute and update stats
    uri = "ss://2022-aes-128-gcm:secret@host.example:1234"
    cfg = await parse_ss2022_async(uri)
    assert cfg is not None
    stats = get_ss2022_parser_stats()
    assert isinstance(stats, dict) and stats.get("parse_count", 0) >= 1
