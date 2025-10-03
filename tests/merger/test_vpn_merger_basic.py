"""Basic tests for merger vpn_merger module."""

import asyncio
import json
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

from streamline_vpn.merger.vpn_merger import (
    UltimateVPNMerger,
    main_async,
    detect_and_run,
    build_parser,
    main
)


class TestUltimateVPNMerger:
    """Test cases for UltimateVPNMerger class."""

    @pytest.fixture
    def mock_config(self):
        """Create mock CONFIG."""
        config = MagicMock()
        config.shuffle_sources = False
        config.history_file = "history.json"
        config.output_dir = "/test/output"
        config.save_every = 1000
        return config

    def test_init_basic(self, mock_config):
        """Test basic initialization of UltimateVPNMerger."""
        with patch('streamline_vpn.merger.vpn_merger.CONFIG', mock_config):
            with patch('streamline_vpn.merger.vpn_merger.UnifiedSources') as mock_sources:
                with patch('streamline_vpn.merger.vpn_merger.EnhancedConfigProcessor'):
                    with patch('streamline_vpn.merger.vpn_merger.AsyncSourceFetcher'):
                        with patch('streamline_vpn.merger.vpn_merger.Deduplicator'):
                            with patch('streamline_vpn.merger.vpn_merger.Sorter'):
                                with patch('streamline_vpn.merger.vpn_merger.Analyzer'):
                                    with patch('streamline_vpn.merger.vpn_merger.BatchProcessor'):
                                        with patch('streamline_vpn.merger.vpn_merger.choose_proxy'):
                                            with patch('streamline_vpn.merger.vpn_merger.Path') as mock_path:
                                                mock_sources.get_all_sources.return_value = ["source1", "source2"]
                                                mock_path_instance = MagicMock()
                                                mock_path_instance.is_absolute.return_value = False
                                                mock_path_instance.read_text.side_effect = FileNotFoundError()
                                                mock_path_instance.parent.mkdir = MagicMock()
                                                mock_path.return_value = mock_path_instance
                                                
                                                merger = UltimateVPNMerger()
                                                
                                                assert merger is not None
                                                assert hasattr(merger, 'sources')
                                                assert hasattr(merger, 'processor')

    def test_init_with_sources_file(self, mock_config):
        """Test initialization with custom sources file."""
        with patch('streamline_vpn.merger.vpn_merger.CONFIG', mock_config):
            with patch('streamline_vpn.merger.vpn_merger.UnifiedSources') as mock_sources:
                with patch('streamline_vpn.merger.vpn_merger.EnhancedConfigProcessor'):
                    with patch('streamline_vpn.merger.vpn_merger.AsyncSourceFetcher'):
                        with patch('streamline_vpn.merger.vpn_merger.Deduplicator'):
                            with patch('streamline_vpn.merger.vpn_merger.Sorter'):
                                with patch('streamline_vpn.merger.vpn_merger.Analyzer'):
                                    with patch('streamline_vpn.merger.vpn_merger.BatchProcessor'):
                                        with patch('streamline_vpn.merger.vpn_merger.choose_proxy'):
                                            with patch('streamline_vpn.merger.vpn_merger.Path'):
                                                mock_sources.get_all_sources.return_value = ["custom_source"]
                                                
                                                UltimateVPNMerger(sources_file="custom_sources.txt")
                                                
                                                mock_sources.get_all_sources.assert_called_once_with("custom_sources.txt")

    def test_init_loads_existing_history(self, mock_config):
        """Test initialization loads existing proxy history."""
        history_data = {"proxy1": {"ping": 100, "success": True}}
        
        with patch('streamline_vpn.merger.vpn_merger.CONFIG', mock_config):
            with patch('streamline_vpn.merger.vpn_merger.UnifiedSources') as mock_sources:
                with patch('streamline_vpn.merger.vpn_merger.EnhancedConfigProcessor'):
                    with patch('streamline_vpn.merger.vpn_merger.AsyncSourceFetcher'):
                        with patch('streamline_vpn.merger.vpn_merger.Deduplicator'):
                            with patch('streamline_vpn.merger.vpn_merger.Sorter'):
                                with patch('streamline_vpn.merger.vpn_merger.Analyzer'):
                                    with patch('streamline_vpn.merger.vpn_merger.BatchProcessor'):
                                        with patch('streamline_vpn.merger.vpn_merger.choose_proxy'):
                                            with patch('streamline_vpn.merger.vpn_merger.Path') as mock_path:
                                                mock_sources.get_all_sources.return_value = ["source1"]
                                                mock_path_instance = MagicMock()
                                                mock_path_instance.is_absolute.return_value = False
                                                mock_path_instance.read_text.return_value = json.dumps(history_data)
                                                mock_path_instance.parent.mkdir = MagicMock()
                                                mock_path.return_value = mock_path_instance
                                                
                                                merger = UltimateVPNMerger()
                                                
                                                assert merger.proxy_history == history_data

    @pytest.mark.asyncio
    async def test_update_history(self, mock_config):
        """Test _update_history method."""
        with patch('streamline_vpn.merger.vpn_merger.CONFIG', mock_config):
            with patch('streamline_vpn.merger.vpn_merger.UnifiedSources') as mock_sources:
                with patch('streamline_vpn.merger.vpn_merger.EnhancedConfigProcessor'):
                    with patch('streamline_vpn.merger.vpn_merger.AsyncSourceFetcher'):
                        with patch('streamline_vpn.merger.vpn_merger.Deduplicator'):
                            with patch('streamline_vpn.merger.vpn_merger.Sorter'):
                                with patch('streamline_vpn.merger.vpn_merger.Analyzer'):
                                    with patch('streamline_vpn.merger.vpn_merger.BatchProcessor'):
                                        with patch('streamline_vpn.merger.vpn_merger.choose_proxy'):
                                            with patch('streamline_vpn.merger.vpn_merger.Path'):
                                                mock_sources.get_all_sources.return_value = ["source1"]
                                                
                                                merger = UltimateVPNMerger()
                                                
                                                config_result = MagicMock()
                                                config_result.config = "test-config"
                                                config_result.ping_time = 0.1
                                                config_result.success = True
                                                
                                                await merger._update_history(config_result)
                                                
                                                assert "test-config" in merger.proxy_history
                                                assert merger.proxy_history["test-config"]["ping"] == 100

    def test_sort_by_performance(self, mock_config):
        """Test _sort_by_performance method."""
        with patch('streamline_vpn.merger.vpn_merger.CONFIG', mock_config):
            with patch('streamline_vpn.merger.vpn_merger.UnifiedSources') as mock_sources:
                with patch('streamline_vpn.merger.vpn_merger.EnhancedConfigProcessor'):
                    with patch('streamline_vpn.merger.vpn_merger.AsyncSourceFetcher'):
                        with patch('streamline_vpn.merger.vpn_merger.Deduplicator'):
                            with patch('streamline_vpn.merger.vpn_merger.Sorter'):
                                with patch('streamline_vpn.merger.vpn_merger.Analyzer'):
                                    with patch('streamline_vpn.merger.vpn_merger.BatchProcessor'):
                                        with patch('streamline_vpn.merger.vpn_merger.choose_proxy'):
                                            with patch('streamline_vpn.merger.vpn_merger.Path'):
                                                mock_sources.get_all_sources.return_value = ["source1"]
                                                
                                                merger = UltimateVPNMerger()
                                                
                                                # Create mock results with different ping times
                                                result1 = MagicMock()
                                                result1.ping_time = 0.2
                                                result1.config = "config1"
                                                
                                                result2 = MagicMock()
                                                result2.ping_time = 0.1
                                                result2.config = "config2"
                                                
                                                results = [result1, result2]
                                                
                                                sorted_results = merger._sort_by_performance(results)
                                                
                                                # Should be sorted by ping time (fastest first)
                                                assert sorted_results[0] == result2
                                                assert sorted_results[1] == result1

    def test_parse_extra_params(self, mock_config):
        """Test _parse_extra_params method."""
        with patch('streamline_vpn.merger.vpn_merger.CONFIG', mock_config):
            with patch('streamline_vpn.merger.vpn_merger.UnifiedSources') as mock_sources:
                with patch('streamline_vpn.merger.vpn_merger.EnhancedConfigProcessor'):
                    with patch('streamline_vpn.merger.vpn_merger.AsyncSourceFetcher'):
                        with patch('streamline_vpn.merger.vpn_merger.Deduplicator'):
                            with patch('streamline_vpn.merger.vpn_merger.Sorter'):
                                with patch('streamline_vpn.merger.vpn_merger.Analyzer'):
                                    with patch('streamline_vpn.merger.vpn_merger.BatchProcessor'):
                                        with patch('streamline_vpn.merger.vpn_merger.choose_proxy'):
                                            with patch('streamline_vpn.merger.vpn_merger.Path'):
                                                mock_sources.get_all_sources.return_value = ["source1"]
                                                
                                                merger = UltimateVPNMerger()
                                                
                                                link = "vmess://config?extra1=value1&extra2=value2"
                                                params = merger._parse_extra_params(link)
                                                
                                                assert params == {"extra1": ["value1"], "extra2": ["value2"]}


class TestMainAsync:
    """Test cases for main_async function."""

    @pytest.mark.asyncio
    async def test_main_async_basic(self):
        """Test basic main_async function."""
        mock_args = MagicMock()
        mock_args.sources = "sources.txt"
        
        with patch('streamline_vpn.merger.vpn_merger.UltimateVPNMerger') as mock_merger_class:
            mock_merger = AsyncMock()
            mock_merger_class.return_value = mock_merger
            
            await main_async(mock_args)
            
            mock_merger_class.assert_called_once_with(sources_file="sources.txt")
            mock_merger.run.assert_called_once()


class TestDetectAndRun:
    """Test cases for detect_and_run function."""

    def test_detect_and_run_normal_environment(self):
        """Test detect_and_run in normal Python environment."""
        with patch('streamline_vpn.merger.vpn_merger.asyncio.run') as mock_run:
            detect_and_run()
            
            mock_run.assert_called_once()

    def test_detect_and_run_jupyter_environment(self):
        """Test detect_and_run in Jupyter environment."""
        with patch('streamline_vpn.merger.vpn_merger.asyncio.run', side_effect=RuntimeError("asyncio.run() cannot be called from a running event loop")):
            with patch('streamline_vpn.merger.vpn_merger.asyncio.create_task') as mock_create_task:
                detect_and_run()
                
                mock_create_task.assert_called_once()


class TestBuildParser:
    """Test cases for build_parser function."""

    def test_build_parser_creates_new_parser(self):
        """Test that build_parser creates new parser when none provided."""
        parser = build_parser()
        
        assert parser is not None
        assert hasattr(parser, 'parse_args')

    def test_build_parser_adds_sources_argument(self):
        """Test that build_parser adds sources argument."""
        parser = build_parser()
        
        # Test parsing with sources argument
        args = parser.parse_args(['--sources', 'custom_sources.txt'])
        assert args.sources == 'custom_sources.txt'


class TestMain:
    """Test cases for main function."""

    def test_main_with_args(self):
        """Test main function with provided arguments."""
        mock_args = MagicMock()
        mock_args.sources = "test_sources.txt"
        
        with patch('streamline_vpn.merger.vpn_merger.detect_and_run') as mock_detect:
            main(mock_args)
            
            mock_detect.assert_called_once_with(mock_args)

    def test_main_without_args(self):
        """Test main function without arguments."""
        with patch('streamline_vpn.merger.vpn_merger.build_parser') as mock_build_parser:
            with patch('streamline_vpn.merger.vpn_merger.detect_and_run') as mock_detect:
                mock_parser = MagicMock()
                mock_args = MagicMock()
                mock_parser.parse_args.return_value = mock_args
                mock_build_parser.return_value = mock_parser
                
                main()
                
                mock_build_parser.assert_called_once()
                mock_parser.parse_args.assert_called_once()
                mock_detect.assert_called_once_with(mock_args)


class TestVPNMergerFunctionality:
    """Test VPN merger functionality exists and is importable."""

    def test_functions_exist(self):
        """Test that main functions exist and are callable."""
        assert callable(main_async)
        assert callable(detect_and_run)
        assert callable(build_parser)
        assert callable(main)
