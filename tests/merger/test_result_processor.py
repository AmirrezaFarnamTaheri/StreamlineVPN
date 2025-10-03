"""Tests for merger result_processor module."""

import base64
import json
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from streamline_vpn.merger.result_processor import (
    ConfigResult,
    EnhancedConfigProcessor,
    CONFIG
)


class TestConfigResult:
    """Test cases for ConfigResult dataclass."""

    def test_config_result_creation(self):
        """Test ConfigResult creation with default values."""
        result = ConfigResult(config="test_config", protocol="VMess")
        
        assert result.config == "test_config"
        assert result.protocol == "VMess"
        assert result.host is None
        assert result.port is None
        assert result.ping_time is None
        assert result.is_reachable is False
        assert result.source_url == ""
        assert result.country is None

    def test_config_result_with_all_fields(self):
        """Test ConfigResult creation with all fields."""
        result = ConfigResult(
            config="vmess://test",
            protocol="VMess",
            host="example.com",
            port=443,
            ping_time=100.5,
            is_reachable=True,
            source_url="http://source.com",
            country="US"
        )
        
        assert result.config == "vmess://test"
        assert result.protocol == "VMess"
        assert result.host == "example.com"
        assert result.port == 443
        assert result.ping_time == 100.5
        assert result.is_reachable is True
        assert result.source_url == "http://source.com"
        assert result.country == "US"


class TestEnhancedConfigProcessor:
    """Test cases for EnhancedConfigProcessor."""

    @pytest.fixture
    def processor(self):
        """Create processor instance."""
        with patch('streamline_vpn.merger.result_processor.NodeTester'):
            return EnhancedConfigProcessor()

    def test_processor_initialization(self, processor):
        """Test processor initialization."""
        assert processor is not None
        assert hasattr(processor, 'tester')
        assert processor.MAX_DECODE_SIZE > 0

    def test_normalize_url_basic(self, processor):
        """Test basic URL normalization."""
        url = "http://example.com/path?b=2&a=1#fragment"
        normalized = processor._normalize_url(url)
        
        # Should sort query params and remove fragment
        assert "a=1&b=2" in normalized
        assert "#fragment" not in normalized

    def test_normalize_url_vmess(self, processor):
        """Test VMess URL normalization."""
        # Create a valid VMess config
        vmess_data = {
            "v": "2",
            "ps": "test",
            "add": "example.com",
            "port": "443",
            "id": "test-uuid",
            "aid": "0",
            "net": "ws",
            "type": "none",
            "host": "",
            "path": "/",
            "tls": "tls"
        }
        encoded = base64.b64encode(json.dumps(vmess_data).encode()).decode()
        vmess_url = f"vmess://{encoded}"
        
        normalized = processor._normalize_url(vmess_url)
        
        # Should normalize the JSON payload
        assert normalized.startswith("vmess://")
        assert len(normalized) > len("vmess://")

    def test_normalize_url_invalid_vmess(self, processor):
        """Test VMess URL normalization with invalid data."""
        # Invalid base64
        vmess_url = "vmess://invalid_base64!"
        normalized = processor._normalize_url(vmess_url)
        
        # Should handle gracefully
        assert normalized.startswith("vmess://")

    def test_normalize_url_vless(self, processor):
        """Test VLESS URL normalization."""
        vless_data = {"id": "test-uuid", "add": "example.com", "port": "443"}
        encoded = base64.b64encode(json.dumps(vless_data).encode()).decode()
        vless_url = f"vless://{encoded}"
        
        normalized = processor._normalize_url(vless_url)
        
        assert normalized.startswith("vless://")

    def test_extract_host_port_vmess(self, processor):
        """Test host/port extraction from VMess config."""
        vmess_data = {
            "add": "example.com",
            "port": "443"
        }
        encoded = base64.b64encode(json.dumps(vmess_data).encode()).decode()
        vmess_url = f"vmess://{encoded}"
        
        host, port = processor.extract_host_port(vmess_url)
        
        assert host == "example.com"
        assert port == 443

    def test_extract_host_port_vmess_with_host_field(self, processor):
        """Test host/port extraction from VMess config using host field."""
        vmess_data = {
            "host": "example.com",
            "port": "8080"
        }
        encoded = base64.b64encode(json.dumps(vmess_data).encode()).decode()
        vmess_url = f"vmess://{encoded}"
        
        host, port = processor.extract_host_port(vmess_url)
        
        assert host == "example.com"
        assert port == 8080

    def test_extract_host_port_vmess_invalid(self, processor):
        """Test host/port extraction from invalid VMess config."""
        vmess_url = "vmess://invalid_base64!"
        
        host, port = processor.extract_host_port(vmess_url)
        
        assert host is None
        assert port is None

    def test_extract_host_port_vmess_oversized(self, processor):
        """Test host/port extraction from oversized VMess config."""
        # Create oversized data
        large_data = {"add": "example.com", "port": "443", "large": "x" * (processor.MAX_DECODE_SIZE + 1)}
        encoded = base64.b64encode(json.dumps(large_data).encode()).decode()
        vmess_url = f"vmess://{encoded}"
        
        host, port = processor.extract_host_port(vmess_url)
        
        assert host is None
        assert port is None

    def test_extract_host_port_ssr(self, processor):
        """Test host/port extraction from SSR config."""
        # Create SSR config: host:port:protocol:method:obfs:password_base64
        ssr_data = "example.com:443:origin:aes-256-cfb:plain:cGFzc3dvcmQ"
        encoded = base64.urlsafe_b64encode(ssr_data.encode()).decode().rstrip('=')
        ssr_url = f"ssr://{encoded}"
        
        host, port = processor.extract_host_port(ssr_url)
        
        assert host == "example.com"
        assert port == 443

    def test_extract_host_port_ssr_invalid(self, processor):
        """Test host/port extraction from invalid SSR config."""
        ssr_url = "ssr://invalid_base64!"
        
        host, port = processor.extract_host_port(ssr_url)
        
        assert host is None
        assert port is None

    def test_extract_host_port_ssr_malformed(self, processor):
        """Test host/port extraction from malformed SSR config."""
        # SSR config without port
        ssr_data = "example.com"
        encoded = base64.urlsafe_b64encode(ssr_data.encode()).decode()
        ssr_url = f"ssr://{encoded}"
        
        host, port = processor.extract_host_port(ssr_url)
        
        assert host is None
        assert port is None

    def test_extract_host_port_standard_url(self, processor):
        """Test host/port extraction from standard URL."""
        url = "http://example.com:8080/path"
        
        host, port = processor.extract_host_port(url)
        
        assert host == "example.com"
        assert port == 8080

    def test_extract_host_port_regex_fallback(self, processor):
        """Test host/port extraction using regex fallback."""
        config = "some_protocol://user@example.com:9090/path"
        
        host, port = processor.extract_host_port(config)
        
        assert host == "example.com"
        assert port == 9090

    def test_extract_host_port_no_match(self, processor):
        """Test host/port extraction with no match."""
        config = "invalid_config_format"
        
        host, port = processor.extract_host_port(config)
        
        assert host is None
        assert port is None

    def test_create_semantic_hash_vmess(self, processor):
        """Test semantic hash creation for VMess config."""
        vmess_data = {
            "id": "test-uuid-123",
            "add": "example.com",
            "port": "443"
        }
        encoded = base64.b64encode(json.dumps(vmess_data).encode()).decode()
        vmess_url = f"vmess://{encoded}"
        
        hash1 = processor.create_semantic_hash(vmess_url)
        hash2 = processor.create_semantic_hash(vmess_url)
        
        # Should be consistent
        assert hash1 == hash2
        assert len(hash1) > 0

    def test_create_semantic_hash_vless(self, processor):
        """Test semantic hash creation for VLESS config."""
        vless_data = {
            "uuid": "test-uuid-456",
            "add": "example.com",
            "port": "443"
        }
        encoded = base64.b64encode(json.dumps(vless_data).encode()).decode()
        vless_url = f"vless://{encoded}"
        
        hash_value = processor.create_semantic_hash(vless_url)
        
        assert len(hash_value) > 0

    def test_create_semantic_hash_trojan(self, processor):
        """Test semantic hash creation for Trojan config."""
        trojan_url = "trojan://password123@example.com:443"
        
        hash_value = processor.create_semantic_hash(trojan_url)
        
        assert len(hash_value) > 0

    def test_create_semantic_hash_shadowsocks(self, processor):
        """Test semantic hash creation for Shadowsocks config."""
        ss_url = "ss://YWVzLTI1Ni1nY206cGFzc3dvcmQ@example.com:443"
        
        hash_value = processor.create_semantic_hash(ss_url)
        
        assert len(hash_value) > 0

    def test_create_semantic_hash_different_configs(self, processor):
        """Test that different configs produce different hashes."""
        config1 = "vmess://eyJpZCI6InRlc3QxIiwiYWRkIjoiZXhhbXBsZTEuY29tIiwicG9ydCI6IjQ0MyJ9"
        config2 = "vmess://eyJpZCI6InRlc3QyIiwiYWRkIjoiZXhhbXBsZTIuY29tIiwicG9ydCI6IjQ0MyJ9"
        
        hash1 = processor.create_semantic_hash(config1)
        hash2 = processor.create_semantic_hash(config2)
        
        assert hash1 != hash2

    def test_create_semantic_hash_invalid_vmess(self, processor):
        """Test semantic hash creation for invalid VMess config."""
        vmess_url = "vmess://invalid_base64!"
        
        hash_value = processor.create_semantic_hash(vmess_url)
        
        # Should still produce a hash
        assert len(hash_value) > 0

    def test_create_semantic_hash_with_username(self, processor):
        """Test semantic hash creation with username in URL."""
        url = "vmess://username@example.com:443"
        
        hash_value = processor.create_semantic_hash(url)
        
        assert len(hash_value) > 0

    def test_create_semantic_hash_fallback(self, processor):
        """Test semantic hash creation fallback to normalized URL."""
        url = "unknown://example.com:443"
        
        hash_value = processor.create_semantic_hash(url)
        
        assert len(hash_value) > 0


class TestResultProcessorEdgeCases:
    """Edge case tests for result_processor module."""

    @pytest.fixture
    def processor(self):
        """Create processor instance."""
        with patch('streamline_vpn.merger.result_processor.NodeTester'):
            return EnhancedConfigProcessor()

    def test_normalize_url_empty_query(self, processor):
        """Test URL normalization with empty query."""
        url = "http://example.com/path?"
        normalized = processor._normalize_url(url)
        
        assert normalized == "http://example.com/path"

    def test_normalize_url_no_query(self, processor):
        """Test URL normalization without query."""
        url = "http://example.com/path"
        normalized = processor._normalize_url(url)
        
        assert normalized == url

    def test_extract_host_port_unicode_error(self, processor):
        """Test host/port extraction with unicode error."""
        # Create config that will cause UnicodeDecodeError
        with patch('base64.b64decode') as mock_decode:
            mock_decode.side_effect = UnicodeError("Test unicode error")
            
            config = "vmess://dGVzdA=="
            host, port = processor.extract_host_port(config)
            
            assert host is None
            assert port is None

    def test_extract_host_port_value_error(self, processor):
        """Test host/port extraction with value error."""
        # Create SSR config with invalid port
        ssr_data = "example.com:invalid_port:origin:aes-256-cfb:plain:cGFzc3dvcmQ"
        encoded = base64.urlsafe_b64encode(ssr_data.encode()).decode()
        ssr_url = f"ssr://{encoded}"
        
        host, port = processor.extract_host_port(ssr_url)
        
        assert host is None
        assert port is None

    def test_create_semantic_hash_json_decode_error(self, processor):
        """Test semantic hash creation with JSON decode error."""
        # Create VMess with invalid JSON
        invalid_json = "not_json"
        encoded = base64.b64encode(invalid_json.encode()).decode()
        vmess_url = f"vmess://{encoded}"
        
        hash_value = processor.create_semantic_hash(vmess_url)
        
        # Should still produce a hash using fallback
        assert len(hash_value) > 0

    def test_normalize_url_vmess_json_error(self, processor):
        """Test VMess URL normalization with JSON error."""
        # Create VMess with invalid JSON
        invalid_json = "not_json"
        encoded = base64.b64encode(invalid_json.encode()).decode()
        vmess_url = f"vmess://{encoded}"
        
        normalized = processor._normalize_url(vmess_url)
        
        # Should handle gracefully
        assert normalized.startswith("vmess://")

    def test_normalize_url_vmess_unicode_error(self, processor):
        """Test VMess URL normalization with unicode error."""
        with patch('base64.b64decode') as mock_decode:
            mock_decode.side_effect = UnicodeDecodeError("utf-8", b"", 0, 1, "Test error")
            
            vmess_url = "vmess://dGVzdA=="
            normalized = processor._normalize_url(vmess_url)
            
            # Should handle gracefully
            assert normalized.startswith("vmess://")


class TestConfigModule:
    """Test cases for module-level CONFIG loading."""

    def test_config_loading_success(self):
        """Test successful CONFIG loading."""
        # CONFIG should be loaded at module level
        assert CONFIG is not None
        assert hasattr(CONFIG, '__dict__')

    @patch('streamline_vpn.merger.result_processor.load_config')
    def test_config_loading_failure(self, mock_load_config):
        """Test CONFIG loading with failure fallback."""
        mock_load_config.side_effect = ValueError("Config error")
        
        # Reload the module to test the exception handling
        import importlib
        import streamline_vpn.merger.result_processor as rp_module
        importlib.reload(rp_module)
        
        # Should fall back to default Settings
        assert rp_module.CONFIG is not None

    def test_default_config_file_path(self):
        """Test DEFAULT_CONFIG_FILE path."""
        from streamline_vpn.merger.result_processor import DEFAULT_CONFIG_FILE
        
        assert isinstance(DEFAULT_CONFIG_FILE, Path)
        assert DEFAULT_CONFIG_FILE.name == "config.yaml"


class TestResultProcessorIntegration:
    """Integration tests for result_processor module."""

    @pytest.fixture
    def processor(self):
        """Create processor instance."""
        with patch('streamline_vpn.merger.result_processor.NodeTester'):
            return EnhancedConfigProcessor()

    def test_full_vmess_processing(self, processor):
        """Test complete VMess config processing."""
        vmess_data = {
            "v": "2",
            "ps": "test-server",
            "add": "example.com",
            "port": "443",
            "id": "test-uuid-123",
            "aid": "0",
            "net": "ws",
            "type": "none",
            "host": "example.com",
            "path": "/path",
            "tls": "tls"
        }
        encoded = base64.b64encode(json.dumps(vmess_data).encode()).decode()
        vmess_url = f"vmess://{encoded}"
        
        # Test normalization
        normalized = processor._normalize_url(vmess_url)
        assert normalized.startswith("vmess://")
        
        # Test host/port extraction
        host, port = processor.extract_host_port(vmess_url)
        assert host == "example.com"
        assert port == 443
        
        # Test semantic hash
        hash_value = processor.create_semantic_hash(vmess_url)
        assert len(hash_value) > 0
        
        # Test consistency
        hash2 = processor.create_semantic_hash(normalized)
        assert hash_value == hash2

    def test_config_result_with_processor(self, processor):
        """Test ConfigResult integration with processor."""
        config = "vmess://eyJhZGQiOiJleGFtcGxlLmNvbSIsInBvcnQiOiI0NDMifQ=="
        
        host, port = processor.extract_host_port(config)
        
        result = ConfigResult(
            config=config,
            protocol="VMess",
            host=host,
            port=port,
            ping_time=100.0,
            is_reachable=True
        )
        
        assert result.host == "example.com"
        assert result.port == 443
        assert result.is_reachable is True
