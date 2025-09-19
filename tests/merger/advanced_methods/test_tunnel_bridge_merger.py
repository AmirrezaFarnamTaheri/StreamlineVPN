import pytest
from streamline_vpn.merger.advanced_methods.tunnel_bridge_merger import parse_line

def test_parse_line_valid():
    line = "server.com:1234:aes-256-gcm:password123"
    expected = {
        "protocol": "tunnel_bridge",
        "server": "server.com",
        "port": 1234,
        "method": "aes-256-gcm",
        "password": "password123",
    }
    assert parse_line(line) == expected

def test_parse_line_invalid_format_too_few_parts():
    line = "server.com:1234:aes-256-gcm"
    assert parse_line(line) is None

def test_parse_line_empty_string():
    assert parse_line("") is None

def test_parse_line_whitespace_string():
    assert parse_line("   ") is None

def test_parse_line_invalid_port():
    line = "server.com:not-a-port:aes-256-gcm:password123"
    assert parse_line(line) is None

def test_parse_line_with_extra_parts():
    # The parser should only take the first 4 parts
    line = "server.com:1234:aes-256-gcm:password123:extra:stuff"
    expected = {
        "protocol": "tunnel_bridge",
        "server": "server.com",
        "port": 1234,
        "method": "aes-256-gcm",
        "password": "password123",
    }
    assert parse_line(line) == expected
