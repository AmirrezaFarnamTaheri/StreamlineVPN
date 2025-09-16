"""
Tests for OutputManager.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from streamline_vpn.core.output_manager import OutputManager


class TestOutputManager:
    """Test OutputManager class"""
    
    def test_initialization(self):
        """Test output manager initialization"""
        manager = OutputManager()
        assert hasattr(manager, 'output_formats')
        assert hasattr(manager, 'output_destinations')
        assert hasattr(manager, 'is_initialized')
    
    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test output manager initialization"""
        manager = OutputManager()
        result = await manager.initialize()
        assert result is True
        assert manager.is_initialized is True
    
    def test_get_status(self):
        """Test getting manager status"""
        manager = OutputManager()
        status = manager.get_status()
        assert isinstance(status, dict)
        assert 'is_initialized' in status
        assert 'output_formats' in status
        assert 'output_destinations' in status
    
    @pytest.mark.asyncio
    async def test_save_configurations(self):
        """Test saving configurations"""
        manager = OutputManager()
        await manager.initialize()
        
        configs = [
            {"name": "test1", "type": "vmess", "server": "example.com"},
            {"name": "test2", "type": "vless", "server": "test.com"}
        ]
        
        result = await manager.save_configurations(configs)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_save_configurations_empty(self):
        """Test saving empty configurations"""
        manager = OutputManager()
        await manager.initialize()
        
        result = await manager.save_configurations([])
        assert result is True
    
    @pytest.mark.asyncio
    async def test_export_configurations(self):
        """Test exporting configurations"""
        manager = OutputManager()
        await manager.initialize()
        
        configs = [{"name": "test", "type": "vmess"}]
        result = await manager.export_configurations(configs, "json")
        assert result is True
    
    @pytest.mark.asyncio
    async def test_cleanup(self):
        """Test manager cleanup"""
        manager = OutputManager()
        await manager.initialize()
        
        result = await manager.cleanup()
        assert result is True

