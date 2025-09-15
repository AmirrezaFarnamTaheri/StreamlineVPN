"""
Focused tests for StreamlineVPNMerger
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from streamline_vpn.core.merger import StreamlineVPNMerger


class TestStreamlineVPNMerger:
    """Test StreamlineVPNMerger class"""
    
    def test_initialization(self):
        """Test merger initialization"""
        merger = StreamlineVPNMerger()
        assert merger is not None
        assert hasattr(merger, 'source_manager')
        assert hasattr(merger, 'config_processor')
        assert hasattr(merger, 'output_manager')
    
    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test merger initialization"""
        merger = StreamlineVPNMerger()
        result = await merger.initialize()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_process_all(self):
        """Test processing all sources"""
        merger = StreamlineVPNMerger()
        await merger.initialize()
        
        with patch.object(merger.source_manager, 'fetch_all_sources') as mock_fetch:
            mock_fetch.return_value = {"success": True, "sources": []}
            
            result = await merger.process_all()
            assert result is not None
            assert "success" in result
            mock_fetch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_source(self):
        """Test processing single source"""
        merger = StreamlineVPNMerger()
        await merger.initialize()
        
        with patch.object(merger.config_processor, 'process_sources') as mock_process:
            mock_process.return_value = {"success": True, "configs": []}
            
            result = await merger.process_source("test_source")
            assert result is not None
            assert "success" in result
            mock_process.assert_called_once()
    
    def test_validate_configuration(self):
        """Test validating configuration"""
        merger = StreamlineVPNMerger()
        
        config = {"type": "vmess", "name": "test"}
        
        with patch.object(merger, 'validate_configuration') as mock_validate:
            mock_validate.return_value = {"is_valid": True, "errors": []}
            
            result = merger.validate_configuration(config)
            assert result["is_valid"] is True
            mock_validate.assert_called_once_with(config)
    
    def test_validate_configuration_invalid(self):
        """Test validating invalid configuration"""
        merger = StreamlineVPNMerger()
        
        config = {"type": "invalid"}
        
        with patch.object(merger, 'validate_configuration') as mock_validate:
            mock_validate.return_value = {"is_valid": False, "errors": ["Invalid type"]}
            
            result = merger.validate_configuration(config)
            assert result["is_valid"] is False
            mock_validate.assert_called_once_with(config)
    
    def test_list_sources(self):
        """Test listing sources"""
        merger = StreamlineVPNMerger()
        
        with patch.object(merger.source_manager, 'list_sources') as mock_list:
            mock_list.return_value = [{"name": "test1"}, {"name": "test2"}]
            
            result = merger.list_sources()
            assert len(result) == 2
            mock_list.assert_called_once()
    
    def test_add_source(self):
        """Test adding source"""
        merger = StreamlineVPNMerger()
        
        source_data = {"name": "test", "url": "https://example.com"}
        
        with patch.object(merger, 'add_source') as mock_add:
            mock_add.return_value = {"success": True}
            
            result = merger.add_source(source_data)
            assert result["success"] is True
            mock_add.assert_called_once_with(source_data)
    
    def test_health_check(self):
        """Test health check"""
        merger = StreamlineVPNMerger()
        
        with patch.object(merger, 'health_check') as mock_health:
            mock_health.return_value = {"status": "healthy", "components": {}}
            
            result = merger.health_check()
            assert result["status"] == "healthy"
            mock_health.assert_called_once()
