"""
Comprehensive tests for CLI module
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path
from click.testing import CliRunner

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from streamline_vpn.cli import StreamlineVPNCLI, main


class TestStreamlineVPNCLI:
    """Test StreamlineVPNCLI class"""
    
    def test_initialization(self):
        """Test CLI initialization"""
        main_instance = StreamlineVPNCLI()
        assert main_instance.config_path is None
        assert main_instance.output_dir is None
        assert main_instance.verbose is False
        assert main_instance.dry_run is False
    
    def test_setup_logging(self):
        """Test logging setup"""
        main_instance = StreamlineVPNCLI()
        with patch('streamline_vpn.main.setup_logging') as mock_setup:
            main_instance.setup_logging(verbose=True)
            mock_setup.assert_called_once_with(level="DEBUG", format_type="console")
    
    def test_setup_logging_default(self):
        """Test logging setup with default parameters"""
        main_instance = StreamlineVPNCLI()
        with patch('streamline_vpn.main.setup_logging') as mock_setup:
            main_instance.setup_logging()
            mock_setup.assert_called_once_with(level="INFO", format_type="console")
    
    @pytest.mark.asyncio
    async def test_process_configurations_success(self):
        """Test successful configuration processing"""
        main_instance = StreamlineVPNCLI()
        main_instance.config_path = Path("test.yaml")
        main_instance.output_dir = Path("output")
        
        with patch('streamline_vpn.main.StreamlineVPNMerger') as MockMerger:
            mock_merger = AsyncMock()
            mock_merger.initialize = AsyncMock()
            mock_merger.process_all = AsyncMock(return_value={"success": True})
            MockMerger.return_value = mock_merger
            
            result = await main_instance.process_configurations()
            
            assert result == 0
            mock_merger.initialize.assert_called_once()
            mock_merger.process_all.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_configurations_failure(self):
        """Test configuration processing failure"""
        main_instance = StreamlineVPNCLI()
        main_instance.config_path = Path("test.yaml")
        main_instance.output_dir = Path("output")
        
        with patch('streamline_vpn.main.StreamlineVPNMerger') as MockMerger:
            mock_merger = AsyncMock()
            mock_merger.initialize = AsyncMock(side_effect=Exception("Test error"))
            MockMerger.return_value = mock_merger
            
            result = await main_instance.process_configurations()
            
            assert result == 1
    
    @pytest.mark.asyncio
    async def test_validate_configuration_success(self):
        """Test successful configuration validation"""
        main_instance = StreamlineVPNCLI()
        main_instance.config_path = Path("test.yaml")
        
        with patch('streamline_vpn.main.StreamlineVPNMerger') as MockMerger:
            mock_merger = AsyncMock()
            mock_merger.initialize = AsyncMock()
            mock_merger.validate_configuration = AsyncMock(return_value=True)
            MockMerger.return_value = mock_merger
            
            result = await main_instance.validate_configuration()
            
            assert result == 0
            mock_merger.initialize.assert_called_once()
            mock_merger.validate_configuration.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_configuration_failure(self):
        """Test configuration validation failure"""
        main_instance = StreamlineVPNCLI()
        main_instance.config_path = Path("test.yaml")
        
        with patch('streamline_vpn.main.StreamlineVPNMerger') as MockMerger:
            mock_merger = AsyncMock()
            mock_merger.initialize = AsyncMock()
            mock_merger.validate_configuration = AsyncMock(return_value=False)
            MockMerger.return_value = mock_merger
            
            result = await main_instance.validate_configuration()
            
            assert result == 1
    
    @pytest.mark.asyncio
    async def test_validate_configuration_exception(self):
        """Test configuration validation with exception"""
        main_instance = StreamlineVPNCLI()
        main_instance.config_path = Path("test.yaml")
        
        with patch('streamline_vpn.main.StreamlineVPNMerger') as MockMerger:
            mock_merger = AsyncMock()
            mock_merger.initialize = AsyncMock(side_effect=Exception("Test error"))
            MockMerger.return_value = mock_merger
            
            result = await main_instance.validate_configuration()
            
            assert result == 1
    
    @pytest.mark.asyncio
    async def test_start_server_api(self):
        """Test starting API server"""
        main_instance = StreamlineVPNCLI()
        main_instance.config_path = Path("test.yaml")
        
        with patch('streamline_vpn.main.StreamlineVPNMerger') as MockMerger, \
             patch('streamline_vpn.main.uvicorn.run') as mock_run:
            
            mock_merger = AsyncMock()
            mock_merger.initialize = AsyncMock()
            MockMerger.return_value = mock_merger
            
            result = await main_instance.start_server("api")
            
            assert result == 0
            mock_run.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_server_web(self):
        """Test starting web server"""
        main_instance = StreamlineVPNCLI()
        main_instance.config_path = Path("test.yaml")
        
        with patch('streamline_vpn.main.StreamlineVPNMerger') as MockMerger, \
             patch('streamline_vpn.main.uvicorn.run') as mock_run:
            
            mock_merger = AsyncMock()
            mock_merger.initialize = AsyncMock()
            MockMerger.return_value = mock_merger
            
            result = await main_instance.start_server("web")
            
            assert result == 0
            mock_run.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_server_invalid(self):
        """Test starting invalid server type"""
        main_instance = StreamlineVPNCLI()
        
        result = await main_instance.start_server("invalid")
        
        assert result == 1
    
    @pytest.mark.asyncio
    async def test_start_server_exception(self):
        """Test starting server with exception"""
        main_instance = StreamlineVPNCLI()
        main_instance.config_path = Path("test.yaml")
        
        with patch('streamline_vpn.main.StreamlineVPNMerger') as MockMerger:
            mock_merger = AsyncMock()
            mock_merger.initialize = AsyncMock(side_effect=Exception("Test error"))
            MockMerger.return_value = mock_merger
            
            result = await main_instance.start_server("api")
            
            assert result == 1
    
    @pytest.mark.asyncio
    async def test_list_sources(self):
        """Test listing sources"""
        main_instance = StreamlineVPNCLI()
        main_instance.config_path = Path("test.yaml")
        
        with patch('streamline_vpn.main.StreamlineVPNMerger') as MockMerger:
            mock_merger = AsyncMock()
            mock_merger.initialize = AsyncMock()
            mock_merger.list_sources = AsyncMock(return_value=["source1", "source2"])
            MockMerger.return_value = mock_merger
            
            result = await main_instance.list_sources()
            
            assert result == 0
            mock_merger.initialize.assert_called_once()
            mock_merger.list_sources.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_list_sources_exception(self):
        """Test listing sources with exception"""
        main_instance = StreamlineVPNCLI()
        main_instance.config_path = Path("test.yaml")
        
        with patch('streamline_vpn.main.StreamlineVPNMerger') as MockMerger:
            mock_merger = AsyncMock()
            mock_merger.initialize = AsyncMock(side_effect=Exception("Test error"))
            MockMerger.return_value = mock_merger
            
            result = await main_instance.list_sources()
            
            assert result == 1
    
    @pytest.mark.asyncio
    async def test_add_source(self):
        """Test adding source"""
        main_instance = StreamlineVPNCLI()
        main_instance.config_path = Path("test.yaml")
        
        with patch('streamline_vpn.main.StreamlineVPNMerger') as MockMerger:
            mock_merger = AsyncMock()
            mock_merger.initialize = AsyncMock()
            mock_merger.add_source = AsyncMock(return_value=True)
            MockMerger.return_value = mock_merger
            
            result = await main_instance.add_source("https://example.com/sources.txt")
            
            assert result == 0
            mock_merger.initialize.assert_called_once()
            mock_merger.add_source.assert_called_once_with("https://example.com/sources.txt")
    
    @pytest.mark.asyncio
    async def test_add_source_failure(self):
        """Test adding source failure"""
        main_instance = StreamlineVPNCLI()
        main_instance.config_path = Path("test.yaml")
        
        with patch('streamline_vpn.main.StreamlineVPNMerger') as MockMerger:
            mock_merger = AsyncMock()
            mock_merger.initialize = AsyncMock()
            mock_merger.add_source = AsyncMock(return_value=False)
            MockMerger.return_value = mock_merger
            
            result = await main_instance.add_source("https://example.com/sources.txt")
            
            assert result == 1
    
    @pytest.mark.asyncio
    async def test_add_source_exception(self):
        """Test adding source with exception"""
        main_instance = StreamlineVPNCLI()
        main_instance.config_path = Path("test.yaml")
        
        with patch('streamline_vpn.main.StreamlineVPNMerger') as MockMerger:
            mock_merger = AsyncMock()
            mock_merger.initialize = AsyncMock(side_effect=Exception("Test error"))
            MockMerger.return_value = mock_merger
            
            result = await main_instance.add_source("https://example.com/sources.txt")
            
            assert result == 1
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check"""
        main_instance = StreamlineVPNCLI()
        main_instance.config_path = Path("test.yaml")
        
        with patch('streamline_vpn.main.StreamlineVPNMerger') as MockMerger:
            mock_merger = AsyncMock()
            mock_merger.initialize = AsyncMock()
            mock_merger.health_check = AsyncMock(return_value={"status": "healthy"})
            MockMerger.return_value = mock_merger
            
            result = await main_instance.health_check()
            
            assert result == 0
            mock_merger.initialize.assert_called_once()
            mock_merger.health_check.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self):
        """Test health check with unhealthy status"""
        main_instance = StreamlineVPNCLI()
        main_instance.config_path = Path("test.yaml")
        
        with patch('streamline_vpn.main.StreamlineVPNMerger') as MockMerger:
            mock_merger = AsyncMock()
            mock_merger.initialize = AsyncMock()
            mock_merger.health_check = AsyncMock(return_value={"status": "unhealthy"})
            MockMerger.return_value = mock_merger
            
            result = await main_instance.health_check()
            
            assert result == 1
    
    @pytest.mark.asyncio
    async def test_health_check_exception(self):
        """Test health check with exception"""
        main_instance = StreamlineVPNCLI()
        main_instance.config_path = Path("test.yaml")
        
        with patch('streamline_vpn.main.StreamlineVPNMerger') as MockMerger:
            mock_merger = AsyncMock()
            mock_merger.initialize = AsyncMock(side_effect=Exception("Test error"))
            MockMerger.return_value = mock_merger
            
            result = await main_instance.health_check()
            
            assert result == 1


class TestCLICommands:
    """Test CLI commands"""
    
    def test_main_help(self):
        """Test CLI help command"""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "StreamlineVPN CLI" in result.output
    
    def test_process_command_help(self):
        """Test process command help"""
        runner = CliRunner()
        result = runner.invoke(main, ["process", "--help"])
        assert result.exit_code == 0
        assert "Process VPN configurations" in result.output
    
    def test_validate_command_help(self):
        """Test validate command help"""
        runner = CliRunner()
        result = runner.invoke(main, ["validate", "--help"])
        assert result.exit_code == 0
        assert "Validate configuration" in result.output
    
    def test_server_command_help(self):
        """Test server command help"""
        runner = CliRunner()
        result = runner.invoke(main, ["server", "--help"])
        assert result.exit_code == 0
        assert "Start server" in result.output
    
    def test_sources_command_help(self):
        """Test sources command help"""
        runner = CliRunner()
        result = runner.invoke(main, ["sources", "--help"])
        assert result.exit_code == 0
        assert "Manage sources" in result.output
    
    def test_health_command_help(self):
        """Test health command help"""
        runner = CliRunner()
        result = runner.invoke(main, ["health", "--help"])
        assert result.exit_code == 0
        assert "Health check" in result.output
    
    def test_version_command(self):
        """Test version command"""
        runner = CliRunner()
        result = runner.invoke(main, ["version"])
        assert result.exit_code == 0
        assert "StreamlineVPN" in result.output
