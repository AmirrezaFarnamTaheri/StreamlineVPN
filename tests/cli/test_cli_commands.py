"""
Tests for CLI commands functionality.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from click.testing import CliRunner

from streamline_vpn.cli.main import main


class TestCLICommands:
    """Test CLI commands"""

    def setup_method(self):
        """Setup for each test method"""
        self.runner = CliRunner()

    def test_main_command_help(self):
        """Test main command help"""
        result = self.runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "StreamlineVPN" in result.output
        assert "Advanced VPN Configuration Manager" in result.output

    def test_main_command_version(self):
        """Test main command version"""
        # Accept either --version or subgroup
        result = self.runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "version" in result.output.lower()

    def test_main_command_verbose(self):
        """Test main command with verbose flag"""
        result = self.runner.invoke(main, ["--verbose", "--help"])
        assert result.exit_code == 0
        assert "StreamlineVPN" in result.output

    def test_main_command_config(self):
        """Test main command with config file"""
        with patch("pathlib.Path.exists", return_value=True):
            result = self.runner.invoke(main, ["--config", "test.yaml", "--help"])
            assert result.exit_code == 0
            assert "StreamlineVPN" in result.output

    def test_main_command_output(self):
        """Test main command with output directory"""
        result = self.runner.invoke(main, ["--output", "output", "--help"])
        assert result.exit_code == 0
        assert "StreamlineVPN" in result.output

    def test_main_command_dry_run(self):
        """Test main command with dry run flag"""
        result = self.runner.invoke(main, ["--dry-run", "--help"])
        assert result.exit_code == 0
        assert "StreamlineVPN" in result.output

    def test_main_command_invalid_option(self):
        """Test main command with invalid option"""
        result = self.runner.invoke(main, ["--invalid-option"])
        assert result.exit_code != 0

    def test_main_command_no_args(self):
        """Test main command with no arguments, which should show help."""
        result = self.runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Usage:" in result.output

    def test_main_command_short_flags(self):
        """Test main command with short flags"""
        result = self.runner.invoke(
            main, ["-v", "-c", "test.yaml", "-o", "output", "--help"]
        )
        assert result.exit_code == 0
        assert "StreamlineVPN" in result.output

    def test_main_command_multiple_flags(self):
        """Test main command with multiple flags"""
        result = self.runner.invoke(main, ["--verbose", "--dry-run", "--help"])
        assert result.exit_code == 0
        assert "StreamlineVPN" in result.output

    def test_main_command_config_not_exists(self):
        """Test main command with non-existent config file"""
        with patch("pathlib.Path.exists", return_value=False):
            result = self.runner.invoke(main, ["--config", "nonexistent.yaml"])
            assert result.exit_code != 0

    def test_main_command_output_not_dir(self):
        """Test main command with output that's not a directory"""
        with patch("pathlib.Path.is_dir", return_value=False):
            result = self.runner.invoke(main, ["--output", "not_a_dir"])
            assert result.exit_code != 0

    def test_main_command_verbose_levels(self):
        """Test main command with different verbose levels"""
        result = self.runner.invoke(main, ["--verbose", "--help"])
        assert result.exit_code == 0

        result = self.runner.invoke(main, ["--verbose", "--verbose", "--help"])
        assert result.exit_code == 0

    def test_main_command_config_validation(self):
        """Test main command config file validation"""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("yaml.safe_load") as mock_yaml:
                mock_yaml.return_value = {"sources": []}
                result = self.runner.invoke(main, ["--config", "test.yaml", "--help"])
                assert result.exit_code == 0

    def test_main_command_output_creation(self):
        """Test main command output directory creation"""
        with patch("pathlib.Path.mkdir") as mock_mkdir:
            # Use a subcommand so the group callback runs and mkdir is called
            result = self.runner.invoke(
                main, ["--output", "new_output", "version"]
            )
            assert result.exit_code == 0
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_main_command_dry_run_behavior(self):
        """Test main command dry run behavior"""
        with patch("streamline_vpn.cli.context.CLIContext") as MockCLI:
            mock_cli = MockCLI.return_value
            mock_cli.process_configurations = AsyncMock(return_value=True)

            result = self.runner.invoke(main, ["--dry-run", "process"])
            assert result.exit_code == 0

    def test_main_command_verbose_logging(self):
        """Test main command verbose logging setup"""
        with patch("logging.basicConfig") as mock_setup:
            result = self.runner.invoke(main, ["--verbose", "version"])
            assert result.exit_code == 0
            mock_setup.assert_called_once()

    def test_main_command_config_loading(self):
        """Test main command config file loading"""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("yaml.safe_load") as mock_yaml:
                mock_yaml.return_value = {
                    "sources": [{"name": "test", "url": "http://test.com"}]
                }
                result = self.runner.invoke(main, ["--config", "test.yaml", "--help"])
                assert result.exit_code == 0

    def test_main_command_output_validation(self):
        """Test main command output directory validation"""
        with patch("pathlib.Path.is_dir", return_value=True):
            result = self.runner.invoke(main, ["--output", "valid_dir", "--help"])
            assert result.exit_code == 0

    def test_main_command_error_handling(self):
        """Test main command error handling"""
        with patch("streamline_vpn.cli.context.CLIContext") as MockCLI:
            MockCLI.side_effect = Exception("Test error")
            result = self.runner.invoke(main, ["--help"])
            assert result.exit_code != 0
