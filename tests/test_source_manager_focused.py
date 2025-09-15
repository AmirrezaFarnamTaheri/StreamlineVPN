"""
Focused tests for SourceManager
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from streamline_vpn.core.source_manager import SourceManager


class TestSourceManager:
    """Test SourceManager class"""
    
    def test_initialization(self):
        """Test source manager initialization"""
        manager = SourceManager()
        assert hasattr(manager, 'sources')
        assert hasattr(manager, 'fetcher')
        assert hasattr(manager, 'is_initialized')
    
    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test source manager initialization"""
        manager = SourceManager()
        result = await manager.initialize()
        assert result is True
        assert manager.is_initialized is True
    
    @pytest.mark.asyncio
    async def test_add_source(self):
        """Test adding source"""
        manager = SourceManager()
        await manager.initialize()
        
        source_data = {
            "name": "test_source",
            "url": "https://example.com/source.txt",
            "type": "subscription"
        }
        
        result = await manager.add_source(source_data)
        assert result is not None
        assert "success" in result
    
    @pytest.mark.asyncio
    async def test_add_source_duplicate(self):
        """Test adding duplicate source"""
        manager = SourceManager()
        await manager.initialize()
        
        source_data = {
            "name": "test_source",
            "url": "https://example.com/source.txt",
            "type": "subscription"
        }
        
        # Add source first time
        await manager.add_source(source_data)
        
        # Try to add same source again
        result = await manager.add_source(source_data)
        assert result is not None
        assert "success" in result
    
    def test_remove_source(self):
        """Test removing source"""
        manager = SourceManager()
        
        with patch.object(manager, 'remove_source') as mock_remove:
            mock_remove.return_value = True
            
            result = manager.remove_source("test_source")
            assert result is True
            mock_remove.assert_called_once_with("test_source")
    
    def test_remove_source_not_found(self):
        """Test removing non-existent source"""
        manager = SourceManager()
        
        with patch.object(manager, 'remove_source') as mock_remove:
            mock_remove.return_value = False
            
            result = manager.remove_source("nonexistent")
            assert result is False
            mock_remove.assert_called_once_with("nonexistent")
    
    def test_get_source(self):
        """Test getting source"""
        manager = SourceManager()
        
        with patch.object(manager, 'get_source') as mock_get:
            mock_get.return_value = {"name": "test", "url": "https://example.com"}
            
            result = manager.get_source("test")
            assert result["name"] == "test"
            mock_get.assert_called_once_with("test")
    
    def test_get_source_not_found(self):
        """Test getting non-existent source"""
        manager = SourceManager()
        
        with patch.object(manager, 'get_source') as mock_get:
            mock_get.return_value = None
            
            result = manager.get_source("nonexistent")
            assert result is None
            mock_get.assert_called_once_with("nonexistent")
    
    def test_list_sources(self):
        """Test listing sources"""
        manager = SourceManager()
        
        with patch.object(manager, 'list_sources') as mock_list:
            mock_list.return_value = [{"name": "test1"}, {"name": "test2"}]
            
            result = manager.list_sources()
            assert len(result) == 2
            mock_list.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fetch_source(self):
        """Test fetching source"""
        manager = SourceManager()
        await manager.initialize()
        
        with patch.object(manager, 'fetch_source') as mock_fetch:
            mock_fetch.return_value = {"success": True, "data": "test data"}
            
            result = await manager.fetch_source("test_source")
            assert result["success"] is True
            mock_fetch.assert_called_once_with("test_source")
    
    @pytest.mark.asyncio
    async def test_fetch_source_not_found(self):
        """Test fetching non-existent source"""
        manager = SourceManager()
        await manager.initialize()
        
        with patch.object(manager, 'fetch_source') as mock_fetch:
            mock_fetch.return_value = {"success": False, "error": "Source not found"}
            
            result = await manager.fetch_source("nonexistent")
            assert result["success"] is False
            mock_fetch.assert_called_once_with("nonexistent")
    
    @pytest.mark.asyncio
    async def test_fetch_all_sources(self):
        """Test fetching all sources"""
        manager = SourceManager()
        await manager.initialize()
        
        with patch.object(manager, 'fetch_all_sources') as mock_fetch:
            mock_fetch.return_value = {"success": True, "sources": []}
            
            result = await manager.fetch_all_sources()
            assert result["success"] is True
            mock_fetch.assert_called_once()
    
    def test_get_source_stats(self):
        """Test getting source statistics"""
        manager = SourceManager()
        
        with patch.object(manager, 'get_source_stats') as mock_stats:
            mock_stats.return_value = {"total_sources": 0, "active_sources": 0}
            
            result = manager.get_source_stats()
            assert "total_sources" in result
            assert "active_sources" in result
            mock_stats.assert_called_once()
    
    def test_clear_sources(self):
        """Test clearing sources"""
        manager = SourceManager()
        
        with patch.object(manager, 'clear_sources') as mock_clear:
            mock_clear.return_value = None
            
            result = manager.clear_sources()
            assert result is None
            mock_clear.assert_called_once()
    
    def test_reset_manager(self):
        """Test resetting manager"""
        manager = SourceManager()
        
        with patch.object(manager, 'reset_manager') as mock_reset:
            mock_reset.return_value = None
            
            result = manager.reset_manager()
            assert result is None
            mock_reset.assert_called_once()
