"""
Focused tests for ConfigurationProcessor
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from streamline_vpn.core.config_processor import ConfigurationProcessor


class TestConfigurationProcessor:
    """Test ConfigurationProcessor class"""
    
    def test_initialization(self):
        """Test config processor initialization"""
        processor = ConfigurationProcessor()
        assert hasattr(processor, 'sources')
        assert hasattr(processor, 'merger')
        assert hasattr(processor, 'is_initialized')
    
    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test config processor initialization"""
        processor = ConfigurationProcessor()
        result = await processor.initialize()
        assert result is True
        assert processor.is_initialized is True
    
    def test_load_sources(self):
        """Test loading sources from config"""
        processor = ConfigurationProcessor()
        
        config = {
            "sources": [
                {"name": "source1", "url": "https://example.com/source1.txt"},
                {"name": "source2", "url": "https://example.com/source2.txt"}
            ]
        }
        
        processor.load_sources(config)
        assert len(processor.sources) == 2
        assert processor.sources[0]["name"] == "source1"
        assert processor.sources[1]["name"] == "source2"
    
    def test_load_sources_empty(self):
        """Test loading empty sources"""
        processor = ConfigurationProcessor()
        
        config = {"sources": []}
        processor.load_sources(config)
        assert len(processor.sources) == 0
    
    def test_load_sources_no_sources_key(self):
        """Test loading sources when no sources key"""
        processor = ConfigurationProcessor()
        
        config = {"other": "value"}
        processor.load_sources(config)
        assert len(processor.sources) == 0
    
    @pytest.mark.asyncio
    async def test_process_sources(self):
        """Test processing sources"""
        processor = ConfigurationProcessor()
        await processor.initialize()
        
        processor.sources = [
            {"name": "source1", "url": "https://example.com/source1.txt"},
            {"name": "source2", "url": "https://example.com/source2.txt"}
        ]
        
        with patch.object(processor.merger, 'process_source') as mock_process:
            mock_process.return_value = {"success": True, "configs": []}
            
            result = await processor.process_sources()
            assert result is not None
            assert "processed_sources" in result
            assert "total_configs" in result
            assert result["processed_sources"] == 2
    
    def test_get_processor_status(self):
        """Test getting processor status"""
        processor = ConfigurationProcessor()
        
        status = processor.get_processor_status()
        assert "is_initialized" in status
        assert "sources_count" in status
        assert "merger_available" in status
        assert status["is_initialized"] is False
        assert status["sources_count"] == 0
        assert status["merger_available"] is False
    
    def test_reset_processor(self):
        """Test resetting processor"""
        processor = ConfigurationProcessor()
        processor.sources = [{"name": "test", "url": "https://example.com"}]
        processor.is_initialized = True
        
        processor.reset_processor()
        assert processor.sources == []
        assert processor.is_initialized is False
        assert processor.merger is None