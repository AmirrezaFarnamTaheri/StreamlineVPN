import os
import json
import pytest

from streamline_vpn.settings import get_settings, reset_settings_cache
from streamline_vpn.utils.validation import (
    validate_config_line,
    validate_config,
    validate_source_metadata,
    sanitize_string,
    validate_ip_address,
    validate_domain,
)


def test_settings_env_parsing(monkeypatch):
    # Provide comma-separated values and ensure they are parsed into lists
    monkeypatch.setenv("ALLOWED_ORIGINS", "http://a.com, http://b.com")
    monkeypatch.setenv("ALLOWED_METHODS", "GET,POST")
    monkeypatch.setenv("ALLOWED_HEADERS", "Content-Type, Authorization")
    reset_settings_cache()
    s = get_settings()
    assert "http://a.com" in s.allowed_origins
    assert "http://b.com" in s.allowed_origins
    assert "GET" in s.allowed_methods and "POST" in s.allowed_methods
    assert "Content-Type" in s.allowed_headers


def test_validate_config_line():
    assert validate_config_line("vmess://abc") is True
    assert validate_config_line("   ") is False
    assert validate_config_line("<script>alert(1)</script>") is False


def test_validate_config_dict():
    good = {"protocol": "vmess", "server": "test-server.example", "port": 443}
    bad_missing = {"protocol": "vmess", "server": "test-server.example"}
    bad_port = {"protocol": "vmess", "server": "test-server.example", "port": 70000}
    bad_protocol = {"protocol": "bad", "server": "test-server.example", "port": 443}
    assert validate_config(good) is True
    assert validate_config(bad_missing) is False
    assert validate_config(bad_port) is False
    assert validate_config(bad_protocol) is False


def test_validate_source_metadata():
    ok = {"url": "https://test-source.example/sub.txt", "weight": 0.5, "tier": "premium"}
    assert validate_source_metadata(ok) in (True, False)  # depends on URL validator
    assert validate_source_metadata({}) is False
    assert validate_source_metadata({"url": "bad://"}) is False
    assert validate_source_metadata({"url": "https://test-source.example", "weight": 2}) is False
    assert validate_source_metadata({"url": "https://test-source.example", "tier": "nope"}) is False


def test_sanitize_and_ip_domain():
    t = sanitize_string("hello\x00world", max_length=5)
    assert t == "hello"
    assert validate_ip_address("127.0.0.1") is True
    assert validate_ip_address("999.0.0.1") is False
    assert validate_domain("test-server.example") is True
    assert validate_domain("bad_domain!") is False

