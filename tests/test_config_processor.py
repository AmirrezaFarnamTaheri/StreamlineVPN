"""
Test Configuration Processor
===========================

Focused tests for configuration processing functionality.
"""

import pytest

from vpn_merger.core.config_processor import ConfigurationProcessor
from vpn_merger.models.configuration import VPNConfiguration


class TestConfigurationProcessor:
    """Test the ConfigurationProcessor class comprehensively."""

    @pytest.fixture
    def processor(self):
        """Create a ConfigurationProcessor instance for testing."""
        return ConfigurationProcessor()

    def test_initialization(self, processor):
        """Test ConfigurationProcessor initialization."""
        assert processor is not None
        assert isinstance(processor.processed_configs, set)
        assert len(processor.processed_configs) == 0
        assert len(processor._protocol_patterns) > 0

    def test_protocol_patterns(self, processor):
        """Test protocol pattern initialization."""
        patterns = processor._protocol_patterns
        assert "vmess" in patterns
        assert "vless" in patterns
        assert "trojan" in patterns
        assert "shadowsocks" in patterns
        assert "shadowsocksr" in patterns
        assert "hysteria" in patterns
        assert "tuic" in patterns

    def test_valid_config_validation(self, processor):
        """Test valid configuration validation."""
        valid_configs = [
            "vmess://eyJhZGQiOiAidGVzdC5leGFtcGxlLmNvbSIsICJwb3J0IjogNDQzfQ==",
            "vless://12345678-90ab-12f3-a6c5-4681aaaaaaaa@test.example.com:443?security=tls",
            "trojan://testpassword@test.example.com:443",
            "ss://base64encoded",
            "ssr://base64encoded",
            "hysteria://test.example.com:443",
            "tuic://test.example.com:443",
        ]

        for config in valid_configs:
            assert processor._is_valid_config(config) is True

    def test_invalid_config_validation(self, processor):
        """Test invalid configuration validation."""
        invalid_configs = [
            "",  # Empty
            "   ",  # Whitespace only
            "invalid",  # No protocol
            "vmess://",  # Protocol only
            "vmess://" + "x" * 10001,  # Too long
            "http://example.com",  # Wrong protocol
        ]

        for config in invalid_configs:
            assert processor._is_valid_config(config) is False

    def test_protocol_detection(self, processor):
        """Test protocol detection."""
        test_cases = [
            ("vmess://config", "vmess"),
            ("vless://config", "vless"),
            ("trojan://config", "trojan"),
            ("ss://config", "shadowsocks"),
            ("shadowsocks://config", "shadowsocks"),
            ("ssr://config", "shadowsocksr"),
            ("hysteria://config", "hysteria"),
            ("hysteria2://config", "hysteria"),
            ("tuic://config", "tuic"),
            ("invalid://config", "unknown"),
        ]

        for config, expected_protocol in test_cases:
            detected = processor._detect_protocol(config)
            assert detected == expected_protocol

    def test_duplicate_detection(self, processor):
        """Test duplicate configuration detection."""
        config1 = "vmess://config1"
        config2 = "vmess://config2"
        config3 = "vmess://config1"  # Duplicate of config1

        # Process first config
        result1 = processor.process_config(config1)
        assert result1 is not None
        assert processor._is_duplicate(config1) is True

        # Process second config
        result2 = processor.process_config(config2)
        assert result2 is not None
        assert processor._is_duplicate(config2) is True

        # Try to process duplicate
        result3 = processor.process_config(config3)
        assert result3 is None  # Should be rejected as duplicate

        assert processor.get_processed_count() == 2

    def test_quality_score_calculation(self, processor):
        """Test quality score calculation."""
        # Test with different protocols
        vmess_config = "vmess://config"
        vless_config = "vless://config"
        ss_config = "ss://config"

        vmess_score = processor._calculate_quality_score(vmess_config, "vmess")
        vless_score = processor._calculate_quality_score(vless_config, "vless")
        ss_score = processor._calculate_quality_score(ss_config, "shadowsocks")

        # VLESS should have highest score
        assert vless_score > vmess_score
        assert vmess_score > ss_score

        # All scores should be between 0 and 1
        assert 0.0 <= vmess_score <= 1.0
        assert 0.0 <= vless_score <= 1.0
        assert 0.0 <= ss_score <= 1.0

    def test_config_processing(self, processor):
        """Test complete configuration processing."""
        config = "vmess://eyJhZGQiOiAidGVzdC5leGFtcGxlLmNvbSIsICJwb3J0IjogNDQzfQ=="
        source_url = "https://example.com/config.txt"

        result = processor.process_config(config, source_url)

        assert result is not None
        assert isinstance(result, VPNConfiguration)
        assert result.config == config
        assert result.protocol == "vmess"
        assert result.source_url == source_url
        assert result.quality_score > 0.0
        assert result.is_valid() is True

    def test_clear_processed(self, processor):
        """Test clearing processed configurations."""
        # Process some configs
        processor.process_config("vmess://config1")
        processor.process_config("vless://config2")

        assert processor.get_processed_count() == 2

        # Clear processed
        processor.clear_processed()
        assert processor.get_processed_count() == 0

    def test_protocol_distribution(self, processor):
        """Test protocol distribution calculation."""
        # Create some test configurations
        configs = [
            VPNConfiguration("vmess://config1", "vmess"),
            VPNConfiguration("vless://config2", "vless"),
            VPNConfiguration("vmess://config3", "vmess"),
            VPNConfiguration("trojan://config4", "trojan"),
        ]

        distribution = processor.get_protocol_distribution(configs)

        assert distribution["vmess"] == 2
        assert distribution["vless"] == 1
        assert distribution["trojan"] == 1
        assert "shadowsocks" not in distribution

    def test_edge_cases(self, processor):
        """Test edge cases and error handling."""
        # Test with None and empty strings
        assert processor.process_config(None) is None
        assert processor.process_config("") is None
        assert processor.process_config("   ") is None

        # Test with very long configs
        long_config = "vmess://" + "x" * 10000
        assert processor._is_valid_config(long_config) is False

        # Test with very short configs
        short_config = "vmess://x"
        assert processor._is_valid_config(short_config) is True
