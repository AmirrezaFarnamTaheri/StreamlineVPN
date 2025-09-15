"""
Tests for CLI functionality
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path
from click.testing import CliRunner

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from streamline_vpn.cli import main


class TestCLIFunctionality:
    """Test CLI functionality"""
    
    def test_cli_help(self):
        """Test CLI help command"""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "StreamlineVPN" in result.output
    
    def test_cli_version(self):
        """Test CLI version command"""
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "StreamlineVPN" in result.output
    
    def test_process_command_help(self):
        """Test process command help"""
        runner = CliRunner()
        result = runner.invoke(main, ["process", "--help"])
        assert result.exit_code == 0
        assert "Process VPN configurations from all sources" in result.output
    
    def test_validate_command_help(self):
        """Test validate command help"""
        runner = CliRunner()
        result = runner.invoke(main, ["validate", "--help"])
        assert result.exit_code == 0
        assert "Validate configuration files and sources" in result.output
    
    def test_server_command_help(self):
        """Test server command help"""
        runner = CliRunner()
        result = runner.invoke(main, ["server", "--help"])
        assert result.exit_code == 0
        assert "Server management commands" in result.output
    
    def test_web_command_help(self):
        """Test web command help"""
        runner = CliRunner()
        result = runner.invoke(main, ["server", "web", "--help"])
        assert result.exit_code == 0
        assert "web" in result.output
    
    def test_sources_command_help(self):
        """Test sources command help"""
        runner = CliRunner()
        result = runner.invoke(main, ["sources", "--help"])
        assert result.exit_code == 0
        assert "Source management commands" in result.output
    
    def test_add_command_help(self):
        """Test add command help"""
        runner = CliRunner()
        result = runner.invoke(main, ["sources", "add", "--help"])
        assert result.exit_code == 0
        assert "add" in result.output
    
    def test_health_command_help(self):
        """Test health command help"""
        runner = CliRunner()
        result = runner.invoke(main, ["health", "--help"])
        assert result.exit_code == 0
        assert "Check system health and status" in result.output
    
    def test_version_command(self):
        """Test version command"""
        runner = CliRunner()
        result = runner.invoke(main, ["version"])
        assert result.exit_code == 0
        assert "StreamlineVPN" in result.output
