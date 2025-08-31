"""
Test ML-related components of the VPN merger.
"""
import pytest
from unittest.mock import Mock, patch
import numpy as np

from vpn_merger import ConfigurationProcessor, VPNConfiguration


class TestMLComponents:
    """Test ML-related functionality."""
    
    def test_quality_scoring(self):
        """Test quality scoring algorithm."""
        processor = ConfigurationProcessor()
        
        # Test different protocols get different scores
        vmess_config = "vmess://eyJhZGQiOiAidGVzdC5leGFtcGxlLmNvbSIsICJwb3J0IjogNDQzfQ=="
        vless_config = "vless://12345678-90ab-12f3-a6c5-4681aaaaaaaa@test.example.com:443?security=tls"
        
        vmess_result = processor.process_config(vmess_config)
        vless_result = processor.process_config(vless_config)
        
        assert vmess_result is not None
        assert vless_result is not None
        
        # VLESS should get higher score than VMess
        assert vless_result.quality_score > vmess_result.quality_score
        
        # Scores should be between 0 and 1
        assert 0 <= vmess_result.quality_score <= 1
        assert 0 <= vless_result.quality_score <= 1
    
    def test_protocol_detection_accuracy(self):
        """Test protocol detection accuracy."""
        processor = ConfigurationProcessor()
        
        test_cases = [
            ("vmess://test", "vmess"),
            ("vless://test", "vless"),
            ("trojan://test", "trojan"),
            ("ss://test", "shadowsocks"),
            ("ssr://test", "shadowsocksr"),
            ("hysteria://test", "hysteria"),
            ("hysteria2://test", "hysteria"),
            ("tuic://test", "tuic"),
            ("invalid://test", "unknown"),
        ]
        
        for config, expected_protocol in test_cases:
            result = processor.process_config(config)
            if result:
                assert result.protocol == expected_protocol, f"Expected {expected_protocol} for {config}"
    
    def test_config_validation(self):
        """Test configuration validation logic."""
        processor = ConfigurationProcessor()
        
        # Valid configs
        valid_configs = [
            "vmess://eyJhZGQiOiAidGVzdC5leGFtcGxlLmNvbSIsICJwb3J0IjogNDQzfQ==",
            "vless://12345678-90ab-12f3-a6c5-4681aaaaaaaa@test.example.com:443?security=tls",
            "trojan://password@test.example.com:443",
        ]
        
        for config in valid_configs:
            result = processor.process_config(config)
            assert result is not None, f"Valid config {config} was rejected"
        
        # Invalid configs
        invalid_configs = [
            "",  # Empty
            "short",  # Too short
            "http://example.com",  # Wrong protocol
            "vmess://",  # Incomplete
        ]
        
        for config in invalid_configs:
            result = processor.process_config(config)
            assert result is None, f"Invalid config {config} was accepted"
    
    def test_deduplication_efficiency(self):
        """Test deduplication works correctly."""
        processor = ConfigurationProcessor()
        
        # Same config multiple times
        config = "vmess://eyJhZGQiOiAidGVzdC5leGFtcGxlLmNvbSIsICJwb3J0IjogNDQzfQ=="
        
        # First time should work
        result1 = processor.process_config(config)
        assert result1 is not None
        
        # Second time should be deduplicated
        result2 = processor.process_config(config)
        assert result2 is None
        
        # Different config should work
        different_config = "vless://12345678-90ab-12f3-a6c5-4681aaaaaaaa@test.example.com:443"
        result3 = processor.process_config(different_config)
        assert result3 is not None
    
    def test_quality_score_distribution(self):
        """Test quality scores are distributed reasonably."""
        processor = ConfigurationProcessor()
        
        configs = [
            "vmess://eyJhZGQiOiAidGVzdC5leGFtcGxlLmNvbSIsICJwb3J0IjogNDQzfQ==",
            "vless://12345678-90ab-12f3-a6c5-4681aaaaaaaa@test.example.com:443?security=tls",
            "trojan://password@test.example.com:443",
            "ss://test@example.com:443",
            "ssr://test@example.com:443",
        ]
        
        scores = []
        for config in configs:
            result = processor.process_config(config)
            if result:
                scores.append(result.quality_score)
        
        # Should have some variation in scores
        assert len(set(scores)) > 1, "All configs got same quality score"
        
        # Scores should be reasonable
        assert all(0 <= score <= 1 for score in scores), "Scores out of range"
        assert any(score > 0.7 for score in scores), "No high-quality configs found"
