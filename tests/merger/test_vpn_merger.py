import pytest
from unittest.mock import patch, MagicMock, ANY, AsyncMock

from streamline_vpn.merger.vpn_merger import UltimateVPNMerger

# Since CONFIG is imported and used at the module level, we need to patch it early.
# We'll do this by mocking the config object from the correct module.
@pytest.fixture(autouse=True)
def mock_merger_config():
    """Mocks the global CONFIG object for the merger module."""
    with patch('streamline_vpn.merger.vpn_merger.CONFIG') as mock_config:
        mock_config.shuffle_sources = False
        mock_config.history_file = 'history.json'
        mock_config.output_dir = 'output'
        mock_config.save_every = 1000
        mock_config.resume_file = None
        mock_config.enable_url_testing = False
        mock_config.enable_sorting = False
        mock_config.top_n = 0
        mock_config.max_ping_ms = None
        # Add any other required config attributes here
        yield mock_config

@pytest.fixture
def mock_dependencies():
    """Provides a fixture with mocked dependencies for UltimateVPNMerger."""
    with patch('streamline_vpn.merger.vpn_merger.UnifiedSources') as mock_sources, \
         patch('streamline_vpn.merger.vpn_merger.EnhancedConfigProcessor', autospec=True) as mock_processor, \
         patch('streamline_vpn.merger.vpn_merger.AsyncSourceFetcher', autospec=True) as mock_fetcher, \
         patch('streamline_vpn.merger.vpn_merger.Deduplicator', autospec=True) as mock_deduplicator, \
         patch('streamline_vpn.merger.vpn_merger.Sorter', autospec=True) as mock_sorter, \
         patch('streamline_vpn.merger.vpn_merger.Analyzer', autospec=True) as mock_analyzer, \
         patch('streamline_vpn.merger.vpn_merger.BatchProcessor', autospec=True) as mock_batch_processor, \
         patch('streamline_vpn.merger.vpn_merger.Path') as mock_path, \
         patch('streamline_vpn.merger.vpn_merger.SourceTester', autospec=True) as mock_source_tester, \
         patch('streamline_vpn.merger.vpn_merger.tqdm', autospec=True) as mock_tqdm:

        mock_sources.get_all_sources.return_value = ["http://source1.com"]
        mock_path.return_value.read_text.return_value = "{}"  # for proxy_history
        mock_path.return_value.is_absolute.return_value = True

        # Mock the instance of SourceTester, not the class
        mock_source_tester_instance = mock_source_tester.return_value
        mock_source_tester_instance.test_and_filter_sources = AsyncMock(return_value=["http://source1.com"])
        mock_source_tester_instance.preflight_connectivity_check = AsyncMock(return_value=True)

        # Fix for the autospec issue: create the 'tester' attribute on the mock processor instance
        processor_instance = mock_processor.return_value
        processor_instance.tester = MagicMock()
        processor_instance.tester.close = AsyncMock()

        yield {
            "sources": mock_sources,
            "processor": mock_processor,
            "fetcher": mock_fetcher,
            "deduplicator": mock_deduplicator,
            "sorter": mock_sorter,
            "analyzer": mock_analyzer,
            "batch_processor": mock_batch_processor,
            "path": mock_path,
            "source_tester": mock_source_tester,
            "tqdm": mock_tqdm,
        }

class TestUltimateVPNMerger:
    """Tests for the UltimateVPNMerger class."""

    def test_init(self, mock_dependencies):
        """Test the initialization of UltimateVPNMerger."""
        merger = UltimateVPNMerger(sources_file="dummy_sources.txt")

        # Assertions
        mock_dependencies["sources"].get_all_sources.assert_called_once_with("dummy_sources.txt")
        mock_dependencies["processor"].assert_called_once()
        mock_dependencies["fetcher"].assert_called_once()
        mock_dependencies["deduplicator"].assert_called_once()
        mock_dependencies["sorter"].assert_called_once()
        mock_dependencies["analyzer"].assert_called_once()
        mock_dependencies["batch_processor"].assert_called_once_with(merger)

        assert merger.sources == ["http://source1.com"]
        assert not merger.stop_fetching
        assert merger.all_results == []
        assert merger.proxy_history == {}

    @pytest.mark.asyncio
    async def test_run_happy_path(self, mock_dependencies, mock_merger_config):
        """Test a successful run of the merger process (happy path)."""
        # --- Setup ---
        merger = UltimateVPNMerger(sources_file="dummy_sources.txt")

        # Configure mock return values
        mock_dependencies["deduplicator"].return_value.deduplicate.return_value = [MagicMock()]
        mock_dependencies["sorter"].return_value.sort_by_performance.return_value = [MagicMock()]
        mock_dependencies["analyzer"].return_value.analyze.return_value = {"reachable_configs": 1, "protocol_stats": {"VLESS": 1}, "total_sources": 1, "available_sources": 1}

        # Mock the async methods on the fetcher instance
        fetcher_instance = mock_dependencies["fetcher"].return_value
        fetcher_instance.fetch_all_sources = AsyncMock()

        # Mock the processor's tester to avoid real network calls
        processor_instance = mock_dependencies["processor"].return_value

        # Mock the output generation
        with patch.object(merger, '_generate_comprehensive_outputs', new_callable=AsyncMock) as mock_generate_outputs, \
             patch.object(merger, '_save_proxy_history', new_callable=AsyncMock) as mock_save_history:

            # --- Execute ---
            await merger.run()

            # --- Assert ---
            # Step 1: Test sources
            mock_dependencies["source_tester"].return_value.test_and_filter_sources.assert_called_once()

            # Step 2: Fetch sources
            fetcher_instance.fetch_all_sources.assert_called_once()

            # Step 3: Deduplicate
            mock_dependencies["deduplicator"].return_value.deduplicate.assert_called_once()

            # Step 4: Sort (skipped in this test as enable_sorting is False)
            mock_dependencies["sorter"].return_value.sort_by_performance.assert_not_called()

            # Step 5: Analyze
            mock_dependencies["analyzer"].return_value.analyze.assert_called_once()

            # Step 6: Generate outputs
            mock_generate_outputs.assert_called_once()

            # Finalization
            mock_save_history.assert_called_once()
            processor_instance.tester.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_with_sorting_enabled(self, mock_dependencies, mock_merger_config):
        """Test a run where sorting is enabled."""
        mock_merger_config.enable_sorting = True

        merger = UltimateVPNMerger(sources_file="dummy_sources.txt")

        # Mock dependencies to return non-empty lists to ensure sorting is called
        mock_dependencies["deduplicator"].return_value.deduplicate.return_value = [MagicMock()]
        sorter_instance = mock_dependencies["sorter"].return_value
        sorter_instance.sort_by_performance.return_value = [MagicMock()]
        # Configure the analyzer mock to prevent TypeError during string formatting
        mock_dependencies["analyzer"].return_value.analyze.return_value = {
            "reachable_configs": 1,
            "protocol_stats": {"VLESS": 1},
            "total_sources": 1,
            "available_sources": 1
        }

        # Mock other methods that are part of the run sequence
        with patch.object(merger, '_generate_comprehensive_outputs', new_callable=AsyncMock), \
             patch.object(merger, '_save_proxy_history', new_callable=AsyncMock), \
             patch.object(merger.fetcher, 'fetch_all_sources', new_callable=AsyncMock):

            await merger.run()

            sorter_instance.sort_by_performance.assert_called_once()
