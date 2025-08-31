"""
Test core components of the VPN merger.
"""
import pytest
from unittest.mock import Mock, patch

from vpn_merger import VPNSubscriptionMerger, SourceManager, ConfigurationProcessor


class TestCoreComponents:
    """Test core component functionality."""
    
    def test_source_manager_initialization(self):
        """Test SourceManager can be initialized."""
        manager = SourceManager()
        assert manager is not None
        assert hasattr(manager, 'sources')
    
    def test_configuration_processor_initialization(self):
        """Test ConfigurationProcessor can be initialized."""
        processor = ConfigurationProcessor()
        assert processor is not None
        assert hasattr(processor, 'processed_configs')
    
    def test_vpn_merger_initialization(self):
        """Test VPNSubscriptionMerger can be initialized."""
        merger = VPNSubscriptionMerger()
        assert merger is not None
        assert hasattr(merger, 'source_manager')
        assert hasattr(merger, 'config_processor')
    
    def test_source_manager_get_sources(self):
        """Test SourceManager can retrieve sources."""
        manager = SourceManager()
        sources = manager.get_all_sources()
        assert isinstance(sources, list)
        assert len(sources) > 0
    
    def test_config_processor_valid_config(self):
        """Test ConfigurationProcessor validates configs correctly."""
        processor = ConfigurationProcessor()
        
        # Valid config
        valid_config = "vmess://eyJhZGQiOiAidGVzdC5leGFtcGxlLmNvbSIsICJwb3J0IjogNDQzfQ=="
        result = processor.process_config(valid_config)
        assert result is not None
        assert result.protocol == "vmess"
        
        # Invalid config
        invalid_config = "invalid://config"
        result = processor.process_config(invalid_config)
        assert result is None
    
    def test_config_processor_deduplication(self):
        """Test ConfigurationProcessor deduplicates configs."""
        processor = ConfigurationProcessor()
        
        config = "vmess://test@example.com:443"
        
        # First time should work
        result1 = processor.process_config(config)
        assert result1 is not None
        
        # Second time should be deduplicated
        result2 = processor.process_config(config)
        assert result2 is None
