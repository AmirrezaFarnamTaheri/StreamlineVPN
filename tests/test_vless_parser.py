"""Tests for VLESS parser."""

# isort:skip_file
import pytest

from streamline_vpn.core.processing.parsers.vless_parser import (
    VLESSParser,
    get_vless_parser_stats,
    parse_vless_async,
)


@pytest.fixture
def parser():
    return VLESSParser()


@pytest.mark.asyncio
async def test_parse_valid_vless_uri(parser):
    uri = "vless://a-uuid-goes-here@test-server.example:443?security=tls&type=ws&path=%2F#test"
    config = await parser.parse(uri)
    assert config is not None
    assert config.protocol.value == "vless"
    assert config.server == "test-server.example"
    assert config.port == 443
    assert config.uuid == "a-uuid-goes-here"
    assert config.security == "tls"
    assert config.network == "ws"
    assert config.path == "/"
    assert config.metadata["security"] == "tls"


@pytest.mark.asyncio
async def test_parse_vless_uri_with_encoded_fragment(parser):
    uri = "vless://a-uuid-goes-here@test-server.example:443?path=%23encoded#fragment"
    config = await parser.parse(uri)
    assert config is not None
    # Ensure encoded '#' is preserved in path
    assert config.path == "#encoded"


@pytest.mark.asyncio
async def test_parse_invalid_vless_uri(parser):
    uri = "vless://invalid-uri"
    config = await parser.parse(uri)
    assert config is None


@pytest.mark.asyncio
async def test_parse_vless_uri_with_no_query(parser):
    uri = "vless://a-uuid-goes-here@test-server.example:443"
    config = await parser.parse(uri)
    assert config is not None
    assert config.protocol.value == "vless"
    assert config.server == "test-server.example"
    assert config.port == 443
    assert config.uuid == "a-uuid-goes-here"
    assert config.security == "tls"  # default value
    assert config.network == "tcp"  # default value
    assert config.path == ""  # default value


@pytest.mark.asyncio
async def test_parse_vless_uri_invalid_port(parser):
    uri = "vless://a-uuid-goes-here@test-server.example:70000"
    config = await parser.parse(uri)
    assert config is None

    uri_neg = "vless://a-uuid-goes-here@test-server.example:-1"
    config_neg = await parser.parse(uri_neg)
    assert config_neg is None


@pytest.mark.asyncio
async def test_async_parse_helper_and_stats():
    uri = "vless://a-uuid-goes-here@test-server.example:443"
    before = get_vless_parser_stats().get("parse_count", 0)
    config = await parse_vless_async(uri)
    assert config is not None
    stats = get_vless_parser_stats()
    assert stats["parse_count"] == before + 1
