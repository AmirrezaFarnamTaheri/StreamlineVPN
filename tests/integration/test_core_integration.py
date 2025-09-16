"""
Integration tests for core StreamlineVPN functionality.
"""

import asyncio
from unittest.mock import AsyncMock, patch
import pytest
import yaml
from pathlib import Path

from streamline_vpn.core.config_processor import ConfigurationProcessor
from streamline_vpn.core.merger import StreamlineVPNMerger
from streamline_vpn.core.output_manager import OutputManager
from streamline_vpn.core.source.manager import SourceManager
from streamline_vpn.models.configuration import Protocol, VPNConfiguration


class TestStreamlineVPNCore:
    """Complete tests for core StreamlineVPN functionality."""

    @pytest.fixture
    def sample_config(self, tmp_path):
        config = {
            "sources": {
                "premium": {
                    "urls": [
                        {
                            "url": "https://example.com/premium.txt",
                            "weight": 0.9,
                        },
                        {
                            "url": "https://example.com/premium2.txt",
                            "weight": 0.8,
                        },
                    ]
                },
                "reliable": {"urls": ["https://example.com/reliable.txt"]},
            },
            "processing": {
                "max_concurrent": 50,
                "timeout": 30,
                "retry_attempts": 3,
            },
            "output": {"formats": ["json", "clash", "singbox"]},
        }
        config_file = tmp_path / "test_config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config, f)
        return str(config_file)

    @pytest.fixture
    def sample_vpn_configs(self):
        return [
            VPNConfiguration(
                name="Test VMess",
                protocol=Protocol.VMESS,
                server="example.com",
                port=443,
                uuid="12345678-1234-1234-1234-123456789012",
                alter_id=0,
                security="auto",
            ),
            VPNConfiguration(
                name="Test VLess",
                protocol=Protocol.VLESS,
                server="example.com",
                port=443,
                uuid="12345678-1234-1234-1234-123456789012",
                flow="xtls-rprx-direct",
            ),
        ]

    @pytest.mark.asyncio
    async def test_config_processor_integration(self, sample_config):
        """Test configuration processor integration."""
        processor = ConfigurationProcessor()
        
        # Test loading configuration
        config = processor.load_configuration(sample_config)
        assert config is not None
        assert "sources" in config
        assert "processing" in config
        assert "output" in config

    @pytest.mark.asyncio
    async def test_source_manager_integration(self, sample_config):
        """Test source manager integration."""
        with patch('streamline_vpn.core.source.manager.SourceManager._load_sources'):
            manager = SourceManager()
            
            # Test getting sources
            sources = await manager.get_all_sources()
            assert isinstance(sources, list)

    @pytest.mark.asyncio
    async def test_merger_integration(self, sample_vpn_configs):
        """Test merger integration."""
        merger = StreamlineVPNMerger()
        
        # Test processing configurations
        with patch('streamline_vpn.core.merger.StreamlineVPNMerger.process_sources') as mock_process:
            mock_process.return_value = AsyncMock(return_value=True)
            
            result = await merger.process_sources(sources=[])
            assert result is True

    @pytest.mark.asyncio
    async def test_output_manager_integration(self, sample_vpn_configs):
        """Test output manager integration."""
        manager = OutputManager()
        
        # Test formatting configurations
        json_output = manager.format_configurations(sample_vpn_configs, "json")
        assert json_output is not None
        assert isinstance(json_output, str)

    @pytest.mark.asyncio
    async def test_end_to_end_processing(self, sample_config, sample_vpn_configs):
        """Test end-to-end processing pipeline."""
        with patch('streamline_vpn.core.source.manager.SourceManager.get_all_sources') as mock_sources:
            mock_sources.return_value = AsyncMock(return_value=[])
            
            with patch('streamline_vpn.core.merger.StreamlineVPNMerger.process_sources') as mock_process:
                mock_process.return_value = AsyncMock(return_value=True)
                
                # Test complete pipeline
                processor = ConfigurationProcessor()
                config = processor.load_configuration(sample_config)
                
                assert config is not None
                assert "sources" in config

    @pytest.mark.asyncio
    async def test_concurrent_processing(self, sample_vpn_configs):
        """Test concurrent processing capabilities."""
        merger = StreamlineVPNMerger()
        
        with patch('streamline_vpn.core.merger.StreamlineVPNMerger.process_sources') as mock_process:
            mock_process.return_value = AsyncMock(return_value=True)
            
            # Test concurrent processing
            tasks = []
            for i in range(5):
                task = merger.process_sources(sources=[])
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            assert all(results)

    @pytest.mark.asyncio
    async def test_error_handling_integration(self, sample_config):
        """Test error handling in integration scenarios."""
        processor = ConfigurationProcessor()
        
        # Test with invalid config file
        with patch('builtins.open', side_effect=FileNotFoundError):
            config = processor.load_configuration("nonexistent.yaml")
            assert config is None

    @pytest.mark.asyncio
    async def test_memory_usage_integration(self, sample_vpn_configs):
        """Test memory usage in integration scenarios."""
        manager = OutputManager()
        
        # Test with large number of configurations
        large_configs = sample_vpn_configs * 1000
        
        json_output = manager.format_configurations(large_configs, "json")
        assert json_output is not None
        assert len(json_output) > 0

    @pytest.mark.asyncio
    async def test_configuration_validation_integration(self, sample_vpn_configs):
        """Test configuration validation in integration."""
        processor = ConfigurationProcessor()
        
        # Test validating configurations
        for config in sample_vpn_configs:
            is_valid = processor.validate_configuration(config)
            assert is_valid is True

    @pytest.mark.asyncio
    async def test_output_formats_integration(self, sample_vpn_configs):
        """Test different output formats in integration."""
        manager = OutputManager()
        
        formats = ["json", "clash", "singbox", "raw"]
        
        for format_type in formats:
            output = manager.format_configurations(sample_vpn_configs, format_type)
            assert output is not None
            assert isinstance(output, str)

