"""
Core Component Tests
====================

Tests for core StreamlineVPN components.
"""

# isort:skip_file

import sys
import time
import asyncio
import types
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest


class _FakeFormatter:
    """Minimal formatter implementation used for tests."""

    def __init__(self, output_path):
        self.output_path = Path(output_path)

    def get_file_extension(
        self,
    ):  # pragma: no cover - overridden in subclasses
        return ""

    def save_configurations(self, configs, filename):
        path = self.output_path / f"{filename}{self.get_file_extension()}"
        self.output_path.mkdir(parents=True, exist_ok=True)
        Path(path).touch()
        return path


class JSONFormatter(_FakeFormatter):
    def get_file_extension(self):  # pragma: no cover - simple override
        return ".json"


class ClashFormatter(_FakeFormatter):
    def get_file_extension(self):  # pragma: no cover - simple override
        return ".yaml"


class SingBoxFormatter(_FakeFormatter):
    def get_file_extension(self):  # pragma: no cover - simple override
        return ".singbox.json"


class RawFormatter(_FakeFormatter):
    def get_file_extension(self):  # pragma: no cover - simple override
        return ""

    def save_configurations(self, configs, filename):
        path = self.output_path / filename
        self.output_path.mkdir(parents=True, exist_ok=True)
        Path(path).touch()
        return path


output_module = types.ModuleType("streamline_vpn.core.output")
output_module.JSONFormatter = JSONFormatter
output_module.ClashFormatter = ClashFormatter
output_module.SingBoxFormatter = SingBoxFormatter
output_module.RawFormatter = RawFormatter
sys.modules["streamline_vpn.core.output"] = output_module


class FakeRedis:
    """Simplified in-memory async Redis replacement."""

    def __init__(self):
        self.store = {}
        self.expiry = {}

    async def get(self, key):
        exp = self.expiry.get(key)
        if exp is not None and exp <= time.monotonic():
            self.store.pop(key, None)
            self.expiry.pop(key, None)
            return None
        return self.store.get(key)

    async def set(self, key, value, ttl=None):
        self.store[key] = value
        if ttl is not None:
            try:
                ttl_val = float(ttl)
            except (TypeError, ValueError):
                # Treat invalid TTLs as no expiry to keep tests stable
                self.expiry.pop(key, None)
                return True
            # Zero or negative TTLs expire immediately
            if ttl_val <= 0:
                self.store.pop(key, None)
                self.expiry.pop(key, None)
                return True
            self.expiry[key] = time.monotonic() + ttl_val
        else:
            # Remove any existing expiry to mimic Redis behaviour
            self.expiry.pop(key, None)
        return True

    async def delete(self, key):
        self.store.pop(key, None)
        self.expiry.pop(key, None)
        return True

    def get_stats(self):
        return {
            "hits": 0,
            "misses": 0,
            "hit_rate": 0.0,
            "avg_response_time": 0.0,
        }


fakeredis_module = types.ModuleType("fakeredis.aioredis")
fakeredis_module.FakeRedis = FakeRedis
sys.modules["fakeredis.aioredis"] = fakeredis_module
fakeredis_pkg = types.ModuleType("fakeredis")
fakeredis_pkg.aioredis = fakeredis_module
sys.modules["fakeredis"] = fakeredis_pkg

from streamline_vpn.core.cache_manager import CacheManager  # noqa: E402
from streamline_vpn.core.config_processor import (
    ConfigurationProcessor,
)  # noqa: E402
from streamline_vpn.core.merger import StreamlineVPNMerger  # noqa: E402
from streamline_vpn.core.output_manager import OutputManager  # noqa: E402
from streamline_vpn.core.source_manager import SourceManager  # noqa: E402
from streamline_vpn.models.configuration import (  # noqa: E402
    Protocol,
    VPNConfiguration,
)


class TestStreamlineVPNMerger:
    """Test StreamlineVPN merger functionality."""

    @pytest.fixture
    async def merger(self, tmp_path):
        """Create a merger instance with mocked dependencies for testing."""
        config_file = tmp_path / "test_sources.yaml"
        config_file.write_text(
            """
            sources:
              premium:
                urls:
                  - url: http://source1.com/sub
            processing:
              max_concurrent: 10
            output:
              formats: [json]
            """
        )

        # We patch the class constructors to control the instances created by the merger
        with patch("streamline_vpn.core.merger.VPNCacheService", autospec=True), \
             patch("streamline_vpn.core.merger.FetcherService", autospec=True), \
             patch("streamline_vpn.core.merger.SourceManager", autospec=True) as MockSourceManager, \
             patch("streamline_vpn.core.merger.ConfigurationProcessor", autospec=True), \
             patch("streamline_vpn.core.merger.OutputManager", autospec=True), \
             patch("streamline_vpn.core.merger.SecurityManager", autospec=True), \
             patch("streamline_vpn.core.merger.MergerProcessor", autospec=True):

            # Configure the return values of the mocked class instances
            mock_source_manager_instance = MockSourceManager.return_value
            mock_source_manager_instance.get_source_statistics.return_value = {
                "total_sources": 1,
                "active_sources": 1,
                "average_reputation": 0.5,
            }

            # The merger instance to be tested
            merger_instance = StreamlineVPNMerger(config_path=str(config_file))

            # The initialize method will now use the mocked classes
            await merger_instance.initialize()

            # The merger processor is created inside initialize, so we need to access it from the instance
            merger_instance.merger_processor.process_sources.return_value = [
                VPNConfiguration(protocol=Protocol.VMESS, server="test.com", port=443, user_id="123", metadata={})
            ]
            merger_instance.merger_processor.deduplicate_configurations.side_effect = lambda configs: configs
            merger_instance.merger_processor.apply_enhancements.side_effect = lambda configs: configs

            yield merger_instance

    @pytest.mark.asyncio
    async def test_merger_initialization(self, merger):
        """Test merger initialization with mocked components."""
        assert merger is not None
        assert merger.initialized is True
        assert merger.source_manager is not None
        assert merger.config_processor is not None
        assert merger.output_manager is not None
        assert merger.merger_processor is not None
        assert merger.config['processing']['max_concurrent'] == 10

    @pytest.mark.asyncio
    async def test_process_all_no_configs_found(self, merger):
        """Test processing when sources yield no configurations."""
        # Mock the merger_processor to return no configs and 0 successful sources
        merger.merger_processor.process_sources.return_value = ([], 0)
        merger.merger_processor.deduplicate_configurations.return_value = []

        result = await merger.process_all()

        assert result["success"] is True
        assert result["total_configurations"] == 0
        assert "No configurations found in any source" in result["warnings"]

    @pytest.mark.asyncio
    async def test_get_statistics(self, merger):
        """Test statistics retrieval."""
        stats = await merger.get_statistics()
        assert isinstance(stats, dict)
        assert "total_sources" in stats
        assert stats["total_sources"] == 1


class TestSourceManager:
    """Test source manager functionality."""

    @pytest.fixture
    def source_manager(self):
        """Create source manager instance for testing."""
        config_path = Path("tests/fixtures/test_sources.yaml")
        mock_security_manager = Mock()
        mock_security_manager.validate_source.return_value = {"is_safe": True}
        return SourceManager(config_path, mock_security_manager)

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
                protocol=Protocol.VMESS,
                server="test.com",
                port=443,
                user_id="test-id",
            )
        ]

        with patch("builtins.open", Mock()):
            result = await output_manager.save_configurations(
                configs, "test_output", "json"
            )
            assert isinstance(result, Path)

    @pytest.mark.asyncio
    async def test_save_configurations_sync_raises_in_event_loop(
        self, output_manager
    ):
        """Ensure synchronous wrapper raises inside an event loop."""
        with patch.object(output_manager, "save_configurations", AsyncMock()):
            with pytest.raises(
                RuntimeError,
                match="save_configurations_sync cannot run inside an event loop",
            ):
                output_manager.save_configurations_sync([], "test_output")

    def test_save_configurations_sync_runs_outside_event_loop(
        self, output_manager
    ):
        """Ensure synchronous wrapper works when no event loop is running."""
        with patch.object(
            output_manager, "save_configurations", AsyncMock(return_value="ok")
        ):
            result = output_manager.save_configurations_sync([], "test_output")
            assert result == "ok"


import fakeredis.aioredis  # noqa: E402


class TestCacheManager:
    """Test cache manager functionality."""

    @pytest.fixture
    def cache_manager(self):
        """Create cache manager instance for testing."""
        redis_nodes = [{"host": "localhost", "port": "6379"}]
        cm = CacheManager(redis_nodes)
        cm.redis_client = fakeredis.aioredis.FakeRedis()
        return cm

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

    @pytest.mark.asyncio
    async def test_cache_ttl_expiration(self, cache_manager):
        """Ensure cached values expire after TTL."""
        key = "ttl_key"
        value = {"exp": "soon"}

        await cache_manager.set(key, value, ttl=0.01)
        await asyncio.sleep(0.02)
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
