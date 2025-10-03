"""Simplified tests for merger pipeline module."""

import asyncio
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from streamline_vpn.merger.pipeline import AggregationPipeline, run_pipeline


class TestAggregationPipelineSimple:
    """Simplified test cases for AggregationPipeline."""

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

    def test_init(self, mock_config):
        """Test pipeline initialization."""
        pipeline = AggregationPipeline(mock_config)
        
        assert pipeline.cfg == mock_config
        assert pipeline.stats["valid_sources"] == 0
        assert pipeline.stats["fetched_configs"] == 0
        assert pipeline.stats["written_configs"] == 0

    @pytest.mark.asyncio
    async def test_run_basic_flow(self, pipeline):
        """Test basic pipeline execution flow."""
        mock_sources_file = MagicMock(spec=Path)
        mock_channels_file = MagicMock(spec=Path)
        
        with patch('streamline_vpn.merger.pipeline.choose_proxy', return_value=None):
            with patch('streamline_vpn.merger.pipeline.aiohttp.TCPConnector'):
                with patch('streamline_vpn.merger.pipeline.aiohttp.ClientSession') as mock_session_class:
                    with patch('streamline_vpn.merger.pipeline.check_and_update_sources', return_value=[]):
                        with patch('streamline_vpn.merger.pipeline.fetch_and_parse_configs', return_value=set()):
                            with patch('streamline_vpn.merger.pipeline.scrape_telegram_configs', return_value=set()):
                                with patch('streamline_vpn.merger.pipeline.deduplicate_and_filter', return_value=[]):
                                    with patch('streamline_vpn.merger.pipeline.output_files', return_value=[]):
                                        with patch('streamline_vpn.merger.pipeline.Path'):
                                            with patch('streamline_vpn.merger.pipeline.time.time', side_effect=[100.0, 105.0]):
                                                with patch('streamline_vpn.merger.pipeline.logging'):
                                                    with patch('builtins.print'):
                                                        # Setup session mock
                                                        mock_session = AsyncMock()
                                                        mock_session_class.return_value = mock_session
                                                        
                                                        # Run pipeline
                                                        out_dir, files = await pipeline.run(
                                                            mock_sources_file,
                                                            mock_channels_file
                                                        )
                                                        
                                                        # Verify session was closed
                                                        mock_session.close.assert_called_once()
                                                        
                                                        # Verify stats
                                                        assert pipeline.stats["valid_sources"] == 0
                                                        assert pipeline.stats["fetched_configs"] == 0
                                                        assert pipeline.stats["written_configs"] == 0

    @pytest.mark.asyncio
    async def test_run_with_keyboard_interrupt(self, pipeline):
        """Test pipeline execution with keyboard interrupt."""
        mock_sources_file = MagicMock(spec=Path)
        mock_channels_file = MagicMock(spec=Path)
        
        with patch('streamline_vpn.merger.pipeline.choose_proxy', return_value=None):
            with patch('streamline_vpn.merger.pipeline.aiohttp.TCPConnector'):
                with patch('streamline_vpn.merger.pipeline.aiohttp.ClientSession') as mock_session_class:
                    with patch('streamline_vpn.merger.pipeline.check_and_update_sources', side_effect=KeyboardInterrupt()):
                        with patch('streamline_vpn.merger.pipeline.deduplicate_and_filter', return_value=[]):
                            with patch('streamline_vpn.merger.pipeline.output_files', return_value=[]):
                                with patch('streamline_vpn.merger.pipeline.Path'):
                                    with patch('streamline_vpn.merger.pipeline.time.time', side_effect=[100.0, 105.0]):
                                        with patch('streamline_vpn.merger.pipeline.logging') as mock_logging:
                                            with patch('builtins.print'):
                                                # Setup session mock
                                                mock_session = AsyncMock()
                                                mock_session_class.return_value = mock_session
                                                
                                                # Run pipeline
                                                out_dir, files = await pipeline.run(
                                                    mock_sources_file,
                                                    mock_channels_file
                                                )
                                                
                                                # Verify warning was logged
                                                mock_logging.warning.assert_called_once_with(
                                                    "Interrupted. Writing partial results..."
                                                )
                                                
                                                # Verify session was closed
                                                mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_with_configs(self, pipeline):
        """Test pipeline execution with some configs."""
        mock_sources_file = MagicMock(spec=Path)
        mock_channels_file = MagicMock(spec=Path)
        
        with patch('streamline_vpn.merger.pipeline.choose_proxy', return_value=None):
            with patch('streamline_vpn.merger.pipeline.aiohttp.TCPConnector'):
                with patch('streamline_vpn.merger.pipeline.aiohttp.ClientSession') as mock_session_class:
                    with patch('streamline_vpn.merger.pipeline.check_and_update_sources', return_value=["source1", "source2"]):
                        with patch('streamline_vpn.merger.pipeline.fetch_and_parse_configs', return_value={"config1", "config2"}):
                            with patch('streamline_vpn.merger.pipeline.scrape_telegram_configs', return_value={"config3"}):
                                with patch('streamline_vpn.merger.pipeline.deduplicate_and_filter', return_value=["final1", "final2"]):
                                    with patch('streamline_vpn.merger.pipeline.output_files', return_value=[Path("output.txt")]):
                                        with patch('streamline_vpn.merger.pipeline.Path'):
                                            with patch('streamline_vpn.merger.pipeline.time.time', side_effect=[100.0, 105.0]):
                                                with patch('streamline_vpn.merger.pipeline.logging'):
                                                    with patch('builtins.print'):
                                                        # Setup session mock
                                                        mock_session = AsyncMock()
                                                        mock_session_class.return_value = mock_session
                                                        
                                                        # Run pipeline
                                                        out_dir, files = await pipeline.run(
                                                            mock_sources_file,
                                                            mock_channels_file
                                                        )
                                                        
                                                        # Verify stats
                                                        assert pipeline.stats["valid_sources"] == 2
                                                        assert pipeline.stats["fetched_configs"] == 3  # 2 HTTP + 1 Telegram
                                                        assert pipeline.stats["written_configs"] == 2
                                                        
                                                        # Verify results
                                                        assert len(files) == 1


class TestRunPipelineSimple:
    """Simplified test cases for run_pipeline function."""

    @pytest.mark.asyncio
    async def test_run_pipeline_function(self):
        """Test run_pipeline function."""
        mock_config = MagicMock()
        mock_sources_file = MagicMock(spec=Path)
        mock_channels_file = MagicMock(spec=Path)
        
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
    async def test_run_pipeline_with_defaults(self):
        """Test run_pipeline function with default parameters."""
        mock_config = MagicMock()
        mock_sources_file = MagicMock(spec=Path)
        mock_channels_file = MagicMock(spec=Path)
        
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
