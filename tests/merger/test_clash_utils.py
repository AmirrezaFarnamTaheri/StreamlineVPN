import pytest
import yaml

from streamline_vpn.merger.clash_utils import (
    flag_emoji,
    build_clash_config,
    config_to_clash_proxy,
)

class TestFlagEmoji:
    """Tests for the flag_emoji function."""

    def test_valid_country_code(self):
        """Test with a valid two-letter country code."""
        assert flag_emoji("US") == "🇺🇸"
        assert flag_emoji("jp") == "🇯🇵" # Should handle lowercase

    def test_invalid_country_code(self):
        """Test with invalid or missing country codes."""
        assert flag_emoji(None) == "🏳"
        assert flag_emoji("") == "🏳"
        assert flag_emoji("USA") == "🏳"
        assert flag_emoji("A") == "🏳"

class TestBuildClashConfig:
    """Tests for the build_clash_config function."""

    def test_build_with_proxies(self):
        """Test building a config with a list of proxies."""
        proxies = [
            {"name": "proxy1", "type": "ss", "server": "1.1.1.1"},
            {"name": "proxy2", "type": "vmess", "server": "2.2.2.2"},
        ]

        result_yaml = build_clash_config(proxies)
        result_data = yaml.safe_load(result_yaml)

        assert "proxies" in result_data
        assert "proxy-groups" in result_data
        assert "rules" in result_data

        assert len(result_data["proxies"]) == 2
        assert result_data["proxies"][0]["name"] == "proxy1"

        assert len(result_data["proxy-groups"]) == 2
        assert result_data["proxy-groups"][0]["name"] == "⚡ Auto-Select"
        assert "proxy1" in result_data["proxy-groups"][0]["proxies"]
        assert "proxy2" in result_data["proxy-groups"][0]["proxies"]

    def test_build_with_no_proxies(self):
        """Test building a config with an empty list of proxies."""
        result_yaml = build_clash_config([])
        assert result_yaml == ""

class TestConfigToClashProxy:
    """Tests for the config_to_clash_proxy function."""

    def test_ss_simple(self):
        """Test a simple Shadowsocks (ss) link."""
        config_link = "ss://YWVzLTI1Ni1nY206cGFzc3dvcmQ@1.2.3.4:8888#Test-SS"
        proxy = config_to_clash_proxy(config_link)

        assert proxy is not None
        assert proxy["name"] == "Test-SS"
        assert proxy["type"] == "ss"
        assert proxy["server"] == "1.2.3.4"
        assert proxy["port"] == 8888
        assert proxy["cipher"] == "aes-256-gcm"
        assert proxy["password"] == "password"

    def test_vmess_simple(self):
        """Test a simple vmess link."""
        # Represents: {"v": "2", "ps": "Test-VMess", "add": "1.2.3.4", "port": "443", "id": "uuid", "aid": "0", "net": "ws", "type": "none", "host": "sub.domain.com", "path": "/path", "tls": "tls"}
        config_link = "vmess://eyJhZGQiOiIxLjIuMy40IiwidiI6IjIiLCJwcyI6IlRlc3QtVk1lc3MiLCJwb3J0Ijo0NDMsImlkIjoidXVpZCIsImFpZCI6MCwibmV0Ijoid3MiLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJzdWIuZG9tYWluLmNvbSIsInBhdGgiOiIvcGF0aCIsInRscyI6InRscyJ9"
        proxy = config_to_clash_proxy(config_link)

        assert proxy is not None
        assert proxy["name"] == "Test-VMess"
        assert proxy["type"] == "vmess"
        assert proxy["server"] == "1.2.3.4"
        assert proxy["port"] == 443
        assert proxy["uuid"] == "uuid"
        assert proxy["alterId"] == 0
        assert proxy["cipher"] == "none" # The 'type' field in vmess is the cipher
        assert proxy["tls"] is True
        assert proxy["network"] == "ws"
        assert proxy["ws-opts"]["path"] == "/path"
        assert proxy["ws-opts"]["headers"]["Host"] == "sub.domain.com"

# More tests for other protocols will be added.
