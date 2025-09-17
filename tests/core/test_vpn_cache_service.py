"""
Tests for VPNCacheService.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from streamline_vpn.core.caching.service import VPNCacheService


class TestVPNCacheService:
    """Test VPNCacheService class"""

    def test_initialization(self):
        """Test cache service initialization"""
        service = VPNCacheService()
        assert hasattr(service, "l1_cache")
        assert hasattr(service, "l2_cache")
        assert hasattr(service, "l3_cache")
        assert hasattr(service, "is_initialized")

    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test cache service initialization"""
        service = VPNCacheService()
        result = await service.initialize()
        assert result is True
        assert service.is_initialized is True

    def test_get_status(self):
        """Test getting cache service status"""
        service = VPNCacheService()
        status = service.get_status()
        assert isinstance(status, dict)
        assert "is_initialized" in status
        assert "l1_status" in status
        assert "l2_status" in status
        assert "l3_status" in status

    @pytest.mark.asyncio
    async def test_get_configuration(self):
        """Test getting configuration from cache"""
        service = VPNCacheService()
        await service.initialize()

        # Mock the cache layers
        with patch.object(service.l1_cache, "get") as mock_l1, patch.object(
            service.l2_cache, "get"
        ) as mock_l2, patch.object(service.l3_cache, "get") as mock_l3:

            mock_l1.return_value = None
            mock_l2.return_value = None
            mock_l3.return_value = {"name": "test_config", "type": "vmess"}

            result = await service.get_configuration("test_key")
            assert result == {"name": "test_config", "type": "vmess"}
            mock_l1.assert_called_once_with("test_key")
            mock_l2.assert_called_once_with("test_key")
            mock_l3.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_set_configuration(self):
        """Test setting configuration in cache"""
        service = VPNCacheService()
        await service.initialize()

        config = {"name": "test_config", "type": "vmess"}

        # Mock the cache layers
        with patch.object(service.l1_cache, "set") as mock_l1, patch.object(
            service.l2_cache, "set"
        ) as mock_l2, patch.object(service.l3_cache, "set") as mock_l3:

            mock_l1.return_value = True
            mock_l2.return_value = True
            mock_l3.return_value = True

            result = await service.set_configuration("test_key", config)
            assert result is True
            mock_l1.assert_called_once_with("test_key", config)
            mock_l2.assert_called_once_with("test_key", config)
            mock_l3.assert_called_once_with("test_key", config)

    @pytest.mark.asyncio
    async def test_invalidate_configuration(self):
        """Test invalidating configuration from cache"""
        service = VPNCacheService()
        await service.initialize()

        # Mock the cache layers
        with patch.object(service.l1_cache, "delete") as mock_l1, patch.object(
            service.l2_cache, "delete"
        ) as mock_l2, patch.object(service.l3_cache, "delete") as mock_l3:

            mock_l1.return_value = True
            mock_l2.return_value = True
            mock_l3.return_value = True

            result = await service.invalidate_configuration("test_key")
            assert result is True
            mock_l1.assert_called_once_with("test_key")
            mock_l2.assert_called_once_with("test_key")
            mock_l3.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_cleanup(self):
        """Test cache service cleanup"""
        service = VPNCacheService()
        await service.initialize()

        result = await service.cleanup()
        assert result is True
