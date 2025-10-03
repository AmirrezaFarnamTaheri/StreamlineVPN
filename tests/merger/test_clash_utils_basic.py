"""Basic tests for merger clash_utils module."""

import base64
import json
from unittest.mock import patch, MagicMock

import pytest
import yaml

from streamline_vpn.merger.clash_utils import (
    config_to_clash_proxy,
    flag_emoji,
    build_clash_config,
    results_to_clash_yaml
)


class TestConfigToClashProxy:
    """Test cases for config_to_clash_proxy function."""

    def test_vmess_basic_config(self):
        """Test basic VMess configuration parsing."""
        vmess_data = {
            "v": "2",
            "ps": "test-server",
            "add": "example.com",
            "port": "443",
            "id": "test-uuid-12345",
            "aid": "0",
            "net": "tcp",
            "type": "none"
        }
        encoded = base64.b64encode(json.dumps(vmess_data).encode()).decode()
        config = f"vmess://{encoded}"
        
        result = config_to_clash_proxy(config, 0)
        
        assert result is not None
        assert result["name"] == "test-server"
        assert result["type"] == "vmess"
        assert result["server"] == "example.com"
        assert result["port"] == 443
        assert result["uuid"] == "test-uuid-12345"

    def test_vmess_with_tls(self):
        """Test VMess configuration with TLS."""
        vmess_data = {
            "v": "2",
            "ps": "tls-server",
            "add": "secure.example.com",
            "port": "443",
            "id": "test-uuid",
            "aid": "0",
            "tls": "tls"
        }
        encoded = base64.b64encode(json.dumps(vmess_data).encode()).decode()
        config = f"vmess://{encoded}"
        
        result = config_to_clash_proxy(config, 0)
        
        assert result is not None
        assert result["tls"] is True

    def test_vmess_with_websocket(self):
        """Test VMess configuration with WebSocket."""
        vmess_data = {
            "v": "2",
            "ps": "ws-server",
            "add": "ws.example.com",
            "port": "443",
            "id": "test-uuid",
            "aid": "0",
            "net": "ws",
            "host": "ws.example.com",
            "path": "/websocket"
        }
        encoded = base64.b64encode(json.dumps(vmess_data).encode()).decode()
        config = f"vmess://{encoded}"
        
        result = config_to_clash_proxy(config, 0)
        
        assert result is not None
        assert result["network"] == "ws"
        assert "ws-opts" in result
        assert result["ws-opts"]["path"] == "/websocket"

    def test_vmess_invalid_base64(self):
        """Test VMess configuration with invalid base64."""
        config = "vmess://invalid-base64"
        
        result = config_to_clash_proxy(config, 0)
        
        assert result is None

    def test_vless_basic_config(self):
        """Test basic VLESS configuration parsing."""
        config = "vless://test-uuid@example.com:443?type=tcp&security=none#test-server"
        
        result = config_to_clash_proxy(config, 0)
        
        assert result is not None
        assert result["name"] == "test-server"
        assert result["type"] == "vless"
        assert result["server"] == "example.com"
        assert result["port"] == 443
        assert result["uuid"] == "test-uuid"

    def test_trojan_basic_config(self):
        """Test basic Trojan configuration parsing."""
        config = "trojan://password123@example.com:443?type=tcp#trojan-server"
        
        result = config_to_clash_proxy(config, 0)
        
        assert result is not None
        assert result["name"] == "trojan-server"
        assert result["type"] == "trojan"
        assert result["server"] == "example.com"
        assert result["port"] == 443
        assert result["password"] == "password123"

    def test_shadowsocks_basic_config(self):
        """Test basic Shadowsocks configuration parsing."""
        auth = base64.b64encode(b"aes-256-gcm:password123").decode()
        config = f"ss://{auth}@example.com:8388#ss-server"
        
        result = config_to_clash_proxy(config, 0)
        
        assert result is not None
        assert result["name"] == "ss-server"
        assert result["type"] == "ss"
        assert result["server"] == "example.com"
        assert result["port"] == 8388
        assert result["cipher"] == "aes-256-gcm"
        assert result["password"] == "password123"

    def test_unsupported_protocol(self):
        """Test unsupported protocol."""
        config = "unknown://test@example.com:443#unknown"
        
        result = config_to_clash_proxy(config, 0)
        
        assert result is None

    def test_malformed_config(self):
        """Test malformed configuration."""
        config = "not-a-valid-config"
        
        result = config_to_clash_proxy(config, 0)
        
        assert result is None


class TestFlagEmoji:
    """Test cases for flag_emoji function."""

    def test_valid_country_code(self):
        """Test valid 2-letter country code."""
        result = flag_emoji("US")
        assert len(result) == 2
        assert result != "🏳"

    def test_invalid_length(self):
        """Test invalid length country code."""
        result = flag_emoji("USA")
        assert result == "🏳"

    def test_empty_country_code(self):
        """Test empty country code."""
        result = flag_emoji("")
        assert result == "🏳"

    def test_none_country_code(self):
        """Test None country code."""
        result = flag_emoji(None)
        assert result == "🏳"


class TestBuildClashConfig:
    """Test cases for build_clash_config function."""

    def test_empty_proxies(self):
        """Test with empty proxies list."""
        result = build_clash_config([])
        assert result == ""

    def test_single_proxy(self):
        """Test with single proxy."""
        proxies = [
            {
                "name": "test-proxy",
                "type": "vmess",
                "server": "example.com",
                "port": 443
            }
        ]
        
        result = build_clash_config(proxies)
        
        assert result != ""
        config = yaml.safe_load(result)
        assert "proxies" in config
        assert "proxy-groups" in config
        assert "rules" in config
        assert len(config["proxies"]) == 1

    def test_multiple_proxies(self):
        """Test with multiple proxies."""
        proxies = [
            {"name": "proxy1", "type": "vmess", "server": "server1.com", "port": 443},
            {"name": "proxy2", "type": "vless", "server": "server2.com", "port": 443}
        ]
        
        result = build_clash_config(proxies)
        
        config = yaml.safe_load(result)
        assert len(config["proxies"]) == 2
        assert len(config["proxy-groups"]) == 2
        
        # Check group names
        group_names = [group["name"] for group in config["proxy-groups"]]
        assert "⚡ Auto-Select" in group_names
        assert "🔰 MANUAL" in group_names


class TestResultsToClashYaml:
    """Test cases for results_to_clash_yaml function."""

    def test_empty_results(self):
        """Test with empty results list."""
        result = results_to_clash_yaml([])
        assert result == ""

    def test_single_result(self):
        """Test with single result."""
        mock_result = MagicMock()
        mock_result.config = "vmess://config"
        mock_result.protocol = "vmess"
        mock_result.ping_time = 0.1
        mock_result.source_url = "https://example.com/config"
        mock_result.country = "US"
        
        with patch('streamline_vpn.merger.clash_utils.config_to_clash_proxy') as mock_parser:
            mock_parser.return_value = {
                "name": "test-proxy",
                "type": "vmess",
                "server": "example.com",
                "port": 443
            }
            
            result = results_to_clash_yaml([mock_result])
            
            assert result != ""
            config = yaml.safe_load(result)
            assert "proxies" in config
            assert len(config["proxies"]) == 1

    def test_result_with_none_ping_time(self):
        """Test result with None ping time."""
        mock_result = MagicMock()
        mock_result.config = "vmess://config"
        mock_result.protocol = "vmess"
        mock_result.ping_time = None
        mock_result.source_url = "https://example.com/config"
        mock_result.country = "US"
        
        with patch('streamline_vpn.merger.clash_utils.config_to_clash_proxy') as mock_parser:
            mock_parser.return_value = {
                "name": "test-proxy",
                "type": "vmess",
                "server": "example.com",
                "port": 443
            }
            
            result = results_to_clash_yaml([mock_result])
            
            config = yaml.safe_load(result)
            proxy = config["proxies"][0]
            assert "?" in proxy["name"]  # Should show ? for unknown ping

    def test_result_with_invalid_config(self):
        """Test result with invalid config that returns None."""
        mock_result = MagicMock()
        mock_result.config = "invalid://config"
        mock_result.protocol = "invalid"
        mock_result.ping_time = 0.1
        mock_result.source_url = "https://example.com/config"
        mock_result.country = "US"
        
        with patch('streamline_vpn.merger.clash_utils.config_to_clash_proxy') as mock_parser:
            mock_parser.return_value = None  # Invalid config
            
            result = results_to_clash_yaml([mock_result])
            
            config = yaml.safe_load(result)
            assert len(config["proxies"]) == 0


class TestClashUtilsEdgeCases:
    """Edge case tests for clash_utils module."""

    def test_config_parsing_exception_handling(self):
        """Test that exceptions are handled gracefully."""
        config = "vmess://invalid"
        
        result = config_to_clash_proxy(config, 0)
        
        assert result is None

    def test_shadowsocks_invalid_base64_auth(self):
        """Test Shadowsocks with invalid base64 auth."""
        config = "ss://invalid-base64@example.com:8388#ss-server"
        
        result = config_to_clash_proxy(config, 0)
        
        assert result is None

    def test_config_with_index(self):
        """Test configuration with custom index."""
        vmess_data = {
            "v": "2",
            "add": "example.com",
            "port": "443",
            "id": "test-uuid",
            "aid": "0"
        }
        encoded = base64.b64encode(json.dumps(vmess_data).encode()).decode()
        config = f"vmess://{encoded}"
        
        result = config_to_clash_proxy(config, 5)
        
        assert result is not None
        assert result["name"] == "vmess-5"

    def test_protocol_override(self):
        """Test configuration with protocol override."""
        config = "vmess://invalid-data"
        
        result = config_to_clash_proxy(config, 0, protocol="trojan")
        
        # Should try to parse as trojan, but fail due to invalid format
        assert result is None
