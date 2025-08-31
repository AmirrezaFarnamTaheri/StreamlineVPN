"""
Test Merger Integration
======================

Focused tests for the main VPNSubscriptionMerger integration functionality.
"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from vpn_merger.core.merger import VPNSubscriptionMerger
from vpn_merger.core.source_manager import SourceManager
from vpn_merger.core.config_processor import ConfigurationProcessor
from vpn_merger.models.configuration import VPNConfiguration


class TestVPNSubscriptionMerger:
    """Test the VPNSubscriptionMerger class comprehensively."""
    
    @pytest.fixture
    def merger(self):
        """Create a VPNSubscriptionMerger instance for testing."""
        return VPNSubscriptionMerger()
    
    @pytest.fixture
    def mock_source_manager(self):
        """Create a mock source manager."""
        mock_sm = Mock(spec=SourceManager)
        mock_sm.get_all_sources.return_value = [
            "https://example1.com/config1.txt",
            "https://example2.com/config2.txt",
            "https://example3.com/config3.txt"
        ]
        mock_sm.get_prioritized_sources.return_value = [
            "https://example1.com/config1.txt",
            "https://example2.com/config2.txt",
            "https://example3.com/config3.txt"
        ]
        return mock_sm
    
    @pytest.fixture
    def mock_config_processor(self):
        """Create a mock config processor."""
        mock_cp = Mock(spec=ConfigurationProcessor)
        mock_cp.process_config.return_value = VPNConfiguration(
            config="vmess://test",
            protocol="vmess",
            quality_score=0.8
        )
        return mock_cp
    
    def test_initialization(self, merger):
        """Test VPNSubscriptionMerger initialization."""
        assert merger is not None
        assert isinstance(merger.source_manager, SourceManager)
        assert isinstance(merger.config_processor, ConfigurationProcessor)
        assert isinstance(merger.results, list)
        assert len(merger.results) == 0
        assert isinstance(merger.stats, dict)
        assert merger.stats['total_sources'] == 0
        assert merger.stats['processed_sources'] == 0
        assert merger.stats['total_configs'] == 0
        assert merger.stats['valid_configs'] == 0
        assert merger.stats['duplicate_configs'] == 0
    
    def test_get_statistics(self, merger):
        """Test statistics retrieval."""
        # Set some mock stats
        merger.stats['total_sources'] = 10
        merger.stats['processed_sources'] = 8
        merger.stats['total_configs'] = 100
        merger.stats['valid_configs'] = 95
        merger.stats['duplicate_configs'] = 5
        merger.source_processing_times = {'source1': 1.5}
        merger.error_counts = {'source1': 1}
        
        stats = merger.get_statistics()
        
        assert stats['total_sources'] == 10
        assert stats['processed_sources'] == 8
        assert stats['total_configs'] == 100
        assert stats['valid_configs'] == 95
        assert stats['duplicate_configs'] == 5
        assert stats['source_processing_times'] == {'source1': 1.5}
        assert stats['error_counts'] == {'source1': 1}
        assert stats['success_rate'] == 0.8  # 8/10
    
    @pytest.mark.asyncio
    async def test_fetch_source_content_success(self, merger):
        """Test successful source content fetching."""
        mock_content = "vmess://config1\nvless://config2\ntrojan://config3"
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value=mock_content)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            content = await merger._fetch_source_content("https://example.com/config.txt")
            
            assert len(content) == 3
            assert "vmess://config1" in content
            assert "vless://config2" in content
            assert "trojan://config3" in content
    
    @pytest.mark.asyncio
    async def test_fetch_source_content_failure(self, merger):
        """Test source content fetching failure."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 404
            mock_get.return_value.__aenter__.return_value = mock_response
            
            content = await merger._fetch_source_content("https://example.com/config.txt")
            
            assert len(content) == 0
    
    @pytest.mark.asyncio
    async def test_fetch_source_content_exception(self, merger):
        """Test source content fetching with exception."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = Exception("Connection failed")
            
            content = await merger._fetch_source_content("https://example.com/config.txt")
            
            assert len(content) == 0
    
    @pytest.mark.asyncio
    async def test_process_single_source_success(self, merger):
        """Test successful single source processing."""
        source_url = "https://example.com/config.txt"
        
        # Mock the health checker
        with patch('vpn_merger.core.merger.UnifiedSourceValidator') as mock_hc_class:
            mock_hc = Mock()
            mock_hc.validate_source.return_value = {'accessible': True}
            mock_hc_class.return_value.__aenter__.return_value = mock_hc
            
            # Mock content fetching
            with patch.object(merger, '_fetch_source_content', return_value=["vmess://config1"]):
                # Mock config processing
                with patch.object(merger.config_processor, 'process_config', return_value=VPNConfiguration(
                    config="vmess://config1",
                    protocol="vmess"
                )):
                    await merger._process_single_source(source_url)
                    
                    assert merger.stats['processed_sources'] == 1
                    assert merger.stats['total_configs'] == 1
                    assert len(merger.results) == 1
    
    @pytest.mark.asyncio
    async def test_process_single_source_inaccessible(self, merger):
        """Test processing inaccessible source."""
        source_url = "https://example.com/config.txt"
        
        # Mock the health checker
        with patch('vpn_merger.core.merger.UnifiedSourceValidator') as mock_hc_class:
            mock_hc = Mock()
            mock_hc.validate_source.return_value = {'accessible': False}
            mock_hc_class.return_value.__aenter__.return_value = mock_hc
            
            await merger._process_single_source(source_url)
            
            assert merger.stats['processed_sources'] == 1
            assert merger.stats['total_configs'] == 0
            assert len(merger.results) == 0
    
    @pytest.mark.asyncio
    async def test_process_single_source_exception(self, merger):
        """Test single source processing with exception."""
        source_url = "https://example.com/config.txt"
        
        # Mock the health checker to raise exception
        with patch('vpn_merger.core.merger.UnifiedSourceValidator') as mock_hc_class:
            mock_hc = Mock()
            mock_hc.validate_source.side_effect = Exception("Health check failed")
            mock_hc_class.return_value.__aenter__.return_value = mock_hc
            
            await merger._process_single_source(source_url)
            
            assert merger.stats['processed_sources'] == 1
            assert merger.stats['total_configs'] == 0
            assert len(merger.results) == 0
    
    def test_get_protocol_distribution(self, merger):
        """Test protocol distribution calculation."""
        # Create test results
        merger.results = [
            VPNConfiguration("vmess://config1", "vmess"),
            VPNConfiguration("vless://config2", "vless"),
            VPNConfiguration("vmess://config3", "vmess"),
            VPNConfiguration("trojan://config4", "trojan")
        ]
        
        distribution = merger._get_protocol_distribution(merger.results)
        
        assert distribution["vmess"] == 2
        assert distribution["vless"] == 1
        assert distribution["trojan"] == 1
    
    def test_get_quality_distribution(self, merger):
        """Test quality distribution calculation."""
        # Create test results with different quality scores
        merger.results = [
            VPNConfiguration("config1", "vmess", quality_score=0.95),  # excellent
            VPNConfiguration("config2", "vless", quality_score=0.85),  # good
            VPNConfiguration("config3", "trojan", quality_score=0.65), # fair
            VPNConfiguration("config4", "shadowsocks", quality_score=0.35)  # poor
        ]
        
        distribution = merger._get_quality_distribution(merger.results)
        
        assert distribution["excellent"] == 1
        assert distribution["good"] == 1
        assert distribution["fair"] == 1
        assert distribution["poor"] == 1
    
    def test_save_results(self, merger):
        """Test saving results to files."""
        # Create test results
        merger.results = [
            VPNConfiguration("vmess://config1", "vmess", quality_score=0.9),
            VPNConfiguration("vless://config2", "vless", quality_score=0.8)
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_files = merger.save_results(merger.results, temp_dir)
            
            # Check that output files were created
            assert 'raw' in output_files
            assert 'base64' in output_files
            assert 'csv' in output_files
            assert 'json' in output_files
            assert 'singbox' in output_files
            
            # Check that files exist
            for file_type, file_path in output_files.items():
                assert os.path.exists(file_path)
                assert os.path.getsize(file_path) > 0
    
    def test_save_results_error_handling(self, merger):
        """Test error handling during result saving."""
        # Create test results
        merger.results = [
            VPNConfiguration("vmess://config1", "vmess", quality_score=0.9)
        ]
        
        # Try to save to non-existent directory (should fail gracefully)
        with patch('os.makedirs', side_effect=PermissionError("Permission denied")):
            output_files = merger.save_results(merger.results, "/invalid/path")
            
            # Should return empty dict on error
            assert output_files == {}
    
    def test_parse_config_string(self, merger):
        """Test configuration string parsing."""
        # Test VMess config
        vmess_config = "vmess://uuid@host:port?security=tls&type=ws"
        parts = merger._parse_config_string(vmess_config)
        
        assert parts.get('host') == 'host'
        assert parts.get('port') == 'port'
        assert parts.get('uuid') == 'uuid'
        assert parts.get('security') == 'tls'
        assert parts.get('type') == 'ws'
        
        # Test VLESS config
        vless_config = "vless://uuid@host:port?security=tls#remark"
        parts = merger._parse_config_string(vless_config)
        
        assert parts.get('host') == 'host'
        assert parts.get('port') == 'port'
        assert parts.get('uuid') == 'uuid'
        assert parts.get('security') == 'tls'
    
    def test_convert_to_singbox_outbound(self, merger):
        """Test conversion to sing-box outbound format."""
        # Test VMess config
        vmess_result = VPNConfiguration(
            config="vmess://uuid@host:port?security=tls",
            protocol="vmess"
        )
        
        outbound = merger._convert_to_singbox_outbound(vmess_result, 0)
        
        assert outbound is not None
        assert outbound["type"] == "vmess"
        assert outbound["tag"] == "outbound-0"
        assert outbound["server"] == "host"
        assert outbound["port"] == "port"
        assert outbound["uuid"] == "uuid"
        assert outbound["security"] == "tls"
        
        # Test VLESS config
        vless_result = VPNConfiguration(
            config="vless://uuid@host:port?security=tls",
            protocol="vless"
        )
        
        outbound = merger._convert_to_singbox_outbound(vless_result, 1)
        
        assert outbound is not None
        assert outbound["type"] == "vless"
        assert outbound["tag"] == "outbound-1"
        assert outbound["server"] == "host"
        assert outbound["port"] == "port"
        assert outbound["uuid"] == "uuid"
        assert outbound["security"] == "tls"
    
    def test_convert_to_singbox_outbound_error(self, merger):
        """Test sing-box conversion error handling."""
        # Test with invalid config that will cause parsing error
        invalid_result = VPNConfiguration(
            config="invalid://config",
            protocol="invalid"
        )
        
        outbound = merger._convert_to_singbox_outbound(invalid_result, 0)
        
        # Should return None on error
        assert outbound is None
