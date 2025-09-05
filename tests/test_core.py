"""
Core Component Tests
====================

Tests for core StreamlineVPN components.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path

from streamline_vpn.core.merger import StreamlineVPNMerger
from streamline_vpn.core.source_manager import SourceManager
from streamline_vpn.core.config_processor import ConfigurationProcessor
from streamline_vpn.core.output_manager import OutputManager
from streamline_vpn.core.cache_manager import CacheManager
from streamline_vpn.models.configuration import VPNConfiguration, ProtocolType


class TestStreamlineVPNMerger:
    """Test StreamlineVPN merger functionality."""

    @pytest.fixture
    def merger(self):
        """Create merger instance for testing."""
        return StreamlineVPNMerger()

    @pytest.mark.asyncio
    async def test_merger_initialization(self, merger):
        """Test merger initialization."""
        assert merger is not None
        assert merger.source_manager is not None
        assert merger.config_processor is not None
        assert merger.output_manager is not None

    @pytest.mark.asyncio
    async def test_process_all_empty_sources(self, merger):
        """Test processing with no sources."""
        with patch.object(merger.source_manager, 'get_active_sources', return_value=[]):
            result = await merger.process_all()
            assert result["success"] is False
            assert "No sources found" in result["error"]

    @pytest.mark.asyncio
    async def test_get_statistics(self, merger):
        """Test statistics retrieval."""
        stats = await merger.get_statistics()
        assert isinstance(stats, dict)
        assert "total_sources" in stats


class TestSourceManager:
    """Test source manager functionality."""

    @pytest.fixture
    def source_manager(self):
        """Create source manager instance for testing."""
        config_path = Path("tests/fixtures/test_sources.yaml")
        return SourceManager(config_path)

    def test_source_manager_initialization(self, source_manager):
        """Test source manager initialization."""
        assert source_manager is not None
        assert isinstance(source_manager.sources, dict)

    @pytest.mark.asyncio
    async def test_get_active_sources(self, source_manager):
        """Test getting active sources."""
        sources = await source_manager.get_active_sources()
        assert isinstance(sources, list)

    def test_get_source_statistics(self, source_manager):
        """Test source statistics."""
        stats = source_manager.get_source_statistics()
        assert isinstance(stats, dict)
        assert "total_sources" in stats


class TestConfigurationProcessor:
    """Test configuration processor functionality."""

    @pytest.fixture
    def processor(self):
        """Create configuration processor instance for testing."""
        return ConfigurationProcessor()

    @pytest.mark.asyncio
    async def test_parse_vmess_config(self, processor):
        """Test parsing VMess configuration."""
        # This would need a valid VMess config for testing
        config_line = "vmess://test"
        result = await processor.parse_config(config_line)
        # Should return None for invalid config
        assert result is None

    def test_generate_config_hash(self, processor):
        """Test configuration hash generation."""
        config_line = "vmess://test"
        hash1 = processor._generate_config_hash(config_line)
        hash2 = processor._generate_config_hash(config_line)
        assert hash1 == hash2

    def test_get_statistics(self, processor):
        """Test processor statistics."""
        stats = processor.get_statistics()
        assert isinstance(stats, dict)


class TestOutputManager:
    """Test output manager functionality."""

    @pytest.fixture
    def output_manager(self):
        """Create output manager instance for testing."""
        return OutputManager()

    def test_supported_formats(self, output_manager):
        """Test supported output formats."""
        formats = output_manager.get_supported_formats()
        assert isinstance(formats, list)
        assert "raw" in formats
        assert "json" in formats

    @pytest.mark.asyncio
    async def test_save_configurations(self, output_manager):
        """Test saving configurations."""
        configs = [
            VPNConfiguration(
                protocol=ProtocolType.VMESS,
                server="test.com",
                port=443,
                user_id="test-id"
            )
        ]
        
        with patch('builtins.open', Mock()):
            result = await output_manager.save_configurations(
                configs, "test_output", "json"
            )
            assert isinstance(result, Path)


class TestCacheManager:
    """Test cache manager functionality."""

    @pytest.fixture
    def cache_manager(self):
        """Create cache manager instance for testing."""
        redis_nodes = [{"host": "localhost", "port": "6379"}]
        return CacheManager(redis_nodes)

    @pytest.mark.asyncio
    async def test_cache_set_get(self, cache_manager):
        """Test cache set and get operations."""
        key = "test_key"
        value = {"test": "data"}
        
        await cache_manager.set(key, value)
        result = await cache_manager.get(key)
        
        assert result == value

    @pytest.mark.asyncio
    async def test_cache_invalidate(self, cache_manager):
        """Test cache invalidation."""
        key = "test_key"
        value = {"test": "data"}
        
        await cache_manager.set(key, value)
        await cache_manager.invalidate(key)
        result = await cache_manager.get(key)
        
        assert result is None

    def test_get_statistics(self, cache_manager):
        """Test cache statistics."""
        stats = cache_manager.get_statistics()
        assert isinstance(stats, dict)
        assert "l1_cache" in stats
        assert "l2_redis" in stats
        assert "circuit_breaker" in stats


if __name__ == "__main__":
    pytest.main([__file__])
