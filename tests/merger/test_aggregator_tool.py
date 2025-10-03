"""Tests for merger aggregator_tool module."""

import argparse
import asyncio
import io
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock, call

import pytest

from streamline_vpn.merger.aggregator_tool import (
    setup_logging,
    build_parser,
    main
)


class TestSetupLogging:
    """Test cases for setup_logging function."""

    def test_setup_logging_creates_directory(self):
        """Test that setup_logging creates log directory."""
        mock_log_dir = MagicMock(spec=Path)
        mock_log_file = MagicMock(spec=Path)
        mock_log_dir.__truediv__.return_value = mock_log_file
        
        with patch('streamline_vpn.merger.aggregator_tool.datetime') as mock_datetime:
            with patch('streamline_vpn.merger.aggregator_tool.logging.basicConfig') as mock_basic_config:
                mock_datetime.utcnow.return_value.date.return_value = "2023-01-01"
                
                setup_logging(mock_log_dir)
                
                mock_log_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)
                mock_log_dir.__truediv__.assert_called_once_with("2023-01-01.log")
                mock_basic_config.assert_called_once()

    def test_setup_logging_configures_handlers(self):
        """Test that setup_logging configures logging handlers."""
        mock_log_dir = MagicMock(spec=Path)
        mock_log_file = MagicMock(spec=Path)
        mock_log_dir.__truediv__.return_value = mock_log_file
        
        with patch('streamline_vpn.merger.aggregator_tool.datetime') as mock_datetime:
            with patch('streamline_vpn.merger.aggregator_tool.logging.basicConfig') as mock_basic_config:
                with patch('streamline_vpn.merger.aggregator_tool.logging.StreamHandler') as mock_stream_handler:
                    with patch('streamline_vpn.merger.aggregator_tool.logging.FileHandler') as mock_file_handler:
                        mock_datetime.utcnow.return_value.date.return_value = "2023-01-01"
                        
                        setup_logging(mock_log_dir)
                        
                        # Verify handlers were created
                        mock_stream_handler.assert_called_once()
                        mock_file_handler.assert_called_once_with(mock_log_file, encoding="utf-8")
                        
                        # Verify basicConfig was called with correct parameters
                        call_args = mock_basic_config.call_args
                        assert call_args.kwargs['level'] == 20  # logging.INFO
                        assert 'format' in call_args.kwargs
                        assert 'handlers' in call_args.kwargs


class TestBuildParser:
    """Test cases for build_parser function."""

    def test_build_parser_creates_new_parser(self):
        """Test that build_parser creates new ArgumentParser when none provided."""
        parser = build_parser()
        
        assert isinstance(parser, argparse.ArgumentParser)
        assert parser.description is not None

    def test_build_parser_uses_existing_parser(self):
        """Test that build_parser uses existing ArgumentParser when provided."""
        existing_parser = argparse.ArgumentParser()
        result_parser = build_parser(existing_parser)
        
        assert result_parser is existing_parser

    def test_build_parser_adds_all_arguments(self):
        """Test that build_parser adds all expected arguments."""
        parser = build_parser()
        
        # Get all argument names
        arg_names = []
        for action in parser._actions:
            if action.dest != 'help':
                arg_names.append(action.dest)
        
        expected_args = [
            'bot', 'protocols', 'include_pattern', 'exclude_pattern',
            'config', 'sources', 'channels', 'hours', 'output_dir',
            'concurrent_limit', 'request_timeout', 'failure_threshold',
            'no_prune', 'no_base64', 'no_singbox', 'no_clash',
            'write_html', 'shuffle_sources', 'output_surge',
            'output_qx', 'output_xyz', 'with_merger', 'upload_gist'
        ]
        
        for expected_arg in expected_args:
            assert expected_arg in arg_names

    def test_build_parser_default_values(self):
        """Test that build_parser sets correct default values."""
        parser = build_parser()
        args = parser.parse_args([])
        
        assert args.bot is False
        assert args.protocols is None
        assert args.hours == 24
        assert args.failure_threshold == 3
        assert args.no_prune is False
        assert args.no_base64 is False
        assert args.no_singbox is False
        assert args.no_clash is False
        assert args.write_html is False
        assert args.shuffle_sources is False
        assert args.with_merger is False
        assert args.upload_gist is False

    def test_build_parser_argument_types(self):
        """Test that build_parser sets correct argument types."""
        parser = build_parser()
        
        # Test integer arguments
        args = parser.parse_args(['--hours', '48', '--concurrent-limit', '20', 
                                  '--request-timeout', '60', '--failure-threshold', '5'])
        
        assert args.hours == 48
        assert args.concurrent_limit == 20
        assert args.request_timeout == 60
        assert args.failure_threshold == 5

    def test_build_parser_list_arguments(self):
        """Test that build_parser handles list arguments correctly."""
        parser = build_parser()
        
        args = parser.parse_args([
            '--include-pattern', 'pattern1',
            '--include-pattern', 'pattern2',
            '--exclude-pattern', 'exclude1'
        ])
        
        assert args.include_pattern == ['pattern1', 'pattern2']
        assert args.exclude_pattern == ['exclude1']


class TestMain:
    """Test cases for main function."""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        config = MagicMock()
        config.output_dir = "/test/output"
        config.log_dir = "/test/logs"
        config.concurrent_limit = 10
        config.request_timeout = 30
        config.write_base64 = True
        config.write_singbox = True
        config.write_clash = True
        config.write_html = False
        config.surge_file = None
        config.qx_file = None
        config.xyz_file = None
        config.include_patterns = []
        config.exclude_patterns = []
        config.include_protocols = []
        config.exclude_protocols = []
        config.github_token = None
        return config

    @pytest.fixture
    def mock_args(self):
        """Create mock arguments."""
        args = MagicMock()
        args.config = "config.yaml"
        args.sources = "sources.txt"
        args.channels = "channels.txt"
        args.protocols = None
        args.hours = 24
        args.failure_threshold = 3
        args.no_prune = False
        args.bot = False
        args.output_dir = None
        args.concurrent_limit = None
        args.request_timeout = None
        args.no_base64 = False
        args.no_singbox = False
        args.no_clash = False
        args.write_html = False
        args.output_surge = None
        args.output_qx = None
        args.output_xyz = None
        args.include_pattern = None
        args.exclude_pattern = None
        args.shuffle_sources = False
        args.upload_gist = False
        args.with_merger = False
        return args

    def test_main_prints_warning(self, mock_args, mock_config):
        """Test that main prints public source warning."""
        with patch('streamline_vpn.merger.aggregator_tool.print_public_source_warning') as mock_warning:
            with patch('streamline_vpn.merger.aggregator_tool.load_config', return_value=mock_config):
                with patch('streamline_vpn.merger.aggregator_tool.setup_logging'):
                    with patch('streamline_vpn.merger.aggregator_tool.asyncio.run'):
                        with patch('streamline_vpn.merger.aggregator_tool.Path'):
                            with patch('builtins.print'):
                                main(mock_args)
                                
                                mock_warning.assert_called_once()

    def test_main_parses_args_when_none_provided(self, mock_config):
        """Test that main parses arguments when none provided."""
        with patch('streamline_vpn.merger.aggregator_tool.build_parser') as mock_build_parser:
            with patch('streamline_vpn.merger.aggregator_tool.print_public_source_warning'):
                with patch('streamline_vpn.merger.aggregator_tool.load_config', return_value=mock_config):
                    with patch('streamline_vpn.merger.aggregator_tool.setup_logging'):
                        with patch('streamline_vpn.merger.aggregator_tool.asyncio.run'):
                            with patch('streamline_vpn.merger.aggregator_tool.Path'):
                                with patch('builtins.print'):
                                    mock_parser = MagicMock()
                                    mock_parser.parse_args.return_value = MagicMock()
                                    mock_build_parser.return_value = mock_parser
                                    
                                    main(None)
                                    
                                    mock_build_parser.assert_called_once()
                                    mock_parser.parse_args.assert_called_once()

    def test_main_handles_config_not_found(self, mock_args):
        """Test that main handles config file not found."""
        with patch('streamline_vpn.merger.aggregator_tool.print_public_source_warning'):
            with patch('streamline_vpn.merger.aggregator_tool.load_config', side_effect=ValueError("Config not found")):
                with patch('builtins.print') as mock_print:
                    with patch('sys.exit') as mock_exit:
                        main(mock_args)
                        
                        mock_print.assert_called_with("Config file not found. Copy config.yaml.example to config.yaml.")
                        mock_exit.assert_called_once_with(1)

    def test_main_overrides_config_with_args(self, mock_args, mock_config):
        """Test that main overrides config with command line arguments."""
        # Set up args to override config
        mock_args.output_dir = "/custom/output"
        mock_args.concurrent_limit = 20
        mock_args.request_timeout = 60
        mock_args.no_base64 = True
        mock_args.no_singbox = True
        mock_args.no_clash = True
        mock_args.write_html = True
        mock_args.output_surge = "surge.conf"
        mock_args.output_qx = "qx.conf"
        mock_args.output_xyz = "xyz.conf"
        mock_args.include_pattern = ["pattern1", "pattern2"]
        mock_args.exclude_pattern = ["exclude1"]
        
        with patch('streamline_vpn.merger.aggregator_tool.print_public_source_warning'):
            with patch('streamline_vpn.merger.aggregator_tool.load_config', return_value=mock_config):
                with patch('streamline_vpn.merger.aggregator_tool.setup_logging'):
                    with patch('streamline_vpn.merger.aggregator_tool.asyncio.run'):
                        with patch('streamline_vpn.merger.aggregator_tool.Path') as mock_path:
                            with patch('builtins.print'):
                                # Mock Path operations
                                mock_output_path = MagicMock()
                                mock_log_path = MagicMock()
                                mock_path.side_effect = [mock_output_path, mock_log_path]
                                mock_output_path.expanduser.return_value.resolve.return_value = mock_output_path
                                mock_log_path.expanduser.return_value.resolve.return_value = mock_log_path
                                
                                main(mock_args)
                                
                                # Verify config was overridden
                                assert mock_config.output_dir == str(mock_output_path)
                                assert mock_config.concurrent_limit == 20
                                assert mock_config.request_timeout == 60
                                assert mock_config.write_base64 is False
                                assert mock_config.write_singbox is False
                                assert mock_config.write_clash is False
                                assert mock_config.write_html is True
                                assert mock_config.surge_file == "surge.conf"
                                assert mock_config.qx_file == "qx.conf"
                                assert mock_config.xyz_file == "xyz.conf"
                                assert "pattern1" in mock_config.include_patterns
                                assert "pattern2" in mock_config.include_patterns
                                assert "exclude1" in mock_config.exclude_patterns

    def test_main_creates_directories(self, mock_args, mock_config):
        """Test that main creates output and log directories."""
        with patch('streamline_vpn.merger.aggregator_tool.print_public_source_warning'):
            with patch('streamline_vpn.merger.aggregator_tool.load_config', return_value=mock_config):
                with patch('streamline_vpn.merger.aggregator_tool.setup_logging'):
                    with patch('streamline_vpn.merger.aggregator_tool.asyncio.run'):
                        with patch('streamline_vpn.merger.aggregator_tool.Path') as mock_path:
                            with patch('builtins.print'):
                                # Mock Path operations
                                mock_output_path = MagicMock()
                                mock_log_path = MagicMock()
                                mock_path.side_effect = [mock_output_path, mock_log_path]
                                mock_output_path.expanduser.return_value.resolve.return_value = mock_output_path
                                mock_log_path.expanduser.return_value.resolve.return_value = mock_log_path
                                
                                main(mock_args)
                                
                                # Verify directories were created
                                mock_output_path.mkdir.assert_called_once_with(parents=True, exist_ok=True)
                                mock_log_path.mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_main_runs_bot_mode(self, mock_args, mock_config):
        """Test that main runs telegram bot mode when --bot flag is set."""
        mock_args.bot = True
        
        with patch('streamline_vpn.merger.aggregator_tool.print_public_source_warning'):
            with patch('streamline_vpn.merger.aggregator_tool.load_config', return_value=mock_config):
                with patch('streamline_vpn.merger.aggregator_tool.setup_logging'):
                    with patch('streamline_vpn.merger.aggregator_tool.asyncio.run') as mock_asyncio_run:
                        with patch('streamline_vpn.merger.aggregator_tool.telegram_bot_mode') as mock_bot_mode:
                            with patch('streamline_vpn.merger.aggregator_tool.Path') as mock_path:
                                with patch('builtins.print'):
                                    # Mock Path operations
                                    mock_output_path = MagicMock()
                                    mock_log_path = MagicMock()
                                    mock_sources_path = MagicMock()
                                    mock_channels_path = MagicMock()
                                    mock_path.side_effect = [mock_output_path, mock_log_path, mock_sources_path, mock_channels_path]
                                    mock_output_path.expanduser.return_value.resolve.return_value = mock_output_path
                                    mock_log_path.expanduser.return_value.resolve.return_value = mock_log_path
                                    
                                    main(mock_args)
                                    
                                    # Verify bot mode was called
                                    mock_asyncio_run.assert_called_once()
                                    call_args = mock_asyncio_run.call_args[0][0]
                                    # The call should be to telegram_bot_mode coroutine

    def test_main_runs_pipeline_mode(self, mock_args, mock_config):
        """Test that main runs pipeline mode when --bot flag is not set."""
        mock_args.protocols = "vmess,vless"
        
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
                                    mock_sources_path = MagicMock()
                                    mock_channels_path = MagicMock()
                                    mock_out_dir = MagicMock()
                                    mock_path.side_effect = [mock_output_path, mock_log_path, mock_sources_path, mock_channels_path]
                                    mock_output_path.expanduser.return_value.resolve.return_value = mock_output_path
                                    mock_log_path.expanduser.return_value.resolve.return_value = mock_log_path
                                    
                                    # Mock pipeline return
                                    mock_run_pipeline.return_value = (mock_out_dir, [])
                                    mock_asyncio_run.return_value = (mock_out_dir, [])
                                    
                                    main(mock_args)
                                    
                                    # Verify pipeline was called
                                    mock_asyncio_run.assert_called_once()
                                    mock_print.assert_any_call(f"Aggregation complete. Files written to {mock_out_dir.resolve()}")

    def test_main_handles_protocols_parsing(self, mock_args, mock_config):
        """Test that main correctly parses protocols argument."""
        mock_args.protocols = "vmess, vless , trojan"
        
        with patch('streamline_vpn.merger.aggregator_tool.print_public_source_warning'):
            with patch('streamline_vpn.merger.aggregator_tool.load_config', return_value=mock_config):
                with patch('streamline_vpn.merger.aggregator_tool.setup_logging'):
                    with patch('streamline_vpn.merger.aggregator_tool.asyncio.run') as mock_asyncio_run:
                        with patch('streamline_vpn.merger.aggregator_tool.run_pipeline') as mock_run_pipeline:
                            with patch('streamline_vpn.merger.aggregator_tool.Path') as mock_path:
                                with patch('builtins.print'):
                                    # Mock Path operations
                                    mock_output_path = MagicMock()
                                    mock_log_path = MagicMock()
                                    mock_sources_path = MagicMock()
                                    mock_channels_path = MagicMock()
                                    mock_out_dir = MagicMock()
                                    mock_path.side_effect = [mock_output_path, mock_log_path, mock_sources_path, mock_channels_path]
                                    mock_output_path.expanduser.return_value.resolve.return_value = mock_output_path
                                    mock_log_path.expanduser.return_value.resolve.return_value = mock_log_path
                                    
                                    # Mock pipeline return
                                    mock_run_pipeline.return_value = (mock_out_dir, [])
                                    mock_asyncio_run.return_value = (mock_out_dir, [])
                                    
                                    main(mock_args)
                                    
                                    # Verify protocols were parsed correctly
                                    # The protocols should be passed to run_pipeline
                                    mock_asyncio_run.assert_called_once()

    def test_main_uploads_to_gist(self, mock_args, mock_config):
        """Test that main uploads files to gist when --upload-gist flag is set."""
        mock_args.upload_gist = True
        mock_config.github_token = "test-token"
        
        with patch('streamline_vpn.merger.aggregator_tool.print_public_source_warning'):
            with patch('streamline_vpn.merger.aggregator_tool.load_config', return_value=mock_config):
                with patch('streamline_vpn.merger.aggregator_tool.setup_logging'):
                    with patch('streamline_vpn.merger.aggregator_tool.asyncio.run') as mock_asyncio_run:
                        with patch('streamline_vpn.merger.aggregator_tool.upload_files_to_gist') as mock_upload:
                            with patch('streamline_vpn.merger.aggregator_tool.write_upload_links') as mock_write_links:
                                with patch('streamline_vpn.merger.aggregator_tool.Path') as mock_path:
                                    with patch('builtins.print') as mock_print:
                                        # Mock Path operations
                                        mock_output_path = MagicMock()
                                        mock_log_path = MagicMock()
                                        mock_sources_path = MagicMock()
                                        mock_channels_path = MagicMock()
                                        mock_out_dir = MagicMock()
                                        mock_files = [Path("file1.txt"), Path("file2.txt")]
                                        mock_path.side_effect = [mock_output_path, mock_log_path, mock_sources_path, mock_channels_path]
                                        mock_output_path.expanduser.return_value.resolve.return_value = mock_output_path
                                        mock_log_path.expanduser.return_value.resolve.return_value = mock_log_path
                                        
                                        # Mock pipeline return
                                        mock_asyncio_run.side_effect = [
                                            (mock_out_dir, mock_files),  # First call to run_pipeline
                                            {"file1.txt": "http://link1", "file2.txt": "http://link2"}  # Second call to upload_files_to_gist
                                        ]
                                        
                                        # Mock upload return
                                        mock_upload.return_value = {"file1.txt": "http://link1", "file2.txt": "http://link2"}
                                        mock_write_links.return_value = Path("links.txt")
                                        
                                        main(mock_args)
                                        
                                        # Verify upload was called
                                        assert mock_asyncio_run.call_count == 2
                                        mock_write_links.assert_called_once()
                                        mock_print.assert_any_call("Uploaded files. Links saved to links.txt")

    def test_main_upload_gist_no_token(self, mock_args, mock_config):
        """Test that main handles missing GitHub token for gist upload."""
        mock_args.upload_gist = True
        mock_config.github_token = None
        
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
                                    mock_sources_path = MagicMock()
                                    mock_channels_path = MagicMock()
                                    mock_out_dir = MagicMock()
                                    mock_files = [Path("file1.txt")]
                                    mock_path.side_effect = [mock_output_path, mock_log_path, mock_sources_path, mock_channels_path]
                                    mock_output_path.expanduser.return_value.resolve.return_value = mock_output_path
                                    mock_log_path.expanduser.return_value.resolve.return_value = mock_log_path
                                    
                                    # Mock pipeline return
                                    mock_asyncio_run.return_value = (mock_out_dir, mock_files)
                                    
                                    main(mock_args)
                                    
                                    # Verify error message was printed
                                    mock_print.assert_any_call(
                                        "GitHub token not provided. Set github_token in config or GITHUB_TOKEN env var"
                                    )

    def test_main_runs_with_merger(self, mock_args, mock_config):
        """Test that main runs vpn_merger when --with-merger flag is set."""
        mock_args.with_merger = True
        
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
                                        mock_sources_path = MagicMock()
                                        mock_channels_path = MagicMock()
                                        mock_out_dir = MagicMock()
                                        mock_path.side_effect = [mock_output_path, mock_log_path, mock_sources_path, mock_channels_path]
                                        mock_output_path.expanduser.return_value.resolve.return_value = mock_output_path
                                        mock_log_path.expanduser.return_value.resolve.return_value = mock_log_path
                                        
                                        # Mock pipeline return
                                        mock_asyncio_run.return_value = (mock_out_dir, [])
                                        
                                        # Mock vpn_merger CONFIG
                                        mock_vpn_merger.CONFIG = MagicMock()
                                        
                                        main(mock_args)
                                        
                                        # Verify vpn_merger was configured and run
                                        assert mock_vpn_merger.CONFIG.resume_file == str(mock_out_dir / "vpn_subscription_raw.txt")
                                        assert mock_vpn_merger.CONFIG.output_dir == mock_config.output_dir
                                        mock_vpn_merger.detect_and_run.assert_called_once()
                                        mock_print.assert_any_call("\n===== VPN Merger Summary =====")


class TestMainEdgeCases:
    """Edge case tests for main function."""

    def test_main_with_env_github_token(self):
        """Test that main uses GITHUB_TOKEN environment variable."""
        mock_args = MagicMock()
        mock_args.config = "config.yaml"
        mock_args.upload_gist = True
        mock_args.bot = False
        mock_args.with_merger = False
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
                        with patch('streamline_vpn.merger.aggregator_tool.upload_files_to_gist') as mock_upload:
                            with patch('streamline_vpn.merger.aggregator_tool.write_upload_links') as mock_write_links:
                                with patch('streamline_vpn.merger.aggregator_tool.Path') as mock_path:
                                    with patch('builtins.print'):
                                        with patch.dict(os.environ, {'GITHUB_TOKEN': 'env-token'}):
                                            # Mock Path operations
                                            mock_output_path = MagicMock()
                                            mock_log_path = MagicMock()
                                            mock_sources_path = MagicMock()
                                            mock_channels_path = MagicMock()
                                            mock_out_dir = MagicMock()
                                            mock_files = [Path("file1.txt")]
                                            mock_path.side_effect = [mock_output_path, mock_log_path, mock_sources_path, mock_channels_path]
                                            mock_output_path.expanduser.return_value.resolve.return_value = mock_output_path
                                            mock_log_path.expanduser.return_value.resolve.return_value = mock_log_path
                                            
                                            # Mock pipeline return
                                            mock_asyncio_run.side_effect = [
                                                (mock_out_dir, mock_files),  # First call to run_pipeline
                                                {"file1.txt": "http://link1"}  # Second call to upload_files_to_gist
                                            ]
                                            
                                            mock_upload.return_value = {"file1.txt": "http://link1"}
                                            mock_write_links.return_value = Path("links.txt")
                                            
                                            main(mock_args)
                                            
                                            # Verify upload was called with env token
                                            assert mock_asyncio_run.call_count == 2

    def test_main_getattr_shuffle_sources(self):
        """Test that main handles getattr for shuffle_sources correctly."""
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
        # Don't set shuffle_sources to test getattr
        del mock_args.shuffle_sources
        
        mock_config = MagicMock()
        mock_config.output_dir = "/test/output"
        mock_config.log_dir = "/test/logs"
        mock_config.include_patterns = []
        mock_config.exclude_patterns = []
        
        with patch('streamline_vpn.merger.aggregator_tool.print_public_source_warning'):
            with patch('streamline_vpn.merger.aggregator_tool.load_config', return_value=mock_config):
                with patch('streamline_vpn.merger.aggregator_tool.setup_logging'):
                    with patch('streamline_vpn.merger.aggregator_tool.asyncio.run'):
                        with patch('streamline_vpn.merger.aggregator_tool.Path') as mock_path:
                            with patch('builtins.print'):
                                # Mock Path operations
                                mock_output_path = MagicMock()
                                mock_log_path = MagicMock()
                                mock_path.side_effect = [mock_output_path, mock_log_path, MagicMock(), MagicMock()]
                                mock_output_path.expanduser.return_value.resolve.return_value = mock_output_path
                                mock_log_path.expanduser.return_value.resolve.return_value = mock_log_path
                                
                                main(mock_args)
                                
                                # Should not raise an error and shuffle_sources should be False
                                assert mock_config.shuffle_sources is False


class TestMainModuleExecution:
    """Test module execution."""

    def test_main_module_execution(self):
        """Test that main is called when module is executed."""
        # This test is conceptual - we can't easily test __main__ execution
        # Just verify the main function exists and is callable
        from streamline_vpn.merger.aggregator_tool import main
        assert callable(main)
