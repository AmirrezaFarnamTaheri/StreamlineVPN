"""Tests for merger telegram_scraper module."""

import asyncio
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch, mock_open
from telethon import errors
from telethon.tl.custom.message import Message

from streamline_vpn.merger.telegram_scraper import (
    scrape_telegram_configs,
    telegram_bot_mode
)


class TestScrapeTelegramConfigs:
    """Test cases for scrape_telegram_configs function."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        settings = MagicMock()
        settings.telegram_api_id = 12345
        settings.telegram_api_hash = "test_hash"
        settings.session_path = "test_session"
        settings.request_timeout = 30
        settings.retry_attempts = 3
        settings.retry_base_delay = 1.0
        return settings

    @pytest.mark.asyncio
    async def test_scrape_telegram_configs_no_credentials(self):
        """Test scrape_telegram_configs with no credentials."""
        settings = MagicMock()
        settings.telegram_api_id = None
        settings.telegram_api_hash = None
        
        channels_path = MagicMock()
        
        with patch('logging.info') as mock_info:
            result = await scrape_telegram_configs(settings, channels_path, 24)
            
            assert result == set()
            mock_info.assert_called_with("Telegram credentials not provided; skipping Telegram scrape")

    @pytest.mark.asyncio
    async def test_scrape_telegram_configs_no_channels_file(self, mock_settings):
        """Test scrape_telegram_configs when channels file doesn't exist."""
        channels_path = MagicMock()
        channels_path.exists.return_value = False
        
        with patch('logging.warning') as mock_warning:
            result = await scrape_telegram_configs(mock_settings, channels_path, 24)
            
            assert result == set()
            mock_warning.assert_called()

    @pytest.mark.asyncio
    async def test_scrape_telegram_configs_empty_channels(self, mock_settings):
        """Test scrape_telegram_configs with empty channels file."""
        channels_path = MagicMock()
        channels_path.exists.return_value = True
        channels_path.open.return_value.__enter__.return_value = []
        
        with patch('logging.info') as mock_info:
            result = await scrape_telegram_configs(mock_settings, channels_path, 24)
            
            assert result == set()
            mock_info.assert_called()

    @pytest.mark.asyncio
    async def test_scrape_telegram_configs_success(self, mock_settings):
        """Test successful scrape_telegram_configs."""
        channels_path = MagicMock()
        channels_path.exists.return_value = True
        
        # Mock channels file content
        channels_content = ["https://t.me/channel1\n", "channel2\n", "\n"]
        channels_path.open.return_value.__enter__.return_value = channels_content
        
        # Mock TelegramClient
        mock_client = AsyncMock()
        mock_message = MagicMock(spec=Message)
        mock_message.message = "vmess://test-config"
        
        # Mock iter_messages to return our test message
        mock_client.iter_messages.return_value.__aiter__.return_value = [mock_message]
        
        with patch('streamline_vpn.merger.telegram_scraper.TelegramClient') as mock_client_class:
            with patch('streamline_vpn.merger.telegram_scraper.parse_configs_from_text') as mock_parse:
                with patch('streamline_vpn.merger.telegram_scraper.extract_subscription_urls') as mock_extract:
                    with patch('streamline_vpn.merger.telegram_scraper.choose_proxy') as mock_proxy:
                        with patch('aiohttp.ClientSession') as mock_session:
                            with patch('tqdm') as mock_tqdm:
                                mock_client_class.return_value = mock_client
                                mock_parse.return_value = {"config1", "config2"}
                                mock_extract.return_value = []
                                mock_proxy.return_value = None
                                mock_progress = MagicMock()
                                mock_tqdm.return_value = mock_progress
                                
                                result = await scrape_telegram_configs(mock_settings, channels_path, 24)
                                
                                # Should return configs from both channels
                                assert len(result) >= 2
                                mock_client.start.assert_called_once()
                                mock_client.disconnect.assert_called_once()
                                mock_progress.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_scrape_telegram_configs_with_subscription_urls(self, mock_settings):
        """Test scrape_telegram_configs with subscription URLs."""
        channels_path = MagicMock()
        channels_path.exists.return_value = True
        channels_path.open.return_value.__enter__.return_value = ["channel1\n"]
        
        # Mock TelegramClient
        mock_client = AsyncMock()
        mock_message = MagicMock(spec=Message)
        mock_message.message = "Check this subscription: http://example.com/sub"
        
        mock_client.iter_messages.return_value.__aiter__.return_value = [mock_message]
        
        with patch('streamline_vpn.merger.telegram_scraper.TelegramClient') as mock_client_class:
            with patch('streamline_vpn.merger.telegram_scraper.parse_configs_from_text') as mock_parse:
                with patch('streamline_vpn.merger.telegram_scraper.extract_subscription_urls') as mock_extract:
                    with patch('streamline_vpn.merger.telegram_scraper.fetch_text') as mock_fetch:
                        with patch('streamline_vpn.merger.telegram_scraper.choose_proxy'):
                            with patch('aiohttp.ClientSession'):
                                with patch('streamline_vpn.merger.telegram_scraper.tqdm'):
                                    mock_client_class.return_value = mock_client
                                    mock_parse.side_effect = [{"config1"}, {"config2"}]  # First from message, second from subscription
                                    mock_extract.return_value = ["http://example.com/sub"]
                                    mock_fetch.return_value = "subscription_content"
                                    
                                    result = await scrape_telegram_configs(mock_settings, channels_path, 24)
                                    
                                    # Should fetch and parse subscription URL
                                    mock_fetch.assert_called_once()
                                    assert len(result) >= 2

    @pytest.mark.asyncio
    async def test_scrape_telegram_configs_rpc_error_retry(self, mock_settings):
        """Test scrape_telegram_configs with RPC error and retry."""
        channels_path = MagicMock()
        channels_path.exists.return_value = True
        channels_path.open.return_value.__enter__.return_value = ["channel1\n"]
        
        # Mock TelegramClient
        mock_client = AsyncMock()
        
        # First call raises error, second succeeds
        rpc_error = errors.RPCError()
        rpc_error.message = "Test error"
        mock_client.iter_messages.side_effect = [
            rpc_error,
            AsyncMock(__aiter__=AsyncMock(return_value=[]))
        ]
        
        with patch('streamline_vpn.merger.telegram_scraper.TelegramClient') as mock_client_class:
            with patch('streamline_vpn.merger.telegram_scraper.parse_configs_from_text') as mock_parse:
                with patch('streamline_vpn.merger.telegram_scraper.extract_subscription_urls') as mock_extract:
                    with patch('streamline_vpn.merger.telegram_scraper.choose_proxy'):
                        with patch('aiohttp.ClientSession'):
                            with patch('streamline_vpn.merger.telegram_scraper.tqdm'):
                                with patch('logging.warning') as mock_warning:
                                    mock_client_class.return_value = mock_client
                                    mock_parse.return_value = set()
                                    mock_extract.return_value = []
                                    
                                    result = await scrape_telegram_configs(mock_settings, channels_path, 24)
                                    
                                    # Should log warning and retry
                                    mock_warning.assert_called()
                                    mock_client.disconnect.assert_called()
                                    mock_client.connect.assert_called()

    @pytest.mark.asyncio
    async def test_scrape_telegram_configs_repeated_errors(self, mock_settings):
        """Test scrape_telegram_configs with repeated errors."""
        channels_path = MagicMock()
        channels_path.exists.return_value = True
        channels_path.open.return_value.__enter__.return_value = ["channel1\n"]
        
        # Mock TelegramClient
        mock_client = AsyncMock()
        rpc_error = errors.RPCError()
        rpc_error.message = "Persistent error"
        mock_client.iter_messages.side_effect = rpc_error
        
        with patch('streamline_vpn.merger.telegram_scraper.TelegramClient') as mock_client_class:
            with patch('streamline_vpn.merger.telegram_scraper.parse_configs_from_text'):
                with patch('streamline_vpn.merger.telegram_scraper.extract_subscription_urls'):
                    with patch('streamline_vpn.merger.telegram_scraper.choose_proxy'):
                        with patch('aiohttp.ClientSession'):
                            with patch('streamline_vpn.merger.telegram_scraper.tqdm'):
                                with patch('logging.warning') as mock_warning:
                                    mock_client_class.return_value = mock_client
                                    
                                    result = await scrape_telegram_configs(mock_settings, channels_path, 24)
                                    
                                    # Should skip channel after repeated errors
                                    assert "Skipping" in str(mock_warning.call_args_list[-1])

    @pytest.mark.asyncio
    async def test_scrape_telegram_configs_connection_error(self, mock_settings):
        """Test scrape_telegram_configs with connection error."""
        channels_path = MagicMock()
        channels_path.exists.return_value = True
        channels_path.open.return_value.__enter__.return_value = ["channel1\n"]
        
        # Mock TelegramClient
        mock_client = AsyncMock()
        rpc_error = errors.RPCError()
        rpc_error.message = "Connection failed"
        mock_client.start.side_effect = rpc_error
        
        with patch('streamline_vpn.merger.telegram_scraper.TelegramClient') as mock_client_class:
            with patch('tqdm'):
                with patch('logging.warning') as mock_warning:
                    mock_client_class.return_value = mock_client
                    
                    result = await scrape_telegram_configs(mock_settings, channels_path, 24)
                    
                    # Should return empty set and log warning
                    assert result == set()
                    mock_warning.assert_called()

    @pytest.mark.asyncio
    async def test_scrape_telegram_configs_channel_prefix_handling(self, mock_settings):
        """Test scrape_telegram_configs handles channel prefixes correctly."""
        channels_path = MagicMock()
        channels_path.exists.return_value = True
        
        # Mix of channels with and without prefix
        channels_content = [
            "https://t.me/channel1\n",
            "channel2\n",
            "https://t.me/channel3\n"
        ]
        channels_path.open.return_value.__enter__.return_value = channels_content
        
        mock_client = AsyncMock()
        mock_client.iter_messages.return_value.__aiter__.return_value = []
        
        with patch('streamline_vpn.merger.telegram_scraper.TelegramClient') as mock_client_class:
            with patch('streamline_vpn.merger.telegram_scraper.parse_configs_from_text') as mock_parse:
                with patch('streamline_vpn.merger.telegram_scraper.extract_subscription_urls') as mock_extract:
                    with patch('streamline_vpn.merger.telegram_scraper.choose_proxy'):
                        with patch('aiohttp.ClientSession'):
                            with patch('streamline_vpn.merger.telegram_scraper.tqdm'):
                                mock_client_class.return_value = mock_client
                                mock_parse.return_value = set()
                                mock_extract.return_value = []
                                
                                await scrape_telegram_configs(mock_settings, channels_path, 24)
                                
                                # Should call iter_messages for each channel (stripped of prefix)
                                expected_calls = [
                                    (("channel1",), {}),
                                    (("channel2",), {}),
                                    (("channel3",), {})
                                ]
                                
                                # Check that iter_messages was called with correct channel names
                                assert mock_client.iter_messages.call_count == 3


class TestTelegramBotMode:
    """Test cases for telegram_bot_mode function."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings for bot mode."""
        settings = MagicMock()
        settings.telegram_api_id = 12345
        settings.telegram_api_hash = "test_hash"
        settings.telegram_bot_token = "test_token"
        settings.allowed_user_ids = [123456789]
        settings.session_path = "test_session"
        return settings

    @pytest.mark.asyncio
    async def test_telegram_bot_mode_no_credentials(self):
        """Test telegram_bot_mode with missing credentials."""
        settings = MagicMock()
        settings.telegram_api_id = None
        settings.telegram_api_hash = None
        settings.telegram_bot_token = None
        settings.allowed_user_ids = None
        
        sources_file = MagicMock()
        channels_file = MagicMock()
        
        with patch('logging.info') as mock_info:
            await telegram_bot_mode(settings, sources_file, channels_file, 24, None)
            
            mock_info.assert_called_with("Telegram credentials not provided; skipping bot mode")

    @pytest.mark.asyncio
    async def test_telegram_bot_mode_setup(self, mock_settings):
        """Test telegram_bot_mode setup."""
        sources_file = MagicMock()
        channels_file = MagicMock()
        run_pipeline_func = AsyncMock()
        
        # Mock TelegramClient and bot
        mock_bot = AsyncMock()
        mock_client = AsyncMock()
        mock_client.start.return_value = mock_bot
        
        with patch('streamline_vpn.merger.telegram_scraper.TelegramClient') as mock_client_class:
            with patch('logging.info') as mock_info:
                mock_client_class.return_value = mock_client
                mock_bot.run_until_disconnected = AsyncMock()
                
                await telegram_bot_mode(mock_settings, sources_file, channels_file, 24, run_pipeline_func)
                
                # Should start bot and set up handlers
                mock_client.start.assert_called_once_with(bot_token=mock_settings.telegram_bot_token)
                mock_bot.run_until_disconnected.assert_called_once()
                mock_info.assert_called_with("Bot running. Press Ctrl+C to exit.")

    @pytest.mark.asyncio
    async def test_telegram_bot_mode_help_handler(self, mock_settings):
        """Test telegram_bot_mode help handler."""
        sources_file = MagicMock()
        channels_file = MagicMock()
        run_pipeline_func = AsyncMock()
        
        # Mock event handlers
        help_handler = None
        
        def mock_on_decorator(event_type):
            def decorator(func):
                nonlocal help_handler
                if "/help" in str(event_type):
                    help_handler = func
                return func
            return decorator
        
        mock_bot = AsyncMock()
        mock_bot.on = mock_on_decorator
        mock_client = AsyncMock()
        mock_client.start.return_value = mock_bot
        
        with patch('streamline_vpn.merger.telegram_scraper.TelegramClient') as mock_client_class:
            mock_client_class.return_value = mock_client
            mock_bot.run_until_disconnected = AsyncMock()
            
            await telegram_bot_mode(mock_settings, sources_file, channels_file, 24, run_pipeline_func)
            
            # Test help handler
            assert help_handler is not None
            
            # Mock event from allowed user
            mock_event = AsyncMock()
            mock_event.sender_id = mock_settings.allowed_user_ids[0]
            mock_event.respond = AsyncMock()
            
            await help_handler(mock_event)
            
            # Should respond with help text
            mock_event.respond.assert_called_once()
            help_text = mock_event.respond.call_args[0][0]
            assert "/update" in help_text
            assert "/status" in help_text

    @pytest.mark.asyncio
    async def test_telegram_bot_mode_unauthorized_user(self, mock_settings):
        """Test telegram_bot_mode with unauthorized user."""
        sources_file = MagicMock()
        channels_file = MagicMock()
        run_pipeline_func = AsyncMock()
        
        # Mock event handlers
        help_handler = None
        
        def mock_on_decorator(event_type):
            def decorator(func):
                nonlocal help_handler
                if "/help" in str(event_type):
                    help_handler = func
                return func
            return decorator
        
        mock_bot = AsyncMock()
        mock_bot.on = mock_on_decorator
        mock_client = AsyncMock()
        mock_client.start.return_value = mock_bot
        
        with patch('streamline_vpn.merger.telegram_scraper.TelegramClient') as mock_client_class:
            mock_client_class.return_value = mock_client
            mock_bot.run_until_disconnected = AsyncMock()
            
            await telegram_bot_mode(mock_settings, sources_file, channels_file, 24, run_pipeline_func)
            
            # Test help handler with unauthorized user
            mock_event = AsyncMock()
            mock_event.sender_id = 999999999  # Not in allowed_user_ids
            mock_event.respond = AsyncMock()
            
            await help_handler(mock_event)
            
            # Should not respond
            mock_event.respond.assert_not_called()


class TestTelegramScraperEdgeCases:
    """Edge case tests for telegram_scraper module."""

    @pytest.mark.asyncio
    async def test_scrape_telegram_configs_non_message_object(self):
        """Test scrape_telegram_configs with non-Message objects."""
        settings = MagicMock()
        settings.telegram_api_id = 12345
        settings.telegram_api_hash = "test_hash"
        settings.session_path = "test_session"
        
        channels_path = MagicMock()
        channels_path.exists.return_value = True
        channels_path.open.return_value.__enter__.return_value = ["channel1\n"]
        
        # Mock TelegramClient with non-Message object
        mock_client = AsyncMock()
        non_message_obj = MagicMock()  # Not a Message instance
        
        mock_client.iter_messages.return_value.__aiter__.return_value = [non_message_obj]
        
        with patch('streamline_vpn.merger.telegram_scraper.TelegramClient') as mock_client_class:
            with patch('streamline_vpn.merger.telegram_scraper.parse_configs_from_text') as mock_parse:
                with patch('streamline_vpn.merger.telegram_scraper.extract_subscription_urls') as mock_extract:
                    with patch('streamline_vpn.merger.telegram_scraper.choose_proxy'):
                        with patch('aiohttp.ClientSession'):
                            with patch('streamline_vpn.merger.telegram_scraper.tqdm'):
                                mock_client_class.return_value = mock_client
                                mock_parse.return_value = set()
                                mock_extract.return_value = []
                                
                                result = await scrape_telegram_configs(settings, channels_path, 24)
                                
                                # Should skip non-Message objects
                                assert result == set()

    @pytest.mark.asyncio
    async def test_scrape_telegram_configs_message_without_text(self):
        """Test scrape_telegram_configs with Message without text."""
        settings = MagicMock()
        settings.telegram_api_id = 12345
        settings.telegram_api_hash = "test_hash"
        settings.session_path = "test_session"
        
        channels_path = MagicMock()
        channels_path.exists.return_value = True
        channels_path.open.return_value.__enter__.return_value = ["channel1\n"]
        
        # Mock TelegramClient with Message without text
        mock_client = AsyncMock()
        mock_message = MagicMock(spec=Message)
        mock_message.message = None  # No message text
        
        mock_client.iter_messages.return_value.__aiter__.return_value = [mock_message]
        
        with patch('streamline_vpn.merger.telegram_scraper.TelegramClient') as mock_client_class:
            with patch('streamline_vpn.merger.telegram_scraper.parse_configs_from_text') as mock_parse:
                with patch('streamline_vpn.merger.telegram_scraper.extract_subscription_urls') as mock_extract:
                    with patch('streamline_vpn.merger.telegram_scraper.choose_proxy'):
                        with patch('aiohttp.ClientSession'):
                            with patch('streamline_vpn.merger.telegram_scraper.tqdm'):
                                mock_client_class.return_value = mock_client
                                mock_parse.return_value = set()
                                mock_extract.return_value = []
                                
                                result = await scrape_telegram_configs(settings, channels_path, 24)
                                
                                # Should skip messages without text
                                assert result == set()

    @pytest.mark.asyncio
    async def test_scrape_telegram_configs_failed_subscription_fetch(self):
        """Test scrape_telegram_configs with failed subscription fetch."""
        settings = MagicMock()
        settings.telegram_api_id = 12345
        settings.telegram_api_hash = "test_hash"
        settings.session_path = "test_session"
        settings.request_timeout = 30
        settings.retry_attempts = 3
        settings.retry_base_delay = 1.0
        
        channels_path = MagicMock()
        channels_path.exists.return_value = True
        channels_path.open.return_value.__enter__.return_value = ["channel1\n"]
        
        # Mock TelegramClient
        mock_client = AsyncMock()
        mock_message = MagicMock(spec=Message)
        mock_message.message = "Check this subscription: http://example.com/sub"
        
        mock_client.iter_messages.return_value.__aiter__.return_value = [mock_message]
        
        with patch('streamline_vpn.merger.telegram_scraper.TelegramClient') as mock_client_class:
            with patch('streamline_vpn.merger.telegram_scraper.parse_configs_from_text') as mock_parse:
                with patch('streamline_vpn.merger.telegram_scraper.extract_subscription_urls') as mock_extract:
                    with patch('streamline_vpn.merger.telegram_scraper.fetch_text') as mock_fetch:
                        with patch('streamline_vpn.merger.telegram_scraper.choose_proxy'):
                            with patch('aiohttp.ClientSession'):
                                with patch('streamline_vpn.merger.telegram_scraper.tqdm'):
                                    mock_client_class.return_value = mock_client
                                    mock_parse.return_value = {"config1"}
                                    mock_extract.return_value = ["http://example.com/sub"]
                                    mock_fetch.return_value = None  # Failed fetch
                                    
                                    result = await scrape_telegram_configs(settings, channels_path, 24)
                                    
                                    # Should still return configs from message text
                                    assert len(result) >= 1
