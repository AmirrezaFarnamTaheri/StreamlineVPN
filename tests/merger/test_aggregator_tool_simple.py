"""Simplified tests for merger aggregator_tool module."""

import argparse
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from streamline_vpn.merger.aggregator_tool import (
    setup_logging,
    build_parser,
    main
)


class TestSetupLoggingSimple:
    """Simplified test cases for setup_logging function."""

    def test_setup_logging_basic(self):
        """Test basic setup_logging functionality."""
        mock_log_dir = MagicMock(spec=Path)
        mock_log_file = MagicMock(spec=Path)
        mock_log_dir.__truediv__.return_value = mock_log_file
        
        with patch('streamline_vpn.merger.aggregator_tool.datetime') as mock_datetime:
            with patch('streamline_vpn.merger.aggregator_tool.logging.basicConfig') as mock_basic_config:
                with patch('streamline_vpn.merger.aggregator_tool.logging.StreamHandler') as mock_stream_handler:
                    with patch('streamline_vpn.merger.aggregator_tool.logging.FileHandler') as mock_file_handler:
                        mock_datetime.utcnow.return_value.date.return_value = "2023-01-01"
                        
                        setup_logging(mock_log_dir)
                        
                        mock_log_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)
                        mock_basic_config.assert_called_once()


class TestBuildParserSimple:
    """Simplified test cases for build_parser function."""

    def test_build_parser_creates_parser(self):
        """Test that build_parser creates ArgumentParser."""
        parser = build_parser()
        
        assert isinstance(parser, argparse.ArgumentParser)
        assert parser.description is not None

    def test_build_parser_uses_existing_parser(self):
        """Test that build_parser uses existing ArgumentParser when provided."""
        existing_parser = argparse.ArgumentParser()
        result_parser = build_parser(existing_parser)
        
        assert result_parser is existing_parser

    def test_build_parser_has_key_arguments(self):
        """Test that build_parser has key arguments."""
        parser = build_parser()
        
        # Test parsing some key arguments
        args = parser.parse_args(['--bot'])
        assert args.bot is True
        
        args = parser.parse_args(['--hours', '48'])
        assert args.hours == 48
        
        args = parser.parse_args(['--protocols', 'vmess,vless'])
        assert args.protocols == 'vmess,vless'


class TestMainSimple:
    """Simplified test cases for main function."""

    def test_main_prints_warning(self):
        """Test that main prints public source warning."""
        mock_args = MagicMock()
        mock_args.config = "config.yaml"
        mock_args.bot = False
        mock_args.with_merger = False
        mock_args.upload_gist = False
        mock_args.protocols = None
        mock_args.output_dir = None
        mock_args.concurrent_limit = None
        mock_args.request_timeout = None
        mock_args.no_base64 = False
        mock_args.no_singbox = False
        mock_args.no_clash = False
        mock_args.write_html = False
        mock_args.output_surge = None
        mock_args.output_qx = None
        mock_args.output_xyz = None
        mock_args.include_pattern = None
        mock_args.exclude_pattern = None
        mock_args.shuffle_sources = False
        mock_args.hours = 24
        mock_args.failure_threshold = 3
        mock_args.no_prune = False
        mock_args.sources = "sources.txt"
        mock_args.channels = "channels.txt"
        
        mock_config = MagicMock()
        mock_config.output_dir = "/test/output"
        mock_config.log_dir = "/test/logs"
        mock_config.include_patterns = []
        mock_config.exclude_patterns = []
        
        with patch('streamline_vpn.merger.aggregator_tool.print_public_source_warning') as mock_warning:
            with patch('streamline_vpn.merger.aggregator_tool.load_config', return_value=mock_config):
                with patch('streamline_vpn.merger.aggregator_tool.setup_logging'):
                    with patch('streamline_vpn.merger.aggregator_tool.asyncio.run', return_value=(MagicMock(), [])):
                        with patch('streamline_vpn.merger.aggregator_tool.Path'):
                            with patch('builtins.print'):
                                main(mock_args)
                                
                                mock_warning.assert_called_once()

    def test_main_handles_config_not_found(self):
        """Test that main handles config file not found."""
        mock_args = MagicMock()
        mock_args.config = "config.yaml"
        
        with patch('streamline_vpn.merger.aggregator_tool.print_public_source_warning'):
            with patch('streamline_vpn.merger.aggregator_tool.load_config', side_effect=ValueError("Config not found")):
                with patch('builtins.print') as mock_print:
                    with patch('sys.exit') as mock_exit:
                        # The function should exit, so we expect SystemExit or the mock to be called
                        try:
                            main(mock_args)
                        except SystemExit:
                            pass  # Expected when sys.exit is called
                        
                        mock_print.assert_called_with("Config file not found. Copy config.yaml.example to config.yaml.")
                        mock_exit.assert_called_once_with(1)

    def test_main_parses_args_when_none_provided(self):
        """Test that main parses arguments when none provided."""
        mock_config = MagicMock()
        mock_config.output_dir = "/test/output"
        mock_config.log_dir = "/test/logs"
        mock_config.include_patterns = []
        mock_config.exclude_patterns = []
        
        with patch('streamline_vpn.merger.aggregator_tool.build_parser') as mock_build_parser:
            with patch('streamline_vpn.merger.aggregator_tool.print_public_source_warning'):
                with patch('streamline_vpn.merger.aggregator_tool.load_config', return_value=mock_config):
                    with patch('streamline_vpn.merger.aggregator_tool.setup_logging'):
                        with patch('streamline_vpn.merger.aggregator_tool.asyncio.run', return_value=(MagicMock(), [])):
                            with patch('streamline_vpn.merger.aggregator_tool.Path'):
                                with patch('builtins.print'):
                                    mock_parser = MagicMock()
                                    mock_args = MagicMock()
                                    mock_args.config = "config.yaml"
                                    mock_args.bot = False
                                    mock_args.with_merger = False
                                    mock_args.upload_gist = False
                                    mock_args.protocols = None
                                    mock_args.output_dir = None
                                    mock_args.concurrent_limit = None
                                    mock_args.request_timeout = None
                                    mock_args.no_base64 = False
                                    mock_args.no_singbox = False
                                    mock_args.no_clash = False
                                    mock_args.write_html = False
                                    mock_args.output_surge = None
                                    mock_args.output_qx = None
                                    mock_args.output_xyz = None
                                    mock_args.include_pattern = None
                                    mock_args.exclude_pattern = None
                                    mock_args.shuffle_sources = False
                                    mock_args.hours = 24
                                    mock_args.failure_threshold = 3
                                    mock_args.no_prune = False
                                    mock_args.sources = "sources.txt"
                                    mock_args.channels = "channels.txt"
                                    mock_parser.parse_args.return_value = mock_args
                                    mock_build_parser.return_value = mock_parser
                                    
                                    main(None)
                                    
                                    mock_build_parser.assert_called_once()
                                    mock_parser.parse_args.assert_called_once()

    def test_main_overrides_config_basic(self):
        """Test that main overrides config with basic command line arguments."""
        mock_args = MagicMock()
        mock_args.config = "config.yaml"
        mock_args.bot = False
        mock_args.with_merger = False
        mock_args.upload_gist = False
        mock_args.protocols = None
        mock_args.output_dir = "/custom/output"
        mock_args.concurrent_limit = 20
        mock_args.request_timeout = 60
        mock_args.no_base64 = True
        mock_args.no_singbox = False
        mock_args.no_clash = False
        mock_args.write_html = False
        mock_args.output_surge = None
        mock_args.output_qx = None
        mock_args.output_xyz = None
        mock_args.include_pattern = None
        mock_args.exclude_pattern = None
        mock_args.shuffle_sources = False
        mock_args.hours = 24
        mock_args.failure_threshold = 3
        mock_args.no_prune = False
        mock_args.sources = "sources.txt"
        mock_args.channels = "channels.txt"
        
        mock_config = MagicMock()
        mock_config.output_dir = "/test/output"
        mock_config.log_dir = "/test/logs"
        mock_config.concurrent_limit = 10
        mock_config.request_timeout = 30
        mock_config.write_base64 = True
        mock_config.include_patterns = []
        mock_config.exclude_patterns = []
        
        with patch('streamline_vpn.merger.aggregator_tool.print_public_source_warning'):
            with patch('streamline_vpn.merger.aggregator_tool.load_config', return_value=mock_config):
                with patch('streamline_vpn.merger.aggregator_tool.setup_logging'):
                    with patch('streamline_vpn.merger.aggregator_tool.asyncio.run', return_value=(MagicMock(), [])):
                        with patch('streamline_vpn.merger.aggregator_tool.Path') as mock_path:
                            with patch('builtins.print'):
                                # Mock Path operations
                                mock_output_path = MagicMock()
                                mock_log_path = MagicMock()
                                mock_output_path.expanduser.return_value.resolve.return_value = mock_output_path
                                mock_log_path.expanduser.return_value.resolve.return_value = mock_log_path
                                mock_path.side_effect = [mock_output_path, mock_log_path, MagicMock(), MagicMock()]
                                
                                main(mock_args)
                                
                                # Verify config was overridden
                                assert mock_config.output_dir == str(mock_output_path)
                                assert mock_config.concurrent_limit == 20
                                assert mock_config.request_timeout == 60
                                assert mock_config.write_base64 is False

    def test_main_runs_bot_mode(self):
        """Test that main runs telegram bot mode when --bot flag is set."""
        mock_args = MagicMock()
        mock_args.config = "config.yaml"
        mock_args.bot = True
        mock_args.sources = "sources.txt"
        mock_args.channels = "channels.txt"
        mock_args.hours = 24
        mock_args.output_dir = None
        mock_args.concurrent_limit = None
        mock_args.request_timeout = None
        mock_args.no_base64 = False
        mock_args.no_singbox = False
        mock_args.no_clash = False
        mock_args.write_html = False
        mock_args.output_surge = None
        mock_args.output_qx = None
        mock_args.output_xyz = None
        mock_args.include_pattern = None
        mock_args.exclude_pattern = None
        mock_args.shuffle_sources = False
        
        mock_config = MagicMock()
        mock_config.output_dir = "/test/output"
        mock_config.log_dir = "/test/logs"
        mock_config.include_patterns = []
        mock_config.exclude_patterns = []
        
        with patch('streamline_vpn.merger.aggregator_tool.print_public_source_warning'):
            with patch('streamline_vpn.merger.aggregator_tool.load_config', return_value=mock_config):
                with patch('streamline_vpn.merger.aggregator_tool.setup_logging'):
                    with patch('streamline_vpn.merger.aggregator_tool.asyncio.run') as mock_asyncio_run:
                        with patch('streamline_vpn.merger.aggregator_tool.telegram_bot_mode') as mock_bot_mode:
                            with patch('streamline_vpn.merger.aggregator_tool.Path') as mock_path:
                                # Mock Path operations
                                mock_output_path = MagicMock()
                                mock_log_path = MagicMock()
                                mock_output_path.expanduser.return_value.resolve.return_value = mock_output_path
                                mock_log_path.expanduser.return_value.resolve.return_value = mock_log_path
                                mock_path.side_effect = [mock_output_path, mock_log_path, MagicMock(), MagicMock()]
                                
                                main(mock_args)
                                
                                # Verify bot mode was called
                                mock_asyncio_run.assert_called_once()

    def test_main_runs_pipeline_mode(self):
        """Test that main runs pipeline mode when --bot flag is not set."""
        mock_args = MagicMock()
        mock_args.config = "config.yaml"
        mock_args.bot = False
        mock_args.with_merger = False
        mock_args.upload_gist = False
        mock_args.protocols = "vmess,vless"
        mock_args.sources = "sources.txt"
        mock_args.channels = "channels.txt"
        mock_args.hours = 24
        mock_args.failure_threshold = 3
        mock_args.no_prune = False
        mock_args.output_dir = None
        mock_args.concurrent_limit = None
        mock_args.request_timeout = None
        mock_args.no_base64 = False
        mock_args.no_singbox = False
        mock_args.no_clash = False
        mock_args.write_html = False
        mock_args.output_surge = None
        mock_args.output_qx = None
        mock_args.output_xyz = None
        mock_args.include_pattern = None
        mock_args.exclude_pattern = None
        mock_args.shuffle_sources = False
        
        mock_config = MagicMock()
        mock_config.output_dir = "/test/output"
        mock_config.log_dir = "/test/logs"
        mock_config.include_patterns = []
        mock_config.exclude_patterns = []
        
        with patch('streamline_vpn.merger.aggregator_tool.print_public_source_warning'):
            with patch('streamline_vpn.merger.aggregator_tool.load_config', return_value=mock_config):
                with patch('streamline_vpn.merger.aggregator_tool.setup_logging'):
                    with patch('streamline_vpn.merger.aggregator_tool.asyncio.run') as mock_asyncio_run:
                        with patch('streamline_vpn.merger.aggregator_tool.run_pipeline') as mock_run_pipeline:
                            with patch('streamline_vpn.merger.aggregator_tool.Path') as mock_path:
                                with patch('builtins.print') as mock_print:
                                    # Mock Path operations
                                    mock_output_path = MagicMock()
                                    mock_log_path = MagicMock()
                                    mock_out_dir = MagicMock()
                                    mock_output_path.expanduser.return_value.resolve.return_value = mock_output_path
                                    mock_log_path.expanduser.return_value.resolve.return_value = mock_log_path
                                    mock_path.side_effect = [mock_output_path, mock_log_path, MagicMock(), MagicMock()]
                                    
                                    # Mock pipeline return
                                    mock_asyncio_run.return_value = (mock_out_dir, [])
                                    
                                    main(mock_args)
                                    
                                    # Verify pipeline was called
                                    mock_asyncio_run.assert_called_once()
                                    mock_print.assert_any_call(f"Aggregation complete. Files written to {mock_out_dir.resolve()}")

    def test_main_upload_gist_no_token(self):
        """Test that main handles missing GitHub token for gist upload."""
        mock_args = MagicMock()
        mock_args.config = "config.yaml"
        mock_args.bot = False
        mock_args.with_merger = False
        mock_args.upload_gist = True
        mock_args.protocols = None
        mock_args.sources = "sources.txt"
        mock_args.channels = "channels.txt"
        mock_args.hours = 24
        mock_args.failure_threshold = 3
        mock_args.no_prune = False
        mock_args.output_dir = None
        mock_args.concurrent_limit = None
        mock_args.request_timeout = None
        mock_args.no_base64 = False
        mock_args.no_singbox = False
        mock_args.no_clash = False
        mock_args.write_html = False
        mock_args.output_surge = None
        mock_args.output_qx = None
        mock_args.output_xyz = None
        mock_args.include_pattern = None
        mock_args.exclude_pattern = None
        mock_args.shuffle_sources = False
        
        mock_config = MagicMock()
        mock_config.output_dir = "/test/output"
        mock_config.log_dir = "/test/logs"
        mock_config.github_token = None
        mock_config.include_patterns = []
        mock_config.exclude_patterns = []
        
        with patch('streamline_vpn.merger.aggregator_tool.print_public_source_warning'):
            with patch('streamline_vpn.merger.aggregator_tool.load_config', return_value=mock_config):
                with patch('streamline_vpn.merger.aggregator_tool.setup_logging'):
                    with patch('streamline_vpn.merger.aggregator_tool.asyncio.run') as mock_asyncio_run:
                        with patch('streamline_vpn.merger.aggregator_tool.Path') as mock_path:
                            with patch('builtins.print') as mock_print:
                                with patch.dict(os.environ, {}, clear=True):
                                    # Mock Path operations
                                    mock_output_path = MagicMock()
                                    mock_log_path = MagicMock()
                                    mock_out_dir = MagicMock()
                                    mock_output_path.expanduser.return_value.resolve.return_value = mock_output_path
                                    mock_log_path.expanduser.return_value.resolve.return_value = mock_log_path
                                    mock_path.side_effect = [mock_output_path, mock_log_path, MagicMock(), MagicMock()]
                                    
                                    # Mock pipeline return
                                    mock_asyncio_run.return_value = (mock_out_dir, [Path("file1.txt")])
                                    
                                    main(mock_args)
                                    
                                    # Verify error message was printed
                                    mock_print.assert_any_call(
                                        "GitHub token not provided. Set github_token in config or GITHUB_TOKEN env var"
                                    )

    def test_main_runs_with_merger(self):
        """Test that main runs vpn_merger when --with-merger flag is set."""
        mock_args = MagicMock()
        mock_args.config = "config.yaml"
        mock_args.bot = False
        mock_args.with_merger = True
        mock_args.upload_gist = False
        mock_args.protocols = None
        mock_args.sources = "sources.txt"
        mock_args.channels = "channels.txt"
        mock_args.hours = 24
        mock_args.failure_threshold = 3
        mock_args.no_prune = False
        mock_args.output_dir = None
        mock_args.concurrent_limit = None
        mock_args.request_timeout = None
        mock_args.no_base64 = False
        mock_args.no_singbox = False
        mock_args.no_clash = False
        mock_args.write_html = False
        mock_args.output_surge = None
        mock_args.output_qx = None
        mock_args.output_xyz = None
        mock_args.include_pattern = None
        mock_args.exclude_pattern = None
        mock_args.shuffle_sources = False
        
        mock_config = MagicMock()
        mock_config.output_dir = "/test/output"
        mock_config.log_dir = "/test/logs"
        mock_config.write_base64 = True
        mock_config.write_html = False
        mock_config.include_protocols = []
        mock_config.exclude_protocols = []
        mock_config.exclude_patterns = []
        mock_config.concurrent_limit = 10
        mock_config.include_patterns = []
        
        with patch('streamline_vpn.merger.aggregator_tool.print_public_source_warning'):
            with patch('streamline_vpn.merger.aggregator_tool.load_config', return_value=mock_config):
                with patch('streamline_vpn.merger.aggregator_tool.setup_logging'):
                    with patch('streamline_vpn.merger.aggregator_tool.asyncio.run') as mock_asyncio_run:
                        with patch('streamline_vpn.merger.aggregator_tool.vpn_merger') as mock_vpn_merger:
                            with patch('streamline_vpn.merger.aggregator_tool.Path') as mock_path:
                                with patch('streamline_vpn.merger.aggregator_tool.redirect_stdout'):
                                    with patch('builtins.print') as mock_print:
                                        # Mock Path operations
                                        mock_output_path = MagicMock()
                                        mock_log_path = MagicMock()
                                        mock_out_dir = MagicMock()
                                        mock_output_path.expanduser.return_value.resolve.return_value = mock_output_path
                                        mock_log_path.expanduser.return_value.resolve.return_value = mock_log_path
                                        mock_path.side_effect = [mock_output_path, mock_log_path, MagicMock(), MagicMock()]
                                        
                                        # Mock pipeline return
                                        mock_asyncio_run.return_value = (mock_out_dir, [])
                                        
                                        # Mock vpn_merger CONFIG
                                        mock_vpn_merger.CONFIG = MagicMock()
                                        
                                        main(mock_args)
                                        
                                        # Verify vpn_merger was configured and run
                                        mock_vpn_merger.detect_and_run.assert_called_once()
                                        mock_print.assert_any_call("\n===== VPN Merger Summary =====")


class TestMainFunctionExists:
    """Test that main function exists and is callable."""

    def test_main_function_exists(self):
        """Test that main function exists and is callable."""
        from streamline_vpn.merger.aggregator_tool import main
        assert callable(main)
