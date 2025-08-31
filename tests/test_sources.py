"""Test module for source validation and processing."""

import pytest
from unittest.mock import Mock, patch
from vpn_merger import SourceManager, UnifiedSourceValidator


class TestSourceManager:
    """Test SourceManager class functionality."""
    
    def test_load_sources(self):
        """Test source loading from configuration."""
        sources = SourceManager()
        assert sources.sources is not None
        assert isinstance(sources.sources, dict)
    
    def test_get_all_sources(self):
        """Test getting all sources as flat list."""
        sources = SourceManager()
        all_sources = sources.get_all_sources()
        assert isinstance(all_sources, list)
        assert len(all_sources) > 0
    
    def test_get_sources_by_tier(self):
        """Test getting sources by tier."""
        sources = SourceManager()
        tier_sources = sources.get_sources_by_tier("emergency_fallback")
        assert isinstance(tier_sources, list)
    
    def test_get_prioritized_sources(self):
        """Test getting prioritized sources."""
        sources = SourceManager()
        prioritized = sources.get_prioritized_sources()
        assert isinstance(prioritized, list)
        assert len(prioritized) > 0


class TestUnifiedSourceValidator:
    """Test SourceHealthChecker class functionality."""
    
    def test_protocol_detection(self):
        """Test protocol detection functionality."""
        validator = UnifiedSourceValidator()
        
        # Test protocol detection with simple content
        content = "vmess://test"
        protocols = validator._detect_protocols(content)
        assert 'vmess' in protocols
        
        # Test with different protocol
        content = "vless://test"
        protocols = validator._detect_protocols(content)
        assert 'vless' in protocols
        
        # Test that we can detect at least one protocol
        content = "vmess://test\nvless://test"
        protocols = validator._detect_protocols(content)
        assert len(protocols) >= 1
        assert any(p in protocols for p in ['vmess', 'vless'])
    
    def test_reliability_score_calculation(self):
        """Test reliability score calculation."""
        validator = UnifiedSourceValidator()
        
        # Test score calculation
        score = validator._calculate_reliability_score(200, 100, ['vmess', 'vless'])
        assert 0 <= score <= 1
        assert score > 0.5  # Should be reasonable score
