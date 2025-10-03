"""Tests for merger source_manager module."""

import asyncio
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch, mock_open
from aiohttp import ClientSession

from streamline_vpn.merger.source_manager import (
    check_and_update_sources,
    fetch_and_parse_configs
)


class TestCheckAndUpdateSources:
    """Test cases for check_and_update_sources function."""

    @pytest.mark.asyncio
    async def test_check_and_update_sources_file_not_exists(self):
        """Test check_and_update_sources when file doesn't exist."""
        mock_path = MagicMock()
        mock_path.exists.return_value = False
        
        with patch('logging.warning') as mock_warning:
            result = await check_and_update_sources(mock_path)
            
            assert result == []
            mock_warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_and_update_sources_basic_flow(self):
        """Test basic check_and_update_sources flow."""
        # Mock path and file content
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.with_suffix.return_value = MagicMock()
        
        # Mock file content
        file_content = ["http://example1.com\n", "http://example2.com\n", "\n", "http://example1.com\n"]
        mock_file = MagicMock()
        mock_file.__enter__.return_value = file_content
        mock_path.open.return_value = mock_file
        
        # Mock failures file
        failures_path = mock_path.with_suffix.return_value
        failures_path.read_text.side_effect = FileNotFoundError()
        failures_path.write_text = MagicMock()
        
        # Mock fetch_text and parse_configs_from_text
        with patch('streamline_vpn.merger.source_manager.fetch_text') as mock_fetch:
            with patch('streamline_vpn.merger.source_manager.parse_configs_from_text') as mock_parse:
                with patch('aiohttp.ClientSession') as mock_session_class:
                    with patch('aiohttp.TCPConnector') as mock_connector:
                        # Mock file write operations
                        mock_write_file = MagicMock()
                        mock_path.open.side_effect = [mock_file, mock_write_file]
                        
                        mock_fetch.return_value = "config_data"
                        mock_parse.return_value = ["config1", "config2"]
                        
                        mock_session = AsyncMock()
                        mock_session_class.return_value.__aenter__.return_value = mock_session
                        
                        result = await check_and_update_sources(mock_path)
                        
                        # Should return valid sources (deduplicated)
                        assert len(result) == 2
                        assert "http://example1.com" in result
                        assert "http://example2.com" in result

    @pytest.mark.asyncio
    async def test_check_and_update_sources_with_failures(self):
        """Test check_and_update_sources with existing failures."""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        
        # Mock file content
        file_content = "http://example1.com\nhttp://example2.com\n"
        mock_path.open.return_value.__enter__.return_value = file_content.splitlines(keepends=True)
        
        # Mock failures file with existing failures
        failures_path = mock_path.with_suffix.return_value
        existing_failures = {"http://example2.com": 2}
        failures_path.read_text.return_value = json.dumps(existing_failures)
        failures_path.write_text = MagicMock()
        
        # Mock fetch_text - example1 succeeds, example2 fails
        with patch('streamline_vpn.merger.source_manager.fetch_text') as mock_fetch:
            with patch('streamline_vpn.merger.source_manager.parse_configs_from_text') as mock_parse:
                with patch('aiohttp.ClientSession') as mock_session_class:
                    with patch('aiohttp.TCPConnector'):
                        async def fetch_side_effect(session, url, *args, **kwargs):
                            if "example1" in url:
                                return "config_data"
                            return None
                        
                        def parse_side_effect(text):
                            if text:
                                return ["config1"]
                            return []
                        
                        mock_fetch.side_effect = fetch_side_effect
                        mock_parse.side_effect = parse_side_effect
                        
                        mock_session = AsyncMock()
                        mock_session_class.return_value.__aenter__.return_value = mock_session
                        
                        result = await check_and_update_sources(mock_path, max_failures=3)
                        
                        # Should only return successful source
                        assert len(result) == 1
                        assert "http://example1.com" in result

    @pytest.mark.asyncio
    async def test_check_and_update_sources_with_pruning(self):
        """Test check_and_update_sources with pruning enabled."""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        
        # Mock file content
        file_content = "http://example1.com\nhttp://example2.com\n"
        mock_path.open.return_value.__enter__.return_value = file_content.splitlines(keepends=True)
        
        # Mock failures file
        failures_path = mock_path.with_suffix.return_value
        existing_failures = {"http://example2.com": 2}  # Already has 2 failures
        failures_path.read_text.return_value = json.dumps(existing_failures)
        failures_path.write_text = MagicMock()
        
        # Mock file write for updating sources
        mock_write_file = mock_open()
        
        with patch('streamline_vpn.merger.source_manager.fetch_text') as mock_fetch:
            with patch('streamline_vpn.merger.source_manager.parse_configs_from_text') as mock_parse:
                with patch('aiohttp.ClientSession') as mock_session_class:
                    with patch('aiohttp.TCPConnector'):
                        with patch('builtins.open', mock_write_file):
                            # Both sources fail
                            mock_fetch.return_value = None
                            mock_parse.return_value = []
                            
                            mock_session = AsyncMock()
                            mock_session_class.return_value.__aenter__.return_value = mock_session
                            
                            result = await check_and_update_sources(
                                mock_path, 
                                max_failures=3, 
                                prune=True
                            )
                            
                            # Should return empty list as both sources failed
                            assert result == []

    @pytest.mark.asyncio
    async def test_check_and_update_sources_with_disabled_path(self):
        """Test check_and_update_sources with disabled_path logging."""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_disabled_path = MagicMock()
        
        # Mock file content
        file_content = "http://example1.com\n"
        mock_path.open.return_value.__enter__.return_value = file_content.splitlines(keepends=True)
        
        # Mock failures file
        failures_path = mock_path.with_suffix.return_value
        failures_path.read_text.side_effect = FileNotFoundError()
        failures_path.write_text = MagicMock()
        
        # Mock disabled file
        mock_disabled_file = mock_open()
        mock_disabled_path.open.return_value = mock_disabled_file.return_value
        
        with patch('streamline_vpn.merger.source_manager.fetch_text') as mock_fetch:
            with patch('streamline_vpn.merger.source_manager.parse_configs_from_text') as mock_parse:
                with patch('aiohttp.ClientSession') as mock_session_class:
                    with patch('aiohttp.TCPConnector'):
                        with patch('datetime.datetime') as mock_datetime:
                            mock_fetch.return_value = None
                            mock_parse.return_value = []
                            mock_datetime.utcnow.return_value.isoformat.return_value = "2023-01-01T00:00:00"
                            
                            mock_session = AsyncMock()
                            mock_session_class.return_value.__aenter__.return_value = mock_session
                            
                            result = await check_and_update_sources(
                                mock_path,
                                disabled_path=mock_disabled_path,
                                max_failures=1,
                                prune=True
                            )
                            
                            # Should log to disabled file
                            mock_disabled_path.open.assert_called_once_with("a")

    @pytest.mark.asyncio
    async def test_check_and_update_sources_with_external_session(self):
        """Test check_and_update_sources with external session."""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_session = AsyncMock()
        
        # Mock file content
        file_content = "http://example1.com\n"
        mock_path.open.return_value.__enter__.return_value = file_content.splitlines(keepends=True)
        
        # Mock failures file
        failures_path = mock_path.with_suffix.return_value
        failures_path.read_text.side_effect = FileNotFoundError()
        failures_path.write_text = MagicMock()
        
        with patch('streamline_vpn.merger.source_manager.fetch_text') as mock_fetch:
            with patch('streamline_vpn.merger.source_manager.parse_configs_from_text') as mock_parse:
                mock_fetch.return_value = "config_data"
                mock_parse.return_value = ["config1"]
                
                result = await check_and_update_sources(mock_path, session=mock_session)
                
                # Should use provided session
                assert len(result) == 1
                mock_fetch.assert_called_with(
                    mock_session,
                    "http://example1.com",
                    10,  # default timeout
                    retries=3,
                    base_delay=1.0,
                    proxy=None
                )

    @pytest.mark.asyncio
    async def test_check_and_update_sources_with_proxy(self):
        """Test check_and_update_sources with proxy."""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        
        # Mock file content
        file_content = "http://example1.com\n"
        mock_path.open.return_value.__enter__.return_value = file_content.splitlines(keepends=True)
        
        # Mock failures file
        failures_path = mock_path.with_suffix.return_value
        failures_path.read_text.side_effect = FileNotFoundError()
        failures_path.write_text = MagicMock()
        
        with patch('streamline_vpn.merger.source_manager.fetch_text') as mock_fetch:
            with patch('streamline_vpn.merger.source_manager.parse_configs_from_text') as mock_parse:
                with patch('aiohttp.ClientSession') as mock_session_class:
                    with patch('aiohttp.TCPConnector'):
                        mock_fetch.return_value = "config_data"
                        mock_parse.return_value = ["config1"]
                        
                        mock_session = AsyncMock()
                        mock_session_class.return_value.__aenter__.return_value = mock_session
                        
                        result = await check_and_update_sources(
                            mock_path, 
                            proxy="http://proxy:8080"
                        )
                        
                        # Should pass proxy to fetch_text
                        mock_fetch.assert_called_with(
                            mock_session,
                            "http://example1.com",
                            10,  # default timeout
                            retries=3,
                            base_delay=1.0,
                            proxy="http://proxy:8080"
                        )


class TestFetchAndParseConfigs:
    """Test cases for fetch_and_parse_configs function."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        settings = MagicMock()
        settings.shuffle_sources = False
        settings.concurrent_limit = 10
        settings.request_timeout = 30
        settings.retry_attempts = 3
        settings.retry_base_delay = 1.0
        settings.enable_url_testing = False
        return settings

    @pytest.mark.asyncio
    async def test_fetch_and_parse_configs_basic(self, mock_settings):
        """Test basic fetch_and_parse_configs functionality."""
        sources = ["http://example1.com", "http://example2.com"]
        
        with patch('streamline_vpn.merger.source_manager.fetch_text') as mock_fetch:
            with patch('streamline_vpn.merger.source_manager.parse_configs_from_text') as mock_parse:
                with patch('aiohttp.ClientSession') as mock_session_class:
                    with patch('aiohttp.TCPConnector'):
                        with patch('streamline_vpn.merger.source_manager.tqdm') as mock_tqdm:
                            mock_fetch.return_value = "config_data"
                            mock_parse.return_value = {"config1", "config2"}
                            
                            mock_session = AsyncMock()
                            mock_session_class.return_value.__aenter__.return_value = mock_session
                            mock_progress = MagicMock()
                            mock_tqdm.return_value = mock_progress
                            
                            result = await fetch_and_parse_configs(sources, mock_settings)
                            
                            # Should return combined configs from both sources
                            assert len(result) >= 2  # At least the configs we mocked
                            mock_progress.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_and_parse_configs_with_shuffle(self, mock_settings):
        """Test fetch_and_parse_configs with source shuffling."""
        mock_settings.shuffle_sources = True
        sources = ["http://example1.com", "http://example2.com"]
        
        with patch('random.shuffle') as mock_shuffle:
            with patch('streamline_vpn.merger.source_manager.fetch_text') as mock_fetch:
                with patch('streamline_vpn.merger.source_manager.parse_configs_from_text') as mock_parse:
                    with patch('aiohttp.ClientSession') as mock_session_class:
                        with patch('aiohttp.TCPConnector'):
                            with patch('streamline_vpn.merger.source_manager.tqdm'):
                                mock_fetch.return_value = "config_data"
                                mock_parse.return_value = {"config1"}
                                
                                mock_session = AsyncMock()
                                mock_session_class.return_value.__aenter__.return_value = mock_session
                                
                                await fetch_and_parse_configs(sources, mock_settings)
                                
                                # Should shuffle sources
                                mock_shuffle.assert_called_once_with(sources)

    @pytest.mark.asyncio
    async def test_fetch_and_parse_configs_with_external_session(self, mock_settings):
        """Test fetch_and_parse_configs with external session."""
        sources = ["http://example1.com"]
        mock_session = AsyncMock()
        
        with patch('streamline_vpn.merger.source_manager.fetch_text') as mock_fetch:
            with patch('streamline_vpn.merger.source_manager.parse_configs_from_text') as mock_parse:
                with patch('tqdm'):
                    mock_fetch.return_value = "config_data"
                    mock_parse.return_value = {"config1"}
                    
                    result = await fetch_and_parse_configs(
                        sources, 
                        mock_settings, 
                        session=mock_session
                    )
                    
                    # Should use provided session
                    mock_fetch.assert_called_with(
                        mock_session,
                        "http://example1.com",
                        mock_settings.request_timeout,
                        retries=mock_settings.retry_attempts,
                        base_delay=mock_settings.retry_base_delay,
                        proxy=None
                    )

    @pytest.mark.asyncio
    async def test_fetch_and_parse_configs_with_proxy(self, mock_settings):
        """Test fetch_and_parse_configs with proxy."""
        sources = ["http://example1.com"]
        
        with patch('streamline_vpn.merger.source_manager.fetch_text') as mock_fetch:
            with patch('streamline_vpn.merger.source_manager.parse_configs_from_text') as mock_parse:
                with patch('aiohttp.ClientSession') as mock_session_class:
                    with patch('aiohttp.TCPConnector'):
                        with patch('streamline_vpn.merger.source_manager.tqdm'):
                            mock_fetch.return_value = "config_data"
                            mock_parse.return_value = {"config1"}
                            
                            mock_session = AsyncMock()
                            mock_session_class.return_value.__aenter__.return_value = mock_session
                            
                            await fetch_and_parse_configs(
                                sources, 
                                mock_settings, 
                                proxy="http://proxy:8080"
                            )
                            
                            # Should pass proxy to fetch_text
                            mock_fetch.assert_called_with(
                                mock_session,
                                "http://example1.com",
                                mock_settings.request_timeout,
                                retries=mock_settings.retry_attempts,
                                base_delay=mock_settings.retry_base_delay,
                                proxy="http://proxy:8080"
                            )

    @pytest.mark.asyncio
    async def test_fetch_and_parse_configs_with_url_testing(self, mock_settings):
        """Test fetch_and_parse_configs with URL testing enabled."""
        mock_settings.enable_url_testing = True
        sources = ["http://example1.com", "http://example2.com"]
        
        with patch('streamline_vpn.merger.source_manager.fetch_text') as mock_fetch:
            with patch('streamline_vpn.merger.source_manager.parse_configs_from_text') as mock_parse:
                with patch('aiohttp.ClientSession') as mock_session_class:
                    with patch('aiohttp.TCPConnector'):
                        with patch('streamline_vpn.merger.source_manager.tqdm') as mock_tqdm:
                            mock_fetch.return_value = "config_data"
                            mock_parse.return_value = {"config1"}
                            
                            mock_session = AsyncMock()
                            mock_session_class.return_value.__aenter__.return_value = mock_session
                            mock_progress = MagicMock()
                            mock_tqdm.return_value = mock_progress
                            
                            await fetch_and_parse_configs(sources, mock_settings)
                            
                            # Should update progress for each source
                            assert mock_progress.update.call_count == len(sources)

    @pytest.mark.asyncio
    async def test_fetch_and_parse_configs_failed_fetch(self, mock_settings):
        """Test fetch_and_parse_configs with failed fetches."""
        sources = ["http://example1.com", "http://example2.com"]
        
        with patch('streamline_vpn.merger.source_manager.fetch_text') as mock_fetch:
            with patch('streamline_vpn.merger.source_manager.parse_configs_from_text') as mock_parse:
                with patch('aiohttp.ClientSession') as mock_session_class:
                    with patch('aiohttp.TCPConnector'):
                        with patch('streamline_vpn.merger.source_manager.tqdm'):
                            with patch('logging.warning') as mock_warning:
                                # First source fails, second succeeds
                                mock_fetch.side_effect = [None, "config_data"]
                                mock_parse.return_value = {"config1"}
                                
                                mock_session = AsyncMock()
                                mock_session_class.return_value.__aenter__.return_value = mock_session
                                
                                result = await fetch_and_parse_configs(sources, mock_settings)
                                
                                # Should log warning for failed fetch
                                mock_warning.assert_called()
                                # Should still return configs from successful source
                                assert len(result) >= 1

    @pytest.mark.asyncio
    async def test_fetch_and_parse_configs_empty_sources(self, mock_settings):
        """Test fetch_and_parse_configs with empty sources list."""
        sources = []
        
        with patch('tqdm') as mock_tqdm:
            mock_progress = MagicMock()
            mock_tqdm.return_value = mock_progress
            
            result = await fetch_and_parse_configs(sources, mock_settings)
            
            # Should return empty set
            assert result == set()
            mock_progress.close.assert_called_once()


class TestSourceManagerEdgeCases:
    """Edge case tests for source_manager module."""

    @pytest.mark.asyncio
    async def test_check_and_update_sources_json_decode_error(self):
        """Test check_and_update_sources with JSON decode error in failures file."""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        
        # Mock file content
        file_content = "http://example1.com\n"
        mock_path.open.return_value.__enter__.return_value = file_content.splitlines(keepends=True)
        
        # Mock failures file with invalid JSON
        failures_path = mock_path.with_suffix.return_value
        failures_path.read_text.return_value = "invalid json"
        failures_path.write_text = MagicMock()
        
        with patch('streamline_vpn.merger.source_manager.fetch_text') as mock_fetch:
            with patch('streamline_vpn.merger.source_manager.parse_configs_from_text') as mock_parse:
                with patch('aiohttp.ClientSession') as mock_session_class:
                    with patch('aiohttp.TCPConnector'):
                        with patch('logging.warning') as mock_warning:
                            mock_fetch.return_value = "config_data"
                            mock_parse.return_value = ["config1"]
                            
                            mock_session = AsyncMock()
                            mock_session_class.return_value.__aenter__.return_value = mock_session
                            
                            result = await check_and_update_sources(mock_path)
                            
                            # Should log warning and continue with empty failures dict
                            mock_warning.assert_called()
                            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_fetch_and_parse_configs_concurrent_limit(self):
        """Test fetch_and_parse_configs respects concurrent limit."""
        sources = ["http://example{}.com".format(i) for i in range(20)]
        mock_settings = MagicMock()
        mock_settings.shuffle_sources = False
        mock_settings.concurrent_limit = 5
        mock_settings.request_timeout = 30
        mock_settings.retry_attempts = 3
        mock_settings.retry_base_delay = 1.0
        mock_settings.enable_url_testing = False
        
        with patch('asyncio.Semaphore') as mock_semaphore:
            with patch('streamline_vpn.merger.source_manager.fetch_text') as mock_fetch:
                with patch('streamline_vpn.merger.source_manager.parse_configs_from_text') as mock_parse:
                    with patch('aiohttp.ClientSession') as mock_session_class:
                        with patch('aiohttp.TCPConnector'):
                            with patch('streamline_vpn.merger.source_manager.tqdm'):
                                mock_fetch.return_value = "config_data"
                                mock_parse.return_value = {"config1"}
                                
                                mock_session = AsyncMock()
                                mock_session_class.return_value.__aenter__.return_value = mock_session
                                
                                await fetch_and_parse_configs(sources, mock_settings)
                                
                                # Should create semaphore with concurrent_limit
                                mock_semaphore.assert_called_with(5)

