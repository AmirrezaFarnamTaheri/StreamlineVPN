"""
Tests for SourceManager.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from streamline_vpn.core.source_manager import SourceManager


class TestSourceManager:
    """Test SourceManager class"""
    
    def test_initialization(self):
        """Test source manager initialization"""
        manager = SourceManager()
        assert hasattr(manager, 'sources')
        assert hasattr(manager, 'is_initialized')
    
    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test source manager initialization"""
        manager = SourceManager()
        result = await manager.initialize()
        assert result is True
        assert manager.is_initialized is True
    
    def test_get_status(self):
        """Test getting manager status"""
        manager = SourceManager()
        status = manager.get_status()
        assert isinstance(status, dict)
        assert 'is_initialized' in status
        assert 'source_count' in status
        assert 'active_sources' in status
    
    @pytest.mark.asyncio
    async def test_add_source(self):
        """Test adding a source"""
        manager = SourceManager()
        await manager.initialize()
        
        source_data = {
            "name": "test_source",
            "url": "http://example.com/config",
            "type": "subscription"
        }
        
        result = await manager.add_source(source_data)
        assert result is True
        
        sources = manager.get_all_sources()
        assert len(sources) == 1
        assert sources[0]["name"] == "test_source"
    
    @pytest.mark.asyncio
    async def test_get_all_sources(self):
        """Test getting all sources"""
        manager = SourceManager()
        await manager.initialize()
        
        # Add some test sources
        await manager.add_source({"name": "source1", "url": "http://test1.com"})
        await manager.add_source({"name": "source2", "url": "http://test2.com"})
        
        sources = manager.get_all_sources()
        assert len(sources) == 2
        assert all("name" in source for source in sources)
    
    @pytest.mark.asyncio
    async def test_remove_source(self):
        """Test removing a source"""
        manager = SourceManager()
        await manager.initialize()
        
        # Add a source first
        await manager.add_source({"name": "test_source", "url": "http://test.com"})
        assert len(manager.get_all_sources()) == 1
        
        # Remove the source
        result = await manager.remove_source("test_source")
        assert result is True
        assert len(manager.get_all_sources()) == 0
    
    @pytest.mark.asyncio
    async def test_remove_nonexistent_source(self):
        """Test removing a non-existent source"""
        manager = SourceManager()
        await manager.initialize()
        
        result = await manager.remove_source("nonexistent")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_cleanup(self):
        """Test manager cleanup"""
        manager = SourceManager()
        await manager.initialize()
        
        result = await manager.cleanup()
        assert result is True

