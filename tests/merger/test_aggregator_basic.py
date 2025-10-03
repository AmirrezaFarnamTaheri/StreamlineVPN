"""Basic tests for merger aggregator_tool module."""

import argparse
from unittest.mock import patch, MagicMock

import pytest

from streamline_vpn.merger.aggregator_tool import (
    setup_logging,
    build_parser,
    main
)


class TestSetupLogging:
    """Test cases for setup_logging function."""

    def test_setup_logging_calls_mkdir(self):
        """Test that setup_logging calls mkdir on log directory."""
        mock_log_dir = MagicMock()
        
        with patch('streamline_vpn.merger.aggregator_tool.datetime'):
            with patch('streamline_vpn.merger.aggregator_tool.logging.basicConfig'):
                with patch('streamline_vpn.merger.aggregator_tool.logging.StreamHandler'):
                    with patch('streamline_vpn.merger.aggregator_tool.logging.FileHandler'):
                        setup_logging(mock_log_dir)
                        
                        mock_log_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)


class TestBuildParser:
    """Test cases for build_parser function."""

    def test_build_parser_returns_parser(self):
        """Test that build_parser returns ArgumentParser."""
        parser = build_parser()
        assert isinstance(parser, argparse.ArgumentParser)

    def test_build_parser_accepts_existing_parser(self):
        """Test that build_parser accepts existing parser."""
        existing = argparse.ArgumentParser()
        result = build_parser(existing)
        assert result is existing

    def test_build_parser_has_bot_argument(self):
        """Test that parser has --bot argument."""
        parser = build_parser()
        args = parser.parse_args(['--bot'])
        assert args.bot is True

    def test_build_parser_has_protocols_argument(self):
        """Test that parser has --protocols argument."""
        parser = build_parser()
        args = parser.parse_args(['--protocols', 'vmess,vless'])
        assert args.protocols == 'vmess,vless'


class TestMain:
    """Test cases for main function."""

    def test_main_calls_print_warning(self):
        """Test that main calls print_public_source_warning."""
        mock_args = MagicMock()
        mock_args.config = "config.yaml"
        mock_args.bot = False
        mock_args.with_merger = False
        mock_args.upload_gist = False
        
        mock_config = MagicMock()
        mock_config.output_dir = "/test"
        mock_config.log_dir = "/logs"
        mock_config.include_patterns = []
        mock_config.exclude_patterns = []
        
        with patch('streamline_vpn.merger.aggregator_tool.print_public_source_warning') as mock_warning:
            with patch('streamline_vpn.merger.aggregator_tool.load_config', return_value=mock_config):
                with patch('streamline_vpn.merger.aggregator_tool.setup_logging'):
                    with patch('streamline_vpn.merger.aggregator_tool.asyncio.run'):
                        with patch('streamline_vpn.merger.aggregator_tool.Path'):
                            with patch('builtins.print'):
                                main(mock_args)
                                
                                mock_warning.assert_called_once()

    def test_main_handles_config_error(self):
        """Test that main handles config loading error."""
        mock_args = MagicMock()
        mock_args.config = "nonexistent.yaml"
        
        with patch('streamline_vpn.merger.aggregator_tool.print_public_source_warning'):
            with patch('streamline_vpn.merger.aggregator_tool.load_config', side_effect=ValueError()):
                with patch('builtins.print') as mock_print:
                    with patch('sys.exit') as mock_exit:
                        main(mock_args)
                        
                        mock_print.assert_called_with("Config file not found. Copy config.yaml.example to config.yaml.")
                        mock_exit.assert_called_once_with(1)

    def test_main_parses_args_when_none(self):
        """Test that main parses args when None provided."""
        mock_config = MagicMock()
        mock_config.output_dir = "/test"
        mock_config.log_dir = "/logs"
        mock_config.include_patterns = []
        mock_config.exclude_patterns = []
        
        with patch('streamline_vpn.merger.aggregator_tool.build_parser') as mock_build:
            with patch('streamline_vpn.merger.aggregator_tool.print_public_source_warning'):
                with patch('streamline_vpn.merger.aggregator_tool.load_config', return_value=mock_config):
                    with patch('streamline_vpn.merger.aggregator_tool.setup_logging'):
                        with patch('streamline_vpn.merger.aggregator_tool.asyncio.run'):
                            with patch('streamline_vpn.merger.aggregator_tool.Path'):
                                with patch('builtins.print'):
                                    mock_parser = MagicMock()
                                    mock_args = MagicMock()
                                    mock_args.config = "config.yaml"
                                    mock_args.bot = False
                                    mock_args.with_merger = False
                                    mock_args.upload_gist = False
                                    mock_parser.parse_args.return_value = mock_args
                                    mock_build.return_value = mock_parser
                                    
                                    main(None)
                                    
                                    mock_build.assert_called_once()
                                    mock_parser.parse_args.assert_called_once()

    def test_main_overrides_output_dir(self):
        """Test that main overrides output_dir from args."""
        mock_args = MagicMock()
        mock_args.config = "config.yaml"
        mock_args.output_dir = "/custom/output"
        mock_args.bot = False
        mock_args.with_merger = False
        mock_args.upload_gist = False
        
        mock_config = MagicMock()
        mock_config.output_dir = "/default/output"
        mock_config.log_dir = "/logs"
        mock_config.include_patterns = []
        mock_config.exclude_patterns = []
        
        with patch('streamline_vpn.merger.aggregator_tool.print_public_source_warning'):
            with patch('streamline_vpn.merger.aggregator_tool.load_config', return_value=mock_config):
                with patch('streamline_vpn.merger.aggregator_tool.setup_logging'):
                    with patch('streamline_vpn.merger.aggregator_tool.asyncio.run'):
                        with patch('streamline_vpn.merger.aggregator_tool.Path') as mock_path:
                            with patch('builtins.print'):
                                mock_path_instance = MagicMock()
                                mock_path_instance.expanduser.return_value.resolve.return_value = "/custom/output"
                                mock_path.return_value = mock_path_instance
                                
                                main(mock_args)
                                
                                # Config should be overridden
                                assert mock_config.output_dir == "/custom/output"

    def test_main_runs_bot_mode(self):
        """Test that main runs bot mode when bot=True."""
        mock_args = MagicMock()
        mock_args.config = "config.yaml"
        mock_args.bot = True
        
        mock_config = MagicMock()
        mock_config.output_dir = "/test"
        mock_config.log_dir = "/logs"
        mock_config.include_patterns = []
        mock_config.exclude_patterns = []
        
        with patch('streamline_vpn.merger.aggregator_tool.print_public_source_warning'):
            with patch('streamline_vpn.merger.aggregator_tool.load_config', return_value=mock_config):
                with patch('streamline_vpn.merger.aggregator_tool.setup_logging'):
                    with patch('streamline_vpn.merger.aggregator_tool.asyncio.run') as mock_run:
                        with patch('streamline_vpn.merger.aggregator_tool.telegram_bot_mode'):
                            with patch('streamline_vpn.merger.aggregator_tool.Path'):
                                main(mock_args)
                                
                                # Should call asyncio.run for bot mode
                                mock_run.assert_called_once()

    def test_main_runs_pipeline_mode(self):
        """Test that main runs pipeline mode when bot=False."""
        mock_args = MagicMock()
        mock_args.config = "config.yaml"
        mock_args.bot = False
        mock_args.with_merger = False
        mock_args.upload_gist = False
        
        mock_config = MagicMock()
        mock_config.output_dir = "/test"
        mock_config.log_dir = "/logs"
        mock_config.include_patterns = []
        mock_config.exclude_patterns = []
        
        with patch('streamline_vpn.merger.aggregator_tool.print_public_source_warning'):
            with patch('streamline_vpn.merger.aggregator_tool.load_config', return_value=mock_config):
                with patch('streamline_vpn.merger.aggregator_tool.setup_logging'):
                    with patch('streamline_vpn.merger.aggregator_tool.asyncio.run') as mock_run:
                        with patch('streamline_vpn.merger.aggregator_tool.Path'):
                            with patch('builtins.print'):
                                mock_out_dir = MagicMock()
                                mock_run.return_value = (mock_out_dir, [])
                                
                                main(mock_args)
                                
                                # Should call asyncio.run for pipeline
                                mock_run.assert_called_once()

    def test_main_handles_gist_upload_no_token(self):
        """Test that main handles gist upload with no token."""
        mock_args = MagicMock()
        mock_args.config = "config.yaml"
        mock_args.bot = False
        mock_args.with_merger = False
        mock_args.upload_gist = True
        
        mock_config = MagicMock()
        mock_config.output_dir = "/test"
        mock_config.log_dir = "/logs"
        mock_config.github_token = None
        mock_config.include_patterns = []
        mock_config.exclude_patterns = []
        
        with patch('streamline_vpn.merger.aggregator_tool.print_public_source_warning'):
            with patch('streamline_vpn.merger.aggregator_tool.load_config', return_value=mock_config):
                with patch('streamline_vpn.merger.aggregator_tool.setup_logging'):
                    with patch('streamline_vpn.merger.aggregator_tool.asyncio.run') as mock_run:
                        with patch('streamline_vpn.merger.aggregator_tool.Path'):
                            with patch('builtins.print') as mock_print:
                                with patch('os.environ.get', return_value=None):
                                    mock_out_dir = MagicMock()
                                    mock_run.return_value = (mock_out_dir, [])
                                    
                                    main(mock_args)
                                    
                                    # Should print error message
                                    mock_print.assert_any_call(
                                        "GitHub token not provided. Set github_token in config or GITHUB_TOKEN env var"
                                    )

    def test_main_runs_with_merger(self):
        """Test that main runs with merger when with_merger=True."""
        mock_args = MagicMock()
        mock_args.config = "config.yaml"
        mock_args.bot = False
        mock_args.with_merger = True
        mock_args.upload_gist = False
        
        mock_config = MagicMock()
        mock_config.output_dir = "/test"
        mock_config.log_dir = "/logs"
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
                    with patch('streamline_vpn.merger.aggregator_tool.asyncio.run') as mock_run:
                        with patch('streamline_vpn.merger.aggregator_tool.vpn_merger') as mock_merger:
                            with patch('streamline_vpn.merger.aggregator_tool.Path'):
                                with patch('streamline_vpn.merger.aggregator_tool.redirect_stdout'):
                                    with patch('builtins.print') as mock_print:
                                        mock_out_dir = MagicMock()
                                        mock_run.return_value = (mock_out_dir, [])
                                        mock_merger.CONFIG = MagicMock()
                                        
                                        main(mock_args)
                                        
                                        # Should call detect_and_run
                                        mock_merger.detect_and_run.assert_called_once()
                                        mock_print.assert_any_call("\n===== VPN Merger Summary =====")


class TestMainFunctionality:
    """Test main function exists and is importable."""

    def test_main_function_exists(self):
        """Test that main function exists."""
        from streamline_vpn.merger.aggregator_tool import main
        assert callable(main)
