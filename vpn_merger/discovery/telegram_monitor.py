"""
Telegram Channel Monitor
======================

Real-time Telegram channel monitor for VPN configuration sources.
"""

import logging
from datetime import datetime
from typing import Any

# Telegram API
try:
    from telethon import TelegramClient, events
    from telethon.tl.types import Channel, Message

    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    Message = None  # Type annotation fallback

from .models import (
    TELEGRAM_CHANNELS,
    DiscoveredSource,
    detect_protocols_from_text,
    extract_configs_from_text,
)

logger = logging.getLogger(__name__)


class TelegramChannelMonitor:
    """Real-time Telegram channel monitor for VPN configuration sources."""

    def __init__(self, api_id: str | None = None, api_hash: str | None = None):
        """Initialize Telegram monitor.

        Args:
            api_id: Telegram API ID
            api_hash: Telegram API hash
        """
        self.api_id = api_id
        self.api_hash = api_hash
        self.telegram_client = None
        self.monitored_channels = TELEGRAM_CHANNELS
        self.discovered_sources = []

        if TELEGRAM_AVAILABLE and api_id and api_hash:
            self._initialize_telegram_client()

    def _initialize_telegram_client(self):
        """Initialize Telegram client."""
        try:
            self.telegram_client = TelegramClient(
                "vpn_discovery_session", self.api_id, self.api_hash
            )
            logger.info("Telegram client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Telegram client: {e}")

    async def monitor_channels(self, channels: list[str] | None = None) -> list[DiscoveredSource]:
        """Monitor Telegram channels for VPN configuration sources.

        Args:
            channels: List of channel usernames to monitor

        Returns:
            List of discovered sources
        """
        channels = channels or self.monitored_channels
        discovered_sources = []

        if not self.telegram_client:
            logger.warning("Telegram client not available")
            return discovered_sources

        try:
            await self.telegram_client.start()

            for channel in channels:
                try:
                    channel_sources = await self._monitor_single_channel(channel)
                    discovered_sources.extend(channel_sources)
                except Exception as e:
                    logger.error(f"Error monitoring channel {channel}: {e}")
                    continue

            await self.telegram_client.disconnect()

        except Exception as e:
            logger.error(f"Error in channel monitoring: {e}")

        self.discovered_sources.extend(discovered_sources)
        logger.info(f"Discovered {len(discovered_sources)} new Telegram sources")
        return discovered_sources

    async def _monitor_single_channel(self, channel: str) -> list[DiscoveredSource]:
        """Monitor a single Telegram channel.

        Args:
            channel: Channel username to monitor

        Returns:
            List of discovered sources from this channel
        """
        discovered_sources = []

        try:
            # Get channel entity
            entity = await self.telegram_client.get_entity(channel)

            # Get recent messages
            messages = await self.telegram_client.get_messages(entity, limit=50)

            for message in messages:
                if not message.text:
                    continue

                # Extract configurations from message
                configs = extract_configs_from_text(message.text)
                if not configs:
                    continue

                # Calculate reliability score
                reliability_score = self._calculate_telegram_reliability(message, len(configs))

                # Create discovered source
                source = DiscoveredSource(
                    url=f"https://t.me/{channel}/{message.id}",
                    source_type="telegram",
                    title=f"Telegram Post - {channel}",
                    description=(
                        message.text[:200] + "..." if len(message.text) > 200 else message.text
                    ),
                    discovered_at=datetime.now(),
                    reliability_score=reliability_score,
                    config_count=len(configs),
                    protocols=detect_protocols_from_text(message.text),
                    region="global",
                    last_updated=message.date,
                )
                discovered_sources.append(source)

        except Exception as e:
            logger.error(f"Error monitoring single channel {channel}: {e}")

        return discovered_sources

    def _calculate_telegram_reliability(self, message: "Message", config_count: int) -> float:
        """Calculate reliability score for Telegram message.

        Args:
            message: Telegram message object
            config_count: Number of configurations found

        Returns:
            Reliability score between 0.0 and 1.0
        """
        score = 0.0

        # Message length (0-20 points)
        text_length = len(message.text or "")
        score += min(20, text_length / 100)

        # Configuration count (0-40 points)
        score += min(40, config_count * 2)

        # Message age (0-20 points)
        if message.date:
            days_since_message = (datetime.now() - message.date).days
            if days_since_message < 7:
                score += 20
            elif days_since_message < 30:
                score += 15
            elif days_since_message < 90:
                score += 10

        # Message views (0-20 points) - if available
        if hasattr(message, "views") and message.views:
            score += min(20, message.views / 100)

        return min(1.0, score / 100.0)

    async def search_messages(self, query: str, max_results: int = 50) -> list[dict[str, Any]]:
        """Search Telegram messages for VPN configurations.

        Args:
            query: Search query
            max_results: Maximum number of results to return

        Returns:
            List of message information
        """
        if not self.telegram_client:
            return []

        try:
            await self.telegram_client.start()

            messages = []
            for channel in self.monitored_channels:
                try:
                    entity = await self.telegram_client.get_entity(channel)
                    search_results = await self.telegram_client.get_messages(
                        entity, search=query, limit=max_results // len(self.monitored_channels)
                    )

                    for message in search_results:
                        if message.text:
                            message_info = {
                                "id": message.id,
                                "text": message.text,
                                "date": message.date,
                                "views": getattr(message, "views", 0),
                                "channel": channel,
                                "url": f"https://t.me/{channel}/{message.id}",
                            }
                            messages.append(message_info)

                except Exception as e:
                    logger.debug(f"Error searching channel {channel}: {e}")
                    continue

            await self.telegram_client.disconnect()
            return messages

        except Exception as e:
            logger.error(f"Error searching Telegram messages: {e}")
            return []

    def get_discovery_stats(self) -> dict[str, Any]:
        """Get discovery statistics.

        Returns:
            Dictionary containing discovery statistics
        """
        return {
            "total_sources": len(self.discovered_sources),
            "active_sources": len([s for s in self.discovered_sources if s.is_active]),
            "average_reliability": sum(s.reliability_score for s in self.discovered_sources)
            / max(len(self.discovered_sources), 1),
            "monitored_channels": len(self.monitored_channels),
            "total_configs_found": sum(s.config_count for s in self.discovered_sources),
        }
