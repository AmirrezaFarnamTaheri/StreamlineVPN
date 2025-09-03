"""
Async Source Fetcher Service
===========================

Asynchronous service for fetching VPN configuration sources.
"""

import asyncio
import gzip
import logging
from typing import List, Tuple, Optional, Dict, Any

import aiohttp

logger = logging.getLogger(__name__)


class AsyncSourceFetcher:
    """Asynchronous source fetcher with retry logic and compression support."""
    
    def __init__(self, processor=None, concurrency: int = 10):
        """Initialize the async source fetcher.
        
        Args:
            processor: Optional processor for fetched content
            concurrency: Maximum concurrent requests
        """
        self.processor = processor
        self.concurrency = concurrency
        self.session: Optional[aiohttp.ClientSession] = None
        self._backoff = ExponentialBackoff()
    
    async def open(self):
        """Open the HTTP session."""
        if self.session is not None:
            return
        connector = aiohttp.TCPConnector(limit=self.concurrency, limit_per_host=5, ttl_dns_cache=300)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
    
    async def close(self):
        """Close the HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def fetch_many(self, urls: List[str]) -> List[Tuple[str, List[str]]]:
        """Fetch multiple URLs concurrently.
        
        Args:
            urls: List of URLs to fetch
            
        Returns:
            List of tuples (url, content_lines)
        """
        if not self.session:
            raise RuntimeError("Session not open. Call open() first.")
        
        semaphore = asyncio.Semaphore(self.concurrency)
        
        async def fetch_one(url: str) -> Tuple[str, List[str]]:
            async with semaphore:
                return await self._fetch_single(url)
        
        tasks = [fetch_one(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to fetch {urls[i]}: {result}")
                processed_results.append((urls[i], []))
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _fetch_single(self, url: str, attempts: int = 3) -> Tuple[str, List[str]]:
        """Fetch a single URL.
        
        Args:
            url: URL to fetch
            
        Returns:
            Tuple of (url, content_lines)
        """
        last_error: Optional[Exception] = None
        for attempt in range(max(1, attempts)):
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        content = await self._read_content(response)
                        if callable(self.processor):
                            try:
                                lines = self.processor(content)
                            except Exception:
                                lines = content.split('\n')
                        else:
                            lines = content.split('\n')
                        return (url, [line.strip() for line in lines if str(line).strip()])
                    else:
                        logger.warning(f"HTTP {response.status} for {url}")
                        # retry on non-200
            except Exception as e:
                last_error = e
                logger.error(f"Error fetching {url}: {e}")
            # backoff (tests expect zero backoff to be possible)
            delay = self._backoff.get_delay(attempt)
            if delay > 0:
                await asyncio.sleep(delay)
        # after attempts exhausted
        if last_error:
            logger.error(f"Giving up on {url} after {attempts} attempts: {last_error}")
        return (url, [])
    
    async def _read_content(self, response: aiohttp.ClientResponse) -> str:
        """Read content from response with compression support.
        
        Args:
            response: HTTP response
            
        Returns:
            Decompressed content
        """
        content_encoding = response.headers.get('content-encoding', '').lower()
        
        if content_encoding == 'gzip':
            raw_data = await response.read()
            return gzip.decompress(raw_data).decode('utf-8')
        elif content_encoding == 'br':
            try:
                import brotli
                raw_data = await response.read()
                return brotli.decompress(raw_data).decode('utf-8')
            except ImportError:
                logger.warning("brotli not available, falling back to raw content")
                raw_data = await response.read()
                return raw_data.decode('utf-8', errors='ignore')
        else:
            raw_data = await response.read()
            return raw_data.decode('utf-8', errors='ignore')


class ExponentialBackoff:
    """Exponential backoff for retry logic."""
    
    def __init__(self, base: float = 0.0, max_delay: float = 60.0):
        """Initialize exponential backoff.
        
        Args:
            base: Base delay in seconds
            max_delay: Maximum delay in seconds
        """
        self.base = base
        self.max_delay = max_delay
    
    def get_delay(self, attempt: int) -> float:
        """Get delay for attempt number.
        
        Args:
            attempt: Attempt number (0-based)
            
        Returns:
            Delay in seconds
        """
        delay = self.base * (2 ** attempt)
        return min(delay, self.max_delay)
