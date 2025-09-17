"""
Tests for StreamlineVPNMerger.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from streamline_vpn.core.merger import StreamlineVPNMerger


class TestStreamlineVPNMerger:
    """Test StreamlineVPNMerger class"""

    def test_initialization(self):
        """Test merger initialization"""
        merger = StreamlineVPNMerger()
        assert hasattr(merger, "config_processor")
        assert hasattr(merger, "source_manager")
        assert hasattr(merger, "output_manager")
        assert hasattr(merger, "is_processing")

    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test merger initialization"""
        merger = StreamlineVPNMerger()
        result = await merger.initialize()
        assert result is True

    def test_get_status(self):
        """Test getting merger status"""
        merger = StreamlineVPNMerger()
        status = merger.get_status()
        assert isinstance(status, dict)
        assert "is_processing" in status
        assert "config_count" in status
        assert "source_count" in status

    @pytest.mark.asyncio
    async def test_process_configurations(self):
        """Test processing configurations"""
        merger = StreamlineVPNMerger()
        await merger.initialize()

        # Mock the dependencies
        with patch.object(
            merger.source_manager, "get_all_sources"
        ) as mock_sources, patch.object(
            merger.config_processor, "process_configurations"
        ) as mock_process, patch.object(
            merger.output_manager, "save_configurations"
        ) as mock_save:

            mock_sources.return_value = [
                {"name": "test_source", "url": "http://test.com"}
            ]
            mock_process.return_value = [{"name": "test_config", "type": "vmess"}]
            mock_save.return_value = True

            result = await merger.process_configurations()
            assert result is True
            mock_sources.assert_called_once()
            mock_process.assert_called_once()
            mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_configurations_failure(self):
        """Test processing configurations with failure"""
        merger = StreamlineVPNMerger()
        await merger.initialize()

        # Mock the dependencies to fail
        with patch.object(merger.source_manager, "get_all_sources") as mock_sources:
            mock_sources.side_effect = Exception("Source error")

            result = await merger.process_configurations()
            assert result is False

    @pytest.mark.asyncio
    async def test_cleanup(self):
        """Test merger cleanup"""
        merger = StreamlineVPNMerger()
        await merger.initialize()

        result = await merger.cleanup()
        assert result is True
