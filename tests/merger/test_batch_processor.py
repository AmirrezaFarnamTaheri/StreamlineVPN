"""Tests for merger batch_processor module."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import re

from streamline_vpn.merger.batch_processor import BatchProcessor


class TestBatchProcessor:
    """Test cases for BatchProcessor."""

    @pytest.fixture
    def mock_merger(self):
        """Create mock merger."""
        merger = MagicMock()
        merger.deduplicator = MagicMock()
        merger.deduplicator.include_regexes = []
        merger.deduplicator.exclude_regexes = []
        merger.all_results = []
        merger.last_processed_index = 0
        merger.saved_hashes = set()
        merger.cumulative_unique = []
        merger.last_saved_count = 0
        merger.batch_counter = 0
        merger.next_batch_threshold = 10
        merger.start_time = 0.0
        merger.available_sources = ["source1", "source2"]
        merger.sources = ["source1", "source2"]
        merger.stop_fetching = False
        merger.processor = MagicMock()
        merger.processor.create_semantic_hash = MagicMock(return_value="hash123")
        merger.analyzer = MagicMock()
        merger.analyzer.analyze = MagicMock(return_value={"total": 10})
        merger._sort_by_performance = MagicMock(side_effect=lambda x: x)
        merger._generate_comprehensive_outputs = AsyncMock()
        return merger

    @pytest.fixture
    def mock_config(self):
        """Mock CONFIG object."""
        with patch('streamline_vpn.merger.batch_processor.CONFIG') as mock_config:
            mock_config.save_every = 10
            mock_config.tls_fragment = None
            mock_config.include_protocols = None
            mock_config.exclude_protocols = None
            mock_config.enable_url_testing = False
            mock_config.strict_batch = False
            mock_config.cumulative_batches = False
            mock_config.enable_sorting = False
            mock_config.top_n = 0
            mock_config.stop_after_found = 0
            yield mock_config

    def test_init(self, mock_merger):
        """Test BatchProcessor initialization."""
        processor = BatchProcessor(mock_merger)
        
        assert processor.merger == mock_merger
        assert processor.include_regexes == mock_merger.deduplicator.include_regexes
        assert processor.exclude_regexes == mock_merger.deduplicator.exclude_regexes

    @pytest.mark.asyncio
    async def test_maybe_save_batch_save_every_zero(self, mock_merger, mock_config):
        """Test maybe_save_batch when save_every is 0."""
        mock_config.save_every = 0
        processor = BatchProcessor(mock_merger)
        
        await processor.maybe_save_batch()
        
        # Should return early without processing
        assert mock_merger.processor.create_semantic_hash.call_count == 0

    @pytest.mark.asyncio
    async def test_maybe_save_batch_no_new_results(self, mock_merger, mock_config):
        """Test maybe_save_batch with no new results."""
        processor = BatchProcessor(mock_merger)
        
        await processor.maybe_save_batch()
        
        # Should not process anything since no new results
        assert mock_merger.processor.create_semantic_hash.call_count == 0

    @pytest.mark.asyncio
    async def test_maybe_save_batch_with_new_results(self, mock_merger, mock_config):
        """Test maybe_save_batch with new results."""
        # Create mock results
        mock_result1 = MagicMock()
        mock_result1.config = "vmess://test1"
        mock_result1.protocol = "VMess"
        mock_result1.ping_time = 100
        
        mock_result2 = MagicMock()
        mock_result2.config = "vless://test2"
        mock_result2.protocol = "VLESS"
        mock_result2.ping_time = 200
        
        mock_merger.all_results = [mock_result1, mock_result2]
        mock_merger.last_processed_index = 0
        mock_merger.processor.create_semantic_hash.side_effect = lambda x: f"hash_{x}"
        
        processor = BatchProcessor(mock_merger)
        
        await processor.maybe_save_batch()
        
        # Should process both results
        assert mock_merger.processor.create_semantic_hash.call_count == 2
        # Results should be added to cumulative_unique (initially empty, so should have 2)
        assert len(mock_merger.cumulative_unique) == 2
        assert mock_merger.last_processed_index == 2

    @pytest.mark.asyncio
    async def test_maybe_save_batch_with_tls_fragment_filter(self, mock_merger, mock_config):
        """Test maybe_save_batch with TLS fragment filtering."""
        mock_config.tls_fragment = "tls"
        
        # Create mock results - one with TLS, one without
        mock_result1 = MagicMock()
        mock_result1.config = "vmess://test1?security=tls"
        mock_result1.protocol = "VMess"
        mock_result1.ping_time = 100
        
        mock_result2 = MagicMock()
        mock_result2.config = "vmess://test2?security=none"
        mock_result2.protocol = "VMess"
        mock_result2.ping_time = 200
        
        mock_merger.all_results = [mock_result1, mock_result2]
        mock_merger.last_processed_index = 0
        
        processor = BatchProcessor(mock_merger)
        
        await processor.maybe_save_batch()
        
        # Should only process the TLS result
        assert len(mock_merger.cumulative_unique) == 1
        assert mock_merger.cumulative_unique[0] == mock_result1

    @pytest.mark.asyncio
    async def test_maybe_save_batch_with_protocol_filters(self, mock_merger, mock_config):
        """Test maybe_save_batch with protocol filtering."""
        mock_config.include_protocols = ["VMESS"]
        mock_config.exclude_protocols = ["TROJAN"]
        
        # Create mock results with different protocols
        mock_result1 = MagicMock()
        mock_result1.config = "vmess://test1"
        mock_result1.protocol = "VMess"
        mock_result1.ping_time = 100
        
        mock_result2 = MagicMock()
        mock_result2.config = "vless://test2"
        mock_result2.protocol = "VLESS"
        mock_result2.ping_time = 200
        
        mock_result3 = MagicMock()
        mock_result3.config = "trojan://test3"
        mock_result3.protocol = "Trojan"
        mock_result3.ping_time = 300
        
        mock_merger.all_results = [mock_result1, mock_result2, mock_result3]
        mock_merger.last_processed_index = 0
        
        processor = BatchProcessor(mock_merger)
        
        await processor.maybe_save_batch()
        
        # Should only process VMess (included and not excluded)
        assert len(mock_merger.cumulative_unique) == 1
        assert mock_merger.cumulative_unique[0] == mock_result1

    @pytest.mark.asyncio
    async def test_maybe_save_batch_with_regex_filters(self, mock_merger, mock_config):
        """Test maybe_save_batch with regex filtering."""
        # Set up regex filters
        include_regex = re.compile(r"vmess://")
        exclude_regex = re.compile(r"blocked")
        
        processor = BatchProcessor(mock_merger)
        processor.include_regexes = [include_regex]
        processor.exclude_regexes = [exclude_regex]
        
        # Create mock results
        mock_result1 = MagicMock()
        mock_result1.config = "vmess://test1"
        mock_result1.protocol = "VMess"
        mock_result1.ping_time = 100
        
        mock_result2 = MagicMock()
        mock_result2.config = "vless://test2"
        mock_result2.protocol = "VLESS"
        mock_result2.ping_time = 200
        
        mock_result3 = MagicMock()
        mock_result3.config = "vmess://blocked-server"
        mock_result3.protocol = "VMess"
        mock_result3.ping_time = 300
        
        mock_merger.all_results = [mock_result1, mock_result2, mock_result3]
        mock_merger.last_processed_index = 0
        
        await processor.maybe_save_batch()
        
        # Should only process result1 (matches include, doesn't match exclude)
        assert len(mock_merger.cumulative_unique) == 1
        assert mock_merger.cumulative_unique[0] == mock_result1

    @pytest.mark.asyncio
    async def test_maybe_save_batch_with_url_testing(self, mock_merger, mock_config):
        """Test maybe_save_batch with URL testing enabled."""
        mock_config.enable_url_testing = True
        
        # Create mock results - one with ping_time, one without
        mock_result1 = MagicMock()
        mock_result1.config = "vmess://test1"
        mock_result1.protocol = "VMess"
        mock_result1.ping_time = 100
        
        mock_result2 = MagicMock()
        mock_result2.config = "vmess://test2"
        mock_result2.protocol = "VMess"
        mock_result2.ping_time = None
        
        mock_merger.all_results = [mock_result1, mock_result2]
        mock_merger.last_processed_index = 0
        
        processor = BatchProcessor(mock_merger)
        
        await processor.maybe_save_batch()
        
        # Should only process result with ping_time
        assert len(mock_merger.cumulative_unique) == 1
        assert mock_merger.cumulative_unique[0] == mock_result1

    @pytest.mark.asyncio
    async def test_maybe_save_batch_strict_batch_mode(self, mock_merger, mock_config):
        """Test maybe_save_batch in strict batch mode."""
        mock_config.strict_batch = True
        mock_config.save_every = 2
        mock_config.enable_sorting = True
        mock_config.top_n = 1
        
        # Create enough results to trigger batch processing
        results = []
        for i in range(3):
            result = MagicMock()
            result.config = f"vmess://test{i}"
            result.protocol = "VMess"
            result.ping_time = 100 + i
            results.append(result)
        
        mock_merger.all_results = results
        mock_merger.last_processed_index = 0
        mock_merger.processor.create_semantic_hash.side_effect = lambda x: f"hash{x[-1]}"
        
        processor = BatchProcessor(mock_merger)
        
        await processor.maybe_save_batch()
        
        # Should trigger batch processing
        assert mock_merger.batch_counter == 1
        assert mock_merger._generate_comprehensive_outputs.call_count == 2  # batch + cumulative

    @pytest.mark.asyncio
    async def test_maybe_save_batch_non_strict_batch_mode(self, mock_merger, mock_config):
        """Test maybe_save_batch in non-strict batch mode."""
        mock_config.strict_batch = False
        mock_config.save_every = 2
        mock_merger.next_batch_threshold = 2
        
        # Create enough results to trigger batch processing
        results = []
        for i in range(3):
            result = MagicMock()
            result.config = f"vmess://test{i}"
            result.protocol = "VMess"
            result.ping_time = 100 + i
            results.append(result)
        
        mock_merger.all_results = results
        mock_merger.last_processed_index = 0
        mock_merger.processor.create_semantic_hash.side_effect = lambda x: f"hash{x[-1]}"
        
        processor = BatchProcessor(mock_merger)
        
        await processor.maybe_save_batch()
        
        # Should trigger batch processing
        assert mock_merger.batch_counter == 1
        assert mock_merger.next_batch_threshold == 4  # increased by save_every

    @pytest.mark.asyncio
    async def test_maybe_save_batch_stop_after_found(self, mock_merger, mock_config):
        """Test maybe_save_batch with stop_after_found threshold."""
        mock_config.strict_batch = True
        mock_config.save_every = 1
        mock_config.stop_after_found = 2
        
        # Create enough results to trigger stop condition
        results = []
        for i in range(3):
            result = MagicMock()
            result.config = f"vmess://test{i}"
            result.protocol = "VMess"
            result.ping_time = 100 + i
            results.append(result)
        
        mock_merger.all_results = results
        mock_merger.last_processed_index = 0
        mock_merger.processor.create_semantic_hash.side_effect = lambda x: f"hash{x[-1]}"
        
        processor = BatchProcessor(mock_merger)
        
        await processor.maybe_save_batch()
        
        # Should set stop_fetching to True
        assert mock_merger.stop_fetching is True

    @pytest.mark.asyncio
    async def test_maybe_save_batch_cumulative_batches(self, mock_merger, mock_config):
        """Test maybe_save_batch with cumulative batches enabled."""
        mock_config.strict_batch = True
        mock_config.save_every = 2
        mock_config.cumulative_batches = True
        
        # Pre-populate some cumulative results
        mock_merger.cumulative_unique = [MagicMock(), MagicMock()]
        
        # Create new results
        results = []
        for i in range(3):
            result = MagicMock()
            result.config = f"vmess://test{i}"
            result.protocol = "VMess"
            result.ping_time = 100 + i
            results.append(result)
        
        mock_merger.all_results = results
        mock_merger.last_processed_index = 0
        mock_merger.processor.create_semantic_hash.side_effect = lambda x: f"hash{x[-1]}"
        
        processor = BatchProcessor(mock_merger)
        
        await processor.maybe_save_batch()
        
        # Should use cumulative results for batch
        assert mock_merger.batch_counter >= 1
        assert mock_merger.last_saved_count == len(mock_merger.cumulative_unique)

    @pytest.mark.asyncio
    async def test_maybe_save_batch_duplicate_hash_filtering(self, mock_merger, mock_config):
        """Test maybe_save_batch filters duplicate hashes."""
        # Create results with same hash
        mock_result1 = MagicMock()
        mock_result1.config = "vmess://test1"
        mock_result1.protocol = "VMess"
        mock_result1.ping_time = 100
        
        mock_result2 = MagicMock()
        mock_result2.config = "vmess://test2"
        mock_result2.protocol = "VMess"
        mock_result2.ping_time = 200
        
        mock_merger.all_results = [mock_result1, mock_result2]
        mock_merger.last_processed_index = 0
        mock_merger.processor.create_semantic_hash.return_value = "same_hash"
        
        processor = BatchProcessor(mock_merger)
        
        await processor.maybe_save_batch()
        
        # Should only add one result due to duplicate hash
        assert len(mock_merger.cumulative_unique) == 1
        assert "same_hash" in mock_merger.saved_hashes


class TestBatchProcessorEdgeCases:
    """Edge case tests for BatchProcessor."""

    @pytest.fixture
    def mock_merger(self):
        """Create mock merger."""
        merger = MagicMock()
        merger.deduplicator = MagicMock()
        merger.deduplicator.include_regexes = []
        merger.deduplicator.exclude_regexes = []
        merger.all_results = []
        merger.last_processed_index = 0
        merger.saved_hashes = set()
        merger.cumulative_unique = []
        merger.last_saved_count = 0
        merger.batch_counter = 0
        merger.next_batch_threshold = 10
        merger.start_time = 0.0
        merger.available_sources = []
        merger.sources = []
        merger.stop_fetching = False
        merger.processor = MagicMock()
        merger.analyzer = MagicMock()
        merger._sort_by_performance = MagicMock(side_effect=lambda x: x)
        merger._generate_comprehensive_outputs = AsyncMock()
        return merger

    @pytest.fixture
    def mock_config(self):
        """Mock CONFIG object."""
        with patch('streamline_vpn.merger.batch_processor.CONFIG') as mock_config:
            mock_config.save_every = 10
            mock_config.tls_fragment = None
            mock_config.include_protocols = None
            mock_config.exclude_protocols = None
            mock_config.enable_url_testing = False
            mock_config.strict_batch = False
            mock_config.cumulative_batches = False
            mock_config.enable_sorting = False
            mock_config.top_n = 0
            mock_config.stop_after_found = 0
            yield mock_config

    @pytest.mark.asyncio
    async def test_maybe_save_batch_empty_regex_lists(self, mock_merger, mock_config):
        """Test maybe_save_batch with empty regex lists."""
        processor = BatchProcessor(mock_merger)
        processor.include_regexes = []
        processor.exclude_regexes = []
        
        # Create mock result
        mock_result = MagicMock()
        mock_result.config = "vmess://test"
        mock_result.protocol = "VMess"
        mock_result.ping_time = 100
        
        mock_merger.all_results = [mock_result]
        mock_merger.last_processed_index = 0
        mock_merger.processor.create_semantic_hash.return_value = "hash123"
        
        await processor.maybe_save_batch()
        
        # Should process the result normally
        assert len(mock_merger.cumulative_unique) == 1

    @pytest.mark.asyncio
    async def test_maybe_save_batch_negative_save_every(self, mock_merger, mock_config):
        """Test maybe_save_batch with negative save_every."""
        mock_config.save_every = -1
        processor = BatchProcessor(mock_merger)
        
        await processor.maybe_save_batch()
        
        # Should return early
        assert mock_merger.processor.create_semantic_hash.call_count == 0

