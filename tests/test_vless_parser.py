import pytest
from streamline_vpn.core.processing.parsers.vless_parser import VLESSParser


@pytest.fixture
def parser():
    return VLESSParser()


@pytest.mark.asyncio
async def test_parse_valid_vless_uri(parser):
    uri = "vless://a-uuid-goes-here@example.com:443?security=tls&type=ws&path=%2F#test"
    config = await parser.parse(uri)
    assert config is not None
    assert config.protocol.value == "vless"
    assert config.server == "example.com"
    assert config.port == 443
    assert config.uuid == "a-uuid-goes-here"
    assert config.security == "tls"
    assert config.network == "ws"
    assert config.path == "/"


@pytest.mark.asyncio
async def test_parse_invalid_vless_uri(parser):
    uri = "vless://invalid-uri"
    config = await parser.parse(uri)
    assert config is None


@pytest.mark.asyncio
async def test_parse_vless_uri_with_no_query(parser):
    uri = "vless://a-uuid-goes-here@example.com:443"
    config = await parser.parse(uri)
    assert config is not None
    assert config.protocol.value == "vless"
    assert config.server == "example.com"
    assert config.port == 443
    assert config.uuid == "a-uuid-goes-here"
    assert config.security == "tls"  # default value
    assert config.network == "tcp"  # default value
    assert config.path == ""  # default value
