"""Tests for merger pipeline module."""

import asyncio
import pytest
import time
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from streamline_vpn.merger.pipeline import AggregationPipeline, run_pipeline


class TestAggregationPipeline:
    """Test cases for AggregationPipeline."""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        config = MagicMock()
        config.output_dir = "/test/output"
        config.concurrent_limit = 10
        config.request_timeout = 30
        config.retry_attempts = 3
        config.retry_base_delay = 1.0
        return config

    @pytest.fixture
    def pipeline(self, mock_config):
        """Create AggregationPipeline instance."""
        return AggregationPipeline(mock_config)

    @pytest.fixture
    def mock_sources_file(self):
        """Create mock sources file path."""
        mock_path = MagicMock(spec=Path)
        mock_path.with_suffix.return_value = MagicMock(spec=Path)
        mock_path.with_name.return_value = MagicMock(spec=Path)
        return mock_path

    @pytest.fixture
    def mock_channels_file(self):
        """Create mock channels file path."""
        return MagicMock(spec=Path)

    def test_init(self, mock_config):
        """Test pipeline initialization."""
        pipeline = AggregationPipeline(mock_config)
        
        assert pipeline.cfg == mock_config
        assert pipeline.stats["valid_sources"] == 0
        assert pipeline.stats["fetched_configs"] == 0
        assert pipeline.stats["written_configs"] == 0

    @pytest.mark.asyncio
    async def test_run_successful_pipeline(self, pipeline, mock_sources_file, mock_channels_file):
        """Test successful pipeline execution."""
        with patch('streamline_vpn.merger.pipeline.choose_proxy') as mock_choose_proxy:
            with patch('streamline_vpn.merger.pipeline.aiohttp.TCPConnector') as mock_connector:
                with patch('streamline_vpn.merger.pipeline.aiohttp.ClientSession') as mock_session_class:
                    with patch('streamline_vpn.merger.pipeline.check_and_update_sources') as mock_check_sources:
                        with patch('streamline_vpn.merger.pipeline.fetch_and_parse_configs') as mock_fetch_configs:
                            with patch('streamline_vpn.merger.pipeline.scrape_telegram_configs') as mock_scrape_telegram:
                                with patch('streamline_vpn.merger.pipeline.deduplicate_and_filter') as mock_deduplicate:
                                    with patch('streamline_vpn.merger.pipeline.output_files') as mock_output_files:
                                        with patch('streamline_vpn.merger.pipeline.Path') as mock_path_class:
                                            with patch('streamline_vpn.merger.pipeline.time.time') as mock_time:
                                                with patch('streamline_vpn.merger.pipeline.logging') as mock_logging:
                                                    with patch('builtins.print') as mock_print:
                                                        # Setup mocks
                                                        mock_choose_proxy.return_value = "http://proxy:8080"
                                                        mock_connector_instance = MagicMock()
                                                        mock_connector.return_value = mock_connector_instance
                                                        
                                                        mock_session = AsyncMock()
                                                        mock_session_class.return_value = mock_session
                                                        
                                                        mock_check_sources.return_value = ["http://source1.com", "http://source2.com"]
                                                        mock_fetch_configs.return_value = {"config1", "config2", "config3"}
                                                        mock_scrape_telegram.return_value = {"config4", "config5"}
                                                        mock_deduplicate.return_value = ["final1", "final2", "final3"]
                                                        mock_output_files.return_value = [Path("file1.txt"), Path("file2.txt")]
                                                        
                                                        mock_out_dir = MagicMock(spec=Path)
                                                        mock_path_class.return_value = mock_out_dir
                                                        
                                                        mock_time.side_effect = [1000.0, 1010.5]  # Start and end times
                                                        
                                                        # Run pipeline
                                                        out_dir, files = await pipeline.run(
                                                            mock_sources_file,
                                                            mock_channels_file,
                                                            protocols=["vmess", "vless"],
                                                            last_hours=48,
                                                            failure_threshold=5,
                                                            prune=False
                                                        )
                                                        
                                                        # Verify results
                                                        assert out_dir == mock_out_dir
                                                        assert len(files) == 2
                                                        
                                                        # Verify stats
                                                        assert pipeline.stats["valid_sources"] == 2
                                                        assert pipeline.stats["fetched_configs"] == 5  # 3 HTTP + 2 Telegram
                                                        assert pipeline.stats["written_configs"] == 3
                                                        
                                                        # Verify function calls
                                                        mock_choose_proxy.assert_called_once_with(pipeline.cfg)
                                                        mock_connector.assert_called_once_with(limit=pipeline.cfg.concurrent_limit)
                                                        mock_session_class.assert_called_once_with(
                                                            connector=mock_connector_instance,
                                                            proxy="http://proxy:8080"
                                                        )
                                                        
                                                        mock_check_sources.assert_called_once_with(
                                                            mock_sources_file,
                                                            pipeline.cfg.concurrent_limit,
                                                            pipeline.cfg.request_timeout,
                                                            retries=pipeline.cfg.retry_attempts,
                                                            base_delay=pipeline.cfg.retry_base_delay,
                                                            failures_path=mock_sources_file.with_suffix.return_value,
                                                            max_failures=5,
                                                            prune=False,
                                                            disabled_path=None,
                                                            proxy="http://proxy:8080",
                                                            session=mock_session
                                                        )
                                                        
                                                        mock_fetch_configs.assert_called_once_with(
                                                            ["http://source1.com", "http://source2.com"],
                                                            pipeline.cfg,
                                                            proxy="http://proxy:8080",
                                                            session=mock_session
                                                        )
                                                        
                                                        mock_scrape_telegram.assert_called_once_with(
                                                            pipeline.cfg,
                                                            mock_channels_file,
                                                            48
                                                        )
                                                        
                                                        mock_deduplicate.assert_called_once_with(
                                                            {"config1", "config2", "config3", "config4", "config5"},
                                                            pipeline.cfg,
                                                            ["vmess", "vless"]
                                                        )
                                                        
                                                        mock_output_files.assert_called_once_with(
                                                            ["final1", "final2", "final3"],
                                                            mock_out_dir,
                                                            pipeline.cfg
                                                        )
                                                        
                                                        mock_session.close.assert_called_once()
                                                        
                                                        # Verify logging
                                                        assert mock_logging.info.call_count >= 2
                                                        mock_print.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_with_keyboard_interrupt(self, pipeline, mock_sources_file, mock_channels_file):
        """Test pipeline execution with keyboard interrupt."""
        with patch('streamline_vpn.merger.pipeline.choose_proxy') as mock_choose_proxy:
            with patch('streamline_vpn.merger.pipeline.aiohttp.TCPConnector'):
                with patch('streamline_vpn.merger.pipeline.aiohttp.ClientSession') as mock_session_class:
                    with patch('streamline_vpn.merger.pipeline.check_and_update_sources') as mock_check_sources:
                        with patch('streamline_vpn.merger.pipeline.deduplicate_and_filter') as mock_deduplicate:
                            with patch('streamline_vpn.merger.pipeline.output_files') as mock_output_files:
                                with patch('streamline_vpn.merger.pipeline.Path') as mock_path_class:
                                    with patch('streamline_vpn.merger.pipeline.time.time') as mock_time:
                                        with patch('streamline_vpn.merger.pipeline.logging') as mock_logging:
                                            with patch('builtins.print'):
                                                # Setup mocks
                                                mock_choose_proxy.return_value = None
                                                mock_session = AsyncMock()
                                                mock_session_class.return_value = mock_session
                                                
                                                # Make check_and_update_sources raise KeyboardInterrupt
                                                mock_check_sources.side_effect = KeyboardInterrupt("User interrupted")
                                                
                                                mock_deduplicate.return_value = ["partial1", "partial2"]
                                                mock_output_files.return_value = [Path("partial.txt")]
                                                
                                                mock_out_dir = MagicMock(spec=Path)
                                                mock_path_class.return_value = mock_out_dir
                                                
                                                mock_time.side_effect = [1000.0, 1005.0]
                                                
                                                # Run pipeline
                                                out_dir, files = await pipeline.run(
                                                    mock_sources_file,
                                                    mock_channels_file
                                                )
                                                
                                                # Verify results
                                                assert out_dir == mock_out_dir
                                                assert len(files) == 1
                                                
                                                # Verify warning was logged
                                                mock_logging.warning.assert_called_once_with(
                                                    "Interrupted. Writing partial results..."
                                                )
                                                
                                                # Verify session was closed
                                                mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_with_prune_enabled(self, pipeline, mock_sources_file, mock_channels_file):
        """Test pipeline execution with pruning enabled."""
        with patch('streamline_vpn.merger.pipeline.choose_proxy'):
            with patch('streamline_vpn.merger.pipeline.aiohttp.TCPConnector'):
                with patch('streamline_vpn.merger.pipeline.aiohttp.ClientSession') as mock_session_class:
                    with patch('streamline_vpn.merger.pipeline.check_and_update_sources') as mock_check_sources:
                        with patch('streamline_vpn.merger.pipeline.fetch_and_parse_configs'):
                            with patch('streamline_vpn.merger.pipeline.scrape_telegram_configs'):
                                with patch('streamline_vpn.merger.pipeline.deduplicate_and_filter'):
                                    with patch('streamline_vpn.merger.pipeline.output_files'):
                                        with patch('streamline_vpn.merger.pipeline.Path'):
                                            with patch('streamline_vpn.merger.pipeline.time.time'):
                                                with patch('streamline_vpn.merger.pipeline.logging'):
                                                    with patch('builtins.print'):
                                                        # Setup mocks
                                                        mock_session = AsyncMock()
                                                        mock_session_class.return_value = mock_session
                                                        mock_check_sources.return_value = []
                                                        
                                                        # Run pipeline with prune=True
                                                        await pipeline.run(
                                                            mock_sources_file,
                                                            mock_channels_file,
                                                            prune=True
                                                        )
                                                        
                                                        # Verify disabled_path is set when prune=True
                                                        mock_check_sources.assert_called_once()
                                                        call_args = mock_check_sources.call_args
                                                        assert call_args.kwargs['disabled_path'] == mock_sources_file.with_name.return_value
                                                        mock_sources_file.with_name.assert_called_once_with("sources_disabled.txt")

    @pytest.mark.asyncio
    async def test_run_with_default_parameters(self, pipeline, mock_sources_file, mock_channels_file):
        """Test pipeline execution with default parameters."""
        with patch('streamline_vpn.merger.pipeline.choose_proxy'):
            with patch('streamline_vpn.merger.pipeline.aiohttp.TCPConnector'):
                with patch('streamline_vpn.merger.pipeline.aiohttp.ClientSession') as mock_session_class:
                    with patch('streamline_vpn.merger.pipeline.check_and_update_sources') as mock_check_sources:
                        with patch('streamline_vpn.merger.pipeline.fetch_and_parse_configs'):
                            with patch('streamline_vpn.merger.pipeline.scrape_telegram_configs') as mock_scrape_telegram:
                                with patch('streamline_vpn.merger.pipeline.deduplicate_and_filter') as mock_deduplicate:
                                    with patch('streamline_vpn.merger.pipeline.output_files'):
                                        with patch('streamline_vpn.merger.pipeline.Path'):
                                            with patch('streamline_vpn.merger.pipeline.time.time'):
                                                with patch('streamline_vpn.merger.pipeline.logging'):
                                                    with patch('builtins.print'):
                                                        # Setup mocks
                                                        mock_session = AsyncMock()
                                                        mock_session_class.return_value = mock_session
                                                        mock_check_sources.return_value = []
                                                        mock_deduplicate.return_value = []
                                                        
                                                        # Run pipeline with default parameters
                                                        await pipeline.run(mock_sources_file, mock_channels_file)
                                                        
                                                        # Verify default parameters were used
                                                        mock_scrape_telegram.assert_called_once_with(
                                                            pipeline.cfg,
                                                            mock_channels_file,
                                                            24  # Default last_hours
                                                        )
                                                        
                                                        mock_deduplicate.assert_called_once_with(
                                                            set(),  # Empty configs
                                                            pipeline.cfg,
                                                            None  # Default protocols
                                                        )
                                                        
                                                        # Verify default failure_threshold and prune
                                                        call_args = mock_check_sources.call_args
                                                        assert call_args.kwargs['max_failures'] == 3  # Default failure_threshold
                                                        assert call_args.kwargs['prune'] is True  # Default prune

    @pytest.mark.asyncio
    async def test_run_stats_tracking(self, pipeline, mock_sources_file, mock_channels_file):
        """Test that pipeline correctly tracks statistics."""
        with patch('streamline_vpn.merger.pipeline.choose_proxy'):
            with patch('streamline_vpn.merger.pipeline.aiohttp.TCPConnector'):
                with patch('streamline_vpn.merger.pipeline.aiohttp.ClientSession') as mock_session_class:
                    with patch('streamline_vpn.merger.pipeline.check_and_update_sources') as mock_check_sources:
                        with patch('streamline_vpn.merger.pipeline.fetch_and_parse_configs') as mock_fetch_configs:
                            with patch('streamline_vpn.merger.pipeline.scrape_telegram_configs') as mock_scrape_telegram:
                                with patch('streamline_vpn.merger.pipeline.deduplicate_and_filter') as mock_deduplicate:
                                    with patch('streamline_vpn.merger.pipeline.output_files'):
                                        with patch('streamline_vpn.merger.pipeline.Path'):
                                            with patch('streamline_vpn.merger.pipeline.time.time'):
                                                with patch('streamline_vpn.merger.pipeline.logging'):
                                                    with patch('builtins.print'):
                                                        # Setup mocks with specific counts
                                                        mock_session = AsyncMock()
                                                        mock_session_class.return_value = mock_session
                                                        
                                                        mock_check_sources.return_value = ["s1", "s2", "s3"]  # 3 sources
                                                        mock_fetch_configs.return_value = {"c1", "c2"}  # 2 HTTP configs
                                                        mock_scrape_telegram.return_value = {"c3", "c4", "c5"}  # 3 Telegram configs
                                                        mock_deduplicate.return_value = ["f1", "f2", "f3", "f4"]  # 4 final configs
                                                        
                                                        # Run pipeline
                                                        await pipeline.run(mock_sources_file, mock_channels_file)
                                                        
                                                        # Verify stats
                                                        assert pipeline.stats["valid_sources"] == 3
                                                        assert pipeline.stats["fetched_configs"] == 5  # 2 + 3
                                                        assert pipeline.stats["written_configs"] == 4

    @pytest.mark.asyncio
    async def test_run_session_cleanup_on_exception(self, pipeline, mock_sources_file, mock_channels_file):
        """Test that session is properly closed even when exceptions occur."""
        with patch('streamline_vpn.merger.pipeline.choose_proxy'):
            with patch('streamline_vpn.merger.pipeline.aiohttp.TCPConnector'):
                with patch('streamline_vpn.merger.pipeline.aiohttp.ClientSession') as mock_session_class:
                    with patch('streamline_vpn.merger.pipeline.check_and_update_sources') as mock_check_sources:
                        with patch('streamline_vpn.merger.pipeline.deduplicate_and_filter') as mock_deduplicate:
                            with patch('streamline_vpn.merger.pipeline.output_files') as mock_output_files:
                                with patch('streamline_vpn.merger.pipeline.Path'):
                                    with patch('streamline_vpn.merger.pipeline.time.time'):
                                        with patch('streamline_vpn.merger.pipeline.logging'):
                                            with patch('builtins.print'):
                                                # Setup mocks
                                                mock_session = AsyncMock()
                                                mock_session_class.return_value = mock_session
                                                
                                                # Make check_and_update_sources raise an exception
                                                mock_check_sources.side_effect = Exception("Network error")
                                                
                                                mock_deduplicate.return_value = []
                                                mock_output_files.return_value = []
                                                
                                                # Run pipeline - should not raise exception
                                                await pipeline.run(mock_sources_file, mock_channels_file)
                                                
                                                # Verify session was closed despite exception
                                                mock_session.close.assert_called_once()


class TestRunPipeline:
    """Test cases for run_pipeline function."""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        return MagicMock()

    @pytest.fixture
    def mock_sources_file(self):
        """Create mock sources file path."""
        return MagicMock(spec=Path)

    @pytest.fixture
    def mock_channels_file(self):
        """Create mock channels file path."""
        return MagicMock(spec=Path)

    @pytest.mark.asyncio
    async def test_run_pipeline_function(self, mock_config, mock_sources_file, mock_channels_file):
        """Test run_pipeline function."""
        with patch('streamline_vpn.merger.pipeline.AggregationPipeline') as mock_pipeline_class:
            # Setup mock pipeline
            mock_pipeline = AsyncMock()
            mock_pipeline.run.return_value = (Path("/output"), [Path("file1.txt")])
            mock_pipeline_class.return_value = mock_pipeline
            
            # Call function
            result = await run_pipeline(
                mock_config,
                mock_sources_file,
                mock_channels_file,
                protocols=["vmess"],
                last_hours=12,
                failure_threshold=5,
                prune=False
            )
            
            # Verify pipeline was created and run
            mock_pipeline_class.assert_called_once_with(mock_config)
            mock_pipeline.run.assert_called_once_with(
                mock_sources_file,
                mock_channels_file,
                ["vmess"],
                12,
                failure_threshold=5,
                prune=False
            )
            
            # Verify result
            assert result == (Path("/output"), [Path("file1.txt")])

    @pytest.mark.asyncio
    async def test_run_pipeline_with_defaults(self, mock_config, mock_sources_file, mock_channels_file):
        """Test run_pipeline function with default parameters."""
        with patch('streamline_vpn.merger.pipeline.AggregationPipeline') as mock_pipeline_class:
            # Setup mock pipeline
            mock_pipeline = AsyncMock()
            mock_pipeline.run.return_value = (Path("/output"), [])
            mock_pipeline_class.return_value = mock_pipeline
            
            # Call function with minimal parameters
            result = await run_pipeline(mock_config, mock_sources_file, mock_channels_file)
            
            # Verify pipeline was created and run with defaults
            mock_pipeline_class.assert_called_once_with(mock_config)
            mock_pipeline.run.assert_called_once_with(
                mock_sources_file,
                mock_channels_file,
                None,  # Default protocols
                24,    # Default last_hours
                failure_threshold=3,  # Default failure_threshold
                prune=True  # Default prune
            )
            
            # Verify result
            assert result == (Path("/output"), [])


class TestAggregationPipelineEdgeCases:
    """Edge case tests for AggregationPipeline."""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        config = MagicMock()
        config.output_dir = "/test/output"
        config.concurrent_limit = 5
        config.request_timeout = 10
        config.retry_attempts = 2
        config.retry_base_delay = 0.5
        return config

    @pytest.fixture
    def pipeline(self, mock_config):
        """Create AggregationPipeline instance."""
        return AggregationPipeline(mock_config)

    @pytest.mark.asyncio
    async def test_run_with_empty_results(self, pipeline):
        """Test pipeline execution with empty results from all sources."""
        mock_sources_file = MagicMock(spec=Path)
        mock_channels_file = MagicMock(spec=Path)
        
        with patch('streamline_vpn.merger.pipeline.choose_proxy'):
            with patch('streamline_vpn.merger.pipeline.aiohttp.TCPConnector'):
                with patch('streamline_vpn.merger.pipeline.aiohttp.ClientSession') as mock_session_class:
                    with patch('streamline_vpn.merger.pipeline.check_and_update_sources') as mock_check_sources:
                        with patch('streamline_vpn.merger.pipeline.fetch_and_parse_configs') as mock_fetch_configs:
                            with patch('streamline_vpn.merger.pipeline.scrape_telegram_configs') as mock_scrape_telegram:
                                with patch('streamline_vpn.merger.pipeline.deduplicate_and_filter') as mock_deduplicate:
                                    with patch('streamline_vpn.merger.pipeline.output_files') as mock_output_files:
                                        with patch('streamline_vpn.merger.pipeline.Path'):
                                            with patch('streamline_vpn.merger.pipeline.time.time'):
                                                with patch('streamline_vpn.merger.pipeline.logging'):
                                                    with patch('builtins.print'):
                                                        # Setup mocks to return empty results
                                                        mock_session = AsyncMock()
                                                        mock_session_class.return_value = mock_session
                                                        
                                                        mock_check_sources.return_value = []  # No sources
                                                        mock_fetch_configs.return_value = set()  # No HTTP configs
                                                        mock_scrape_telegram.return_value = set()  # No Telegram configs
                                                        mock_deduplicate.return_value = []  # No final configs
                                                        mock_output_files.return_value = []  # No output files
                                                        
                                                        # Run pipeline
                                                        out_dir, files = await pipeline.run(mock_sources_file, mock_channels_file)
                                                        
                                                        # Verify stats are all zero
                                                        assert pipeline.stats["valid_sources"] == 0
                                                        assert pipeline.stats["fetched_configs"] == 0
                                                        assert pipeline.stats["written_configs"] == 0
                                                        
                                                        # Verify empty results
                                                        assert len(files) == 0

    @pytest.mark.asyncio
    async def test_run_with_no_proxy(self, pipeline):
        """Test pipeline execution with no proxy configured."""
        mock_sources_file = MagicMock(spec=Path)
        mock_channels_file = MagicMock(spec=Path)
        
        with patch('streamline_vpn.merger.pipeline.choose_proxy') as mock_choose_proxy:
            with patch('streamline_vpn.merger.pipeline.aiohttp.TCPConnector') as mock_connector:
                with patch('streamline_vpn.merger.pipeline.aiohttp.ClientSession') as mock_session_class:
                    with patch('streamline_vpn.merger.pipeline.check_and_update_sources') as mock_check_sources:
                        with patch('streamline_vpn.merger.pipeline.fetch_and_parse_configs'):
                            with patch('streamline_vpn.merger.pipeline.scrape_telegram_configs'):
                                with patch('streamline_vpn.merger.pipeline.deduplicate_and_filter'):
                                    with patch('streamline_vpn.merger.pipeline.output_files'):
                                        with patch('streamline_vpn.merger.pipeline.Path'):
                                            with patch('streamline_vpn.merger.pipeline.time.time'):
                                                with patch('streamline_vpn.merger.pipeline.logging'):
                                                    with patch('builtins.print'):
                                                        # Setup mocks
                                                        mock_choose_proxy.return_value = None  # No proxy
                                                        mock_connector_instance = MagicMock()
                                                        mock_connector.return_value = mock_connector_instance
                                                        mock_session = AsyncMock()
                                                        mock_session_class.return_value = mock_session
                                                        mock_check_sources.return_value = []
                                                        
                                                        # Run pipeline
                                                        await pipeline.run(mock_sources_file, mock_channels_file)
                                                        
                                                        # Verify session was created with None proxy
                                                        mock_session_class.assert_called_once_with(
                                                            connector=mock_connector_instance,
                                                            proxy=None
                                                        )
                                                        
                                                        # Verify functions were called with None proxy
                                                        call_args = mock_check_sources.call_args
                                                        assert call_args.kwargs['proxy'] is None

    @pytest.mark.asyncio
    async def test_run_timing_measurement(self, pipeline):
        """Test that pipeline correctly measures execution time."""
        mock_sources_file = MagicMock(spec=Path)
        mock_channels_file = MagicMock(spec=Path)
        
        with patch('streamline_vpn.merger.pipeline.choose_proxy'):
            with patch('streamline_vpn.merger.pipeline.aiohttp.TCPConnector'):
                with patch('streamline_vpn.merger.pipeline.aiohttp.ClientSession') as mock_session_class:
                    with patch('streamline_vpn.merger.pipeline.check_and_update_sources'):
                        with patch('streamline_vpn.merger.pipeline.fetch_and_parse_configs'):
                            with patch('streamline_vpn.merger.pipeline.scrape_telegram_configs'):
                                with patch('streamline_vpn.merger.pipeline.deduplicate_and_filter'):
                                    with patch('streamline_vpn.merger.pipeline.output_files'):
                                        with patch('streamline_vpn.merger.pipeline.Path'):
                                            with patch('streamline_vpn.merger.pipeline.time.time') as mock_time:
                                                with patch('streamline_vpn.merger.pipeline.logging') as mock_logging:
                                                    with patch('builtins.print') as mock_print:
                                                        # Setup mocks
                                                        mock_session = AsyncMock()
                                                        mock_session_class.return_value = mock_session
                                                        
                                                        # Mock time to return specific values
                                                        mock_time.side_effect = [100.0, 125.7]  # 25.7 second duration
                                                        
                                                        # Run pipeline
                                                        await pipeline.run(mock_sources_file, mock_channels_file)
                                                        
                                                        # Verify timing was measured and logged
                                                        assert mock_time.call_count == 2
                                                        
                                                        # Check that elapsed time was calculated and printed
                                                        mock_print.assert_called_once()
                                                        print_call_args = str(mock_print.call_args[0][0])
                                                        assert "Elapsed: 25.7s" in print_call_args
                                                        
                                                        # Check that summary was logged
                                                        mock_logging.info.assert_called()
                                                        log_calls = [str(call[0][0]) for call in mock_logging.info.call_args_list]
                                                        summary_logged = any("Elapsed: 25.7s" in call for call in log_calls)
                                                        assert summary_logged
