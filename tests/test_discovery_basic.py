"""
Basic tests for discovery module
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from streamline_vpn.discovery.manager import DiscoveryManager


class TestDiscoveryBasic:
    """Test basic discovery functionality"""
    
    def test_discovery_manager_initialization(self):
        """Test discovery manager initialization"""
        manager = DiscoveryManager()
        assert manager is not None
        assert hasattr(manager, 'discover_sources')
        assert hasattr(manager, 'get_discovered_sources')
        assert hasattr(manager, 'get_statistics')
    
    @pytest.mark.asyncio
    async def test_discover_sources(self):
        """Test discovering sources"""
        manager = DiscoveryManager()
        
        with patch.object(manager, 'discover_sources') as mock_discover:
            mock_discover.return_value = []
            
            result = await manager.discover_sources()
            assert result == []
            mock_discover.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_discovered_sources(self):
        """Test getting discovered sources"""
        manager = DiscoveryManager()
        
        # Test getting empty list initially
        sources = manager.get_discovered_sources()
        assert isinstance(sources, list)
        assert len(sources) == 0
    
    def test_get_statistics(self):
        """Test getting statistics"""
        manager = DiscoveryManager()
        
        stats = manager.get_statistics()
        assert isinstance(stats, dict)
        assert "discovered_sources_count" in stats
        assert "last_discovery" in stats
    
    def test_discovery_manager_methods_exist(self):
        """Test that discovery manager has expected methods"""
        manager = DiscoveryManager()
        
        # Check that the manager has the expected methods
        assert hasattr(manager, 'discover_sources')
        assert hasattr(manager, 'get_discovered_sources')
        assert hasattr(manager, 'get_statistics')
        
        # Check that they are callable
        assert callable(manager.discover_sources)
        assert callable(manager.get_discovered_sources)
        assert callable(manager.get_statistics)
