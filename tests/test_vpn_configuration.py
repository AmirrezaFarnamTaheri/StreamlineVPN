"""
Test VPN Configuration Model
===========================

Focused tests for the VPNConfiguration data model.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock

from vpn_merger.models.configuration import VPNConfiguration


class TestVPNConfiguration:
    """Test the VPNConfiguration model comprehensively."""
    
    @pytest.fixture
    def basic_config(self):
        """Create a basic VPNConfiguration instance."""
        return VPNConfiguration(
            config="vmess://eyJhZGQiOiAidGVzdC5leGFtcGxlLmNvbSIsICJwb3J0IjogNDQzfQ==",
            protocol="vmess"
        )
    
    @pytest.fixture
    def full_config(self):
        """Create a full VPNConfiguration instance with all fields."""
        return VPNConfiguration(
            config="vless://12345678-90ab-12f3-a6c5-4681aaaaaaaa@test.example.com:443?security=tls",
            protocol="vless",
            host="test.example.com",
            port=443,
            ping_time=15.5,
            is_reachable=True,
            source_url="https://example.com/config.txt",
            quality_score=0.95,
            last_tested=datetime.now(),
            error_count=0
        )
    
    def test_basic_initialization(self, basic_config):
        """Test basic configuration initialization."""
        assert basic_config.config == "vmess://eyJhZGQiOiAidGVzdC5leGFtcGxlLmNvbSIsICJwb3J0IjogNDQzfQ=="
        assert basic_config.protocol == "vmess"
        assert basic_config.host is None
        assert basic_config.port is None
        assert basic_config.ping_time is None
        assert basic_config.is_reachable is False
        assert basic_config.source_url is None
        assert basic_config.quality_score == 0.0
        assert basic_config.last_tested is None
        assert basic_config.error_count == 0
    
    def test_full_initialization(self, full_config):
        """Test full configuration initialization."""
        assert full_config.config == "vless://12345678-90ab-12f3-a6c5-4681aaaaaaaa@test.example.com:443?security=tls"
        assert full_config.protocol == "vless"
        assert full_config.host == "test.example.com"
        assert full_config.port == 443
        assert full_config.ping_time == 15.5
        assert full_config.is_reachable is True
        assert full_config.source_url == "https://example.com/config.txt"
        assert full_config.quality_score == 0.95
        assert full_config.last_tested is not None
        assert full_config.error_count == 0
    
    def test_to_dict(self, full_config):
        """Test conversion to dictionary."""
        config_dict = full_config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert config_dict['config'] == full_config.config
        assert config_dict['protocol'] == full_config.protocol
        assert config_dict['host'] == full_config.host
        assert config_dict['port'] == full_config.port
        assert config_dict['ping_time'] == full_config.ping_time
        assert config_dict['is_reachable'] == full_config.is_reachable
        assert config_dict['source_url'] == full_config.source_url
        assert config_dict['quality_score'] == full_config.quality_score
        assert config_dict['last_tested'] == full_config.last_tested
        assert config_dict['error_count'] == full_config.error_count
    
    def test_hash_equality(self, basic_config):
        """Test hash and equality based on config content."""
        # Create another config with same content
        same_config = VPNConfiguration(
            config="vmess://eyJhZGQiOiAidGVzdC5leGFtcGxlLmNvbSIsICJwb3J0IjogNDQzfQ==",
            protocol="vmess"
        )
        
        # Should be equal
        assert basic_config == same_config
        
        # Should have same hash
        assert hash(basic_config) == hash(same_config)
        
        # Different config should not be equal
        different_config = VPNConfiguration(
            config="vmess://different",
            protocol="vmess"
        )
        assert basic_config != different_config
        assert hash(basic_config) != hash(different_config)
    
    def test_is_valid(self, basic_config, full_config):
        """Test configuration validation."""
        # Basic config should be valid
        assert basic_config.is_valid() is True
        
        # Full config should be valid
        assert full_config.is_valid() is True
        
        # Invalid configs
        invalid_config = VPNConfiguration(
            config="",  # Empty config
            protocol="unknown"  # Unknown protocol
        )
        assert invalid_config.is_valid() is False
        
        # Config with negative quality score
        negative_score_config = VPNConfiguration(
            config="vmess://test",
            protocol="vmess",
            quality_score=-0.1
        )
        assert negative_score_config.is_valid() is False
        
        # Config with negative error count
        negative_error_config = VPNConfiguration(
            config="vmess://test",
            protocol="vmess",
            error_count=-1
        )
        assert negative_error_config.is_valid() is False
    
    def test_update_quality_score(self, basic_config):
        """Test quality score updates with validation."""
        # Valid score updates
        basic_config.update_quality_score(0.8)
        assert basic_config.quality_score == 0.8
        
        basic_config.update_quality_score(1.0)
        assert basic_config.quality_score == 1.0
        
        basic_config.update_quality_score(0.0)
        assert basic_config.quality_score == 0.0
        
        # Invalid score updates should raise ValueError
        with pytest.raises(ValueError):
            basic_config.update_quality_score(1.1)
        
        with pytest.raises(ValueError):
            basic_config.update_quality_score(-0.1)
    
    def test_mark_tested(self, basic_config):
        """Test marking configuration as tested."""
        initial_time = basic_config.last_tested
        
        # Mark as tested with ping time and reachability
        basic_config.mark_tested(ping_time=25.0, is_reachable=True)
        
        assert basic_config.last_tested is not None
        assert basic_config.last_tested != initial_time
        assert basic_config.ping_time == 25.0
        assert basic_config.is_reachable is True
        
        # Mark as tested without ping time
        basic_config.mark_tested(is_reachable=False)
        assert basic_config.is_reachable is False
        assert basic_config.ping_time == 25.0  # Should remain unchanged
    
    def test_increment_error_count(self, basic_config):
        """Test error count increment."""
        initial_count = basic_config.error_count
        
        basic_config.increment_error_count()
        assert basic_config.error_count == initial_count + 1
        
        basic_config.increment_error_count()
        assert basic_config.error_count == initial_count + 2
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Very long config
        long_config = VPNConfiguration(
            config="vmess://" + "x" * 1000,
            protocol="vmess"
        )
        assert long_config.is_valid() is True
        
        # Very short config
        short_config = VPNConfiguration(
            config="vmess://x",
            protocol="vmess"
        )
        assert short_config.is_valid() is True
        
        # Zero quality score
        zero_score_config = VPNConfiguration(
            config="vmess://test",
            protocol="vmess",
            quality_score=0.0
        )
        assert zero_score_config.is_valid() is True
        
        # Maximum quality score
        max_score_config = VPNConfiguration(
            config="vmess://test",
            protocol="vmess",
            quality_score=1.0
        )
        assert max_score_config.is_valid() is True
    
    def test_protocol_specific_validation(self):
        """Test validation for different protocols."""
        protocols = ["vmess", "vless", "trojan", "shadowsocks", "shadowsocksr", "hysteria", "tuic"]
        
        for protocol in protocols:
            config = VPNConfiguration(
                config=f"{protocol}://test",
                protocol=protocol
            )
            assert config.is_valid() is True
        
        # Unknown protocol should be invalid
        unknown_config = VPNConfiguration(
            config="unknown://test",
            protocol="unknown"
        )
        assert unknown_config.is_valid() is False
    
    def test_serialization_roundtrip(self, full_config):
        """Test that serialization and deserialization work correctly."""
        # Convert to dict
        config_dict = full_config.to_dict()
        
        # Create new config from dict
        new_config = VPNConfiguration(**config_dict)
        
        # Should be equal
        assert new_config == full_config
        assert new_config.config == full_config.config
        assert new_config.protocol == full_config.protocol
        assert new_config.host == full_config.host
        assert new_config.port == full_config.port
