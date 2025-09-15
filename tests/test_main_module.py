"""
Comprehensive tests for main module (__main__.py)
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from streamline_vpn.__main__ import cli, main, cli_main


class TestMainModule:
    """Test main module functionality"""
    
    @pytest.mark.asyncio
    async def test_main_success(self):
        """Test successful main execution"""
        with patch('streamline_vpn.__main__.setup_logging') as mock_setup, \
             patch('streamline_vpn.__main__.get_settings') as mock_settings, \
             patch('streamline_vpn.__main__.StreamlineVPNMerger') as MockMerger:
            
            # Setup mocks
            mock_merger = AsyncMock()
            mock_merger.initialize = AsyncMock()
            mock_merger.process_all = AsyncMock(return_value={"success": True})
            MockMerger.return_value = mock_merger
            
            # Test main function
            result = await main("test.yaml", "output", ["json"])
            
            assert result == 0
            mock_setup.assert_called_once()
            mock_settings.assert_called_once()
            mock_merger.initialize.assert_called_once()
            mock_merger.process_all.assert_called_once_with(output_dir="output", formats=["json"])
    
    @pytest.mark.asyncio
    async def test_main_keyboard_interrupt(self):
        """Test main with keyboard interrupt"""
        with patch('streamline_vpn.__main__.setup_logging') as mock_setup, \
             patch('streamline_vpn.__main__.get_settings') as mock_settings, \
             patch('streamline_vpn.__main__.StreamlineVPNMerger') as MockMerger:
            
            # Setup mocks
            mock_merger = AsyncMock()
            mock_merger.initialize = AsyncMock(side_effect=KeyboardInterrupt())
            MockMerger.return_value = mock_merger
            
            # Test main function
            result = await main("test.yaml", "output", ["json"])
            
            assert result == 1
    
    @pytest.mark.asyncio
    async def test_main_exception(self):
        """Test main with exception"""
        with patch('streamline_vpn.__main__.setup_logging') as mock_setup, \
             patch('streamline_vpn.__main__.get_settings') as mock_settings, \
             patch('streamline_vpn.__main__.StreamlineVPNMerger') as MockMerger:
            
            # Setup mocks
            mock_merger = AsyncMock()
            mock_merger.initialize = AsyncMock(side_effect=Exception("Test error"))
            MockMerger.return_value = mock_merger
            
            # Test main function
            result = await main("test.yaml", "output", ["json"])
            
            assert result == 1
    
    @pytest.mark.asyncio
    async def test_main_with_none_formats(self):
        """Test main with None formats"""
        with patch('streamline_vpn.__main__.setup_logging') as mock_setup, \
             patch('streamline_vpn.__main__.get_settings') as mock_settings, \
             patch('streamline_vpn.__main__.StreamlineVPNMerger') as MockMerger:
            
            # Setup mocks
            mock_merger = AsyncMock()
            mock_merger.initialize = AsyncMock()
            mock_merger.process_all = AsyncMock(return_value={"success": True})
            MockMerger.return_value = mock_merger
            
            # Test main function
            result = await main("test.yaml", "output", None)
            
            assert result == 0
            mock_merger.process_all.assert_called_once_with(output_dir="output", formats=None)
    
    @pytest.mark.asyncio
    async def test_main_with_empty_formats(self):
        """Test main with empty formats"""
        with patch('streamline_vpn.__main__.setup_logging') as mock_setup, \
             patch('streamline_vpn.__main__.get_settings') as mock_settings, \
             patch('streamline_vpn.__main__.StreamlineVPNMerger') as MockMerger:
            
            # Setup mocks
            mock_merger = AsyncMock()
            mock_merger.initialize = AsyncMock()
            mock_merger.process_all = AsyncMock(return_value={"success": True})
            MockMerger.return_value = mock_merger
            
            # Test main function
            result = await main("test.yaml", "output", [])
            
            assert result == 0
            mock_merger.process_all.assert_called_once_with(output_dir="output", formats=[])
    
    @pytest.mark.asyncio
    async def test_main_with_multiple_formats(self):
        """Test main with multiple formats"""
        with patch('streamline_vpn.__main__.setup_logging') as mock_setup, \
             patch('streamline_vpn.__main__.get_settings') as mock_settings, \
             patch('streamline_vpn.__main__.StreamlineVPNMerger') as MockMerger:
            
            # Setup mocks
            mock_merger = AsyncMock()
            mock_merger.initialize = AsyncMock()
            mock_merger.process_all = AsyncMock(return_value={"success": True})
            MockMerger.return_value = mock_merger
            
            # Test main function
            result = await main("test.yaml", "output", ["json", "clash", "singbox"])
            
            assert result == 0
            mock_merger.process_all.assert_called_once_with(output_dir="output", formats=["json", "clash", "singbox"])
    
    def test_cli_function(self):
        """Test CLI function"""
        # Test with valid parameters - use click testing
        from click.testing import CliRunner
        runner = CliRunner()
        result = runner.invoke(cli, ["--config", "test.yaml", "--output", "output", "--format", "json", "--format", "clash"])
        assert result.exit_code == 0
    
    def test_cli_main_success(self):
        """Test cli_main function success"""
        with patch('streamline_vpn.__main__.cli.main', return_value=0) as mock_cli:
            result = cli_main()
            assert result == 0
            mock_cli.assert_called_once_with(standalone_mode=False)
    
    def test_cli_main_system_exit(self):
        """Test cli_main with SystemExit"""
        with patch('streamline_vpn.__main__.cli.main', side_effect=SystemExit(1)) as mock_cli:
            result = cli_main()
            assert result == 1
    
    def test_cli_main_keyboard_interrupt(self):
        """Test cli_main with KeyboardInterrupt"""
        with patch('streamline_vpn.__main__.cli.main', side_effect=KeyboardInterrupt()) as mock_cli:
            result = cli_main()
            assert result == 1
    
    def test_cli_main_exception(self):
        """Test cli_main with exception"""
        with patch('streamline_vpn.__main__.cli.main', side_effect=Exception("Test error")) as mock_cli:
            result = cli_main()
            assert result == 1
    
    def test_cli_main_invalid_exit_code(self):
        """Test cli_main with invalid exit code"""
        with patch('streamline_vpn.__main__.cli.main', return_value="invalid") as mock_cli:
            result = cli_main()
            assert result == 0
    
    def test_cli_main_system_exit_no_code(self):
        """Test cli_main with SystemExit without code"""
        with patch('streamline_vpn.__main__.cli.main', side_effect=SystemExit(1)) as mock_cli:
            result = cli_main()
            assert result == 1
