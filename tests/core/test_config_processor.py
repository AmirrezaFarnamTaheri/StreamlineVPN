"""
Tests for ConfigurationProcessor.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from streamline_vpn.core.config_processor import ConfigurationProcessor


class TestConfigurationProcessor:
    """Test ConfigurationProcessor class"""

    def test_initialization(self):
        """Test config processor initialization"""
        processor = ConfigurationProcessor()
        assert hasattr(processor, "validator")
        assert hasattr(processor, "deduplicator")
        assert hasattr(processor, "is_processing")

    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test config processor initialization"""
        processor = ConfigurationProcessor()
        result = await processor.initialize()
        assert result is True

    def test_get_status(self):
        """Test getting processor status"""
        processor = ConfigurationProcessor()
        status = processor.get_status()
        assert isinstance(status, dict)
        assert "is_processing" in status
        assert "processed_count" in status
        assert "valid_count" in status
        assert "invalid_count" in status

    @pytest.mark.asyncio
    async def test_process_configurations(self):
        """Test processing configurations"""
        processor = ConfigurationProcessor()
        await processor.initialize()

        configs = [
            {"name": "test1", "type": "vmess", "server": "example.com"},
            {"name": "test2", "type": "vless", "server": "test.com"},
        ]

        result = await processor.process_configurations(configs)
        assert isinstance(result, list)
        assert len(result) <= len(configs)

    @pytest.mark.asyncio
    async def test_process_configurations_empty(self):
        """Test processing empty configurations"""
        processor = ConfigurationProcessor()
        await processor.initialize()

        result = await processor.process_configurations([])
        assert result == []

    @pytest.mark.asyncio
    async def test_cleanup(self):
        """Test processor cleanup"""
        processor = ConfigurationProcessor()
        await processor.initialize()

        result = await processor.cleanup()
        assert result is True
