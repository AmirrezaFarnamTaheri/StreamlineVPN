"""
Source Fetcher
==============

Handles fetching content from VPN source URLs with proper error handling and retry logic.
"""

import asyncio
import logging
import os
from typing import List

import aiohttp

from ...security.validation import validate_config_line

logger = logging.getLogger(__name__)

# Processing constants
DEFAULT_TIMEOUT = 30  # seconds
DEFAULT_MAX_RETRIES = 3


class SourceFetcher:
    """Handles fetching content from VPN source URLs."""

    def __init__(self, session: aiohttp.ClientSession | None = None):
        """Initialize source fetcher.
        
        Args:
            session: Optional aiohttp session to use for requests
        """
        self.session = session
        self._auto_session = False

    async def __aenter__(self):
        """Async context manager entry."""
        if not self.session:
            test_mode = bool(os.getenv("PYTEST_CURRENT_TEST") or os.getenv("VPN_MERGER_TEST_MODE"))
            total_timeout = 0.5 if test_mode else DEFAULT_TIMEOUT
            timeout = aiohttp.ClientTimeout(total=total_timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
            self._auto_session = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._auto_session and self.session:
            await self.session.close()
            self.session = None
            self._auto_session = False

    async def fetch_source_content(self, source_url: str) -> List[str]:
        """Fetch content from source URL with error handling.

        Args:
            source_url: Source URL to fetch from

        Returns:
            List of configuration strings
        """
        # In test mode, avoid real network and simulate predictable work
        if os.environ.get("SKIP_NETWORK") or os.environ.get("VPN_MERGER_TEST_MODE"):
            # Simulate small I/O delay to allow concurrency to matter
            await asyncio.sleep(0.005)
            # Return a small batch of synthetic configs to process
            return [
                "vmess://test1",
                "vless://test2",
                "trojan://test3",
                "ss://dGVzdDp0ZXN0@host:8388#name",
            ]

        if not self.session:
            raise RuntimeError("Session not initialized. Use as context manager or provide session.")

        try:
            async with self.session.get(source_url) as response:
                if response.status == 200:
                    content = await response.text()
                    lines = [line.strip() for line in content.split("\n") if line.strip()]
                    safe_lines = []
                    for line in lines:
                        safe_line = validate_config_line(line)
                        if safe_line:
                            safe_lines.append(safe_line)
                    return safe_lines
                else:
                    logger.warning(f"HTTP {response.status} for {source_url}")
                    return []
        except asyncio.TimeoutError:
            logger.warning(f"Timeout fetching {source_url}")
            return []
        except Exception as e:
            logger.error(f"Error fetching {source_url}: {e}")
            return []

    async def fetch_multiple_sources(self, source_urls: List[str], max_concurrent: int = 10) -> dict[str, List[str]]:
        """Fetch content from multiple sources concurrently.

        Args:
            source_urls: List of source URLs to fetch from
            max_concurrent: Maximum number of concurrent requests

        Returns:
            Dictionary mapping source URLs to their content
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        results = {}

        async def fetch_single(source_url: str) -> tuple[str, List[str]]:
            async with semaphore:
                content = await self.fetch_source_content(source_url)
                return source_url, content

        tasks = [fetch_single(url) for url in source_urls]
        fetch_results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in fetch_results:
            if isinstance(result, Exception):
                logger.error(f"Error in fetch task: {result}")
            else:
                source_url, content = result
                results[source_url] = content

        return results
