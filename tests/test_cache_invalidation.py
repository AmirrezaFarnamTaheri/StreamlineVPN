import pytest
from unittest.mock import MagicMock, AsyncMock
from streamline_vpn.core.caching.service import VPNCacheService
from streamline_vpn.core.source.manager import SourceManager

@pytest.mark.asyncio
async def test_add_source_invalidates_cache():
    cache_service = VPNCacheService()
    cache_service.invalidate_cache_pattern = AsyncMock()

    source_manager = SourceManager(cache_service=cache_service)
    await source_manager.add_source("http://example.com/source1.yaml")

    cache_service.invalidate_cache_pattern.assert_called_once_with("configuration_change")

@pytest.mark.asyncio
async def test_remove_source_invalidates_cache():
    cache_service = VPNCacheService()
    cache_service.invalidate_cache_pattern = AsyncMock()

    source_manager = SourceManager(cache_service=cache_service)
    await source_manager.add_source("http://example.com/source1.yaml")
    cache_service.invalidate_cache_pattern.reset_mock()

    await source_manager.remove_source("http://example.com/source1.yaml")

    cache_service.invalidate_cache_pattern.assert_called_once_with("configuration_change")
