"""
Fetcher Service
===============

Advanced fetcher service with circuit breakers, rate limiting, and retry logic.
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

from .circuit_breaker import CircuitBreaker, CircuitBreakerOpenException
from .rate_limiter import AdaptiveRateLimiter
# Import moved to avoid circular dependencies
# from .policies import ensure_policies, apply_rate_limit, call_with_breaker
from ..utils.logging import get_logger
from ..settings import get_settings
from ..utils.helpers import measure_time

logger = get_logger(__name__)


class FetcherService:
    """Advanced fetcher service with fault tolerance."""

    def __init__(
        self,
        max_concurrent: Optional[int] = None,
        timeout: Optional[int] = None,
        retry_attempts: Optional[int] = None,
        retry_delay: Optional[float] = None,
        circuit_breaker_threshold: int = 5,
        rate_limit_requests: int = 60,
        rate_limit_window: int = 60,
    ):
        """Initialize fetcher service.

        Args:
            max_concurrent: Maximum concurrent requests
            timeout: Request timeout in seconds
            retry_attempts: Number of retry attempts
            retry_delay: Delay between retries in seconds
            circuit_breaker_threshold: Circuit breaker failure threshold
            rate_limit_requests: Rate limit requests per window
            rate_limit_window: Rate limit window in seconds
        """
        settings = get_settings()
        s = settings.fetcher
        self.max_concurrent = (
            max_concurrent if max_concurrent is not None else s.max_concurrent
        )
        self.timeout = timeout if timeout is not None else s.timeout_seconds
        self.retry_attempts = (
            retry_attempts if retry_attempts is not None else s.retry_attempts
        )
        self.retry_delay = (
            retry_delay if retry_delay is not None else s.retry_delay
        )

        # Circuit breakers per domain
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}

        # Rate limiters per domain
        self.rate_limiters: Dict[str, AdaptiveRateLimiter] = {}

        # Semaphore for concurrency control
        self.semaphore = asyncio.Semaphore(self.max_concurrent)

        # Session for connection pooling
        self.session: Optional[aiohttp.ClientSession] = None

        # Statistics
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "circuit_breaker_trips": 0,
            "rate_limit_hits": 0,
            "retry_attempts": 0,
        }

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def initialize(self) -> None:
        """Initialize fetcher service."""
        if self.session is None or self.session.closed:
            from .io_client import make_session

            self.session = make_session(self.max_concurrent, self.timeout)

        logger.info("Fetcher service initialized")

    async def close(self) -> None:
        """Close fetcher service."""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

        logger.info("Fetcher service closed")

    async def fetch(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Fetch content from URL with fault tolerance.

        Args:
            url: URL to fetch
            method: HTTP method
            headers: Additional headers
            data: Request data
            params: Query parameters

        Returns:
            Response content or None if failed
        """
        if not self.session:
            await self.initialize()

        domain = self._get_domain(url)

        # Ensure per-domain policies
        from .policies import ensure_policies, apply_rate_limit, call_with_breaker
        
        circuit_breaker, rate_limiter = ensure_policies(
            domain, self.circuit_breakers, self.rate_limiters
        )
        # Apply rate limiter
        await apply_rate_limit(domain, rate_limiter)

        # Execute request through circuit breaker
        try:
            result = await call_with_breaker(
                circuit_breaker,
                self._execute_request,
                url,
                method,
                headers,
                data,
                params,
            )

            self.stats["successful_requests"] += 1
            return result

        except CircuitBreakerOpenException:
            self.stats["circuit_breaker_trips"] += 1
            logger.warning(f"Circuit breaker open for domain {domain}")
            return None

        except Exception as e:
            self.stats["failed_requests"] += 1
            logger.error(f"Request failed for {url}: {e}")
            return None

        finally:
            self.stats["total_requests"] += 1

    async def fetch_multiple(
        self,
        urls: List[str],
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Optional[str]]:
        """Fetch multiple URLs concurrently.

        Args:
            urls: List of URLs to fetch
            method: HTTP method
            headers: Additional headers

        Returns:
            Dictionary mapping URLs to responses
        """
        tasks = []
        for url in urls:
            task = asyncio.create_task(
                self._fetch_with_semaphore(url, method, headers)
            )
            tasks.append((url, task))

        results = {}
        for url, task in tasks:
            try:
                result = await task
                results[url] = result
            except Exception as e:
                logger.error(f"Task failed for {url}: {e}")
                results[url] = None

        return results

    async def _fetch_with_semaphore(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
    ) -> Optional[str]:
        """Fetch URL with semaphore for concurrency control.

        Args:
            url: URL to fetch
            method: HTTP method
            headers: Additional headers

        Returns:
            Response content or None if failed
        """
        async with self.semaphore:
            return await self.fetch(url, method, headers)

    @measure_time
    async def _execute_request(
        self,
        url: str,
        method: str,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Execute HTTP request with retry logic.

        Args:
            url: URL to fetch
            method: HTTP method
            headers: Additional headers
            data: Request data
            params: Query parameters

        Returns:
            Response content

        Raises:
            Exception: If request fails after retries
        """
        from .io_client import execute_request

        return await execute_request(
            self.session,
            url,
            method=method,
            headers=headers,
            data=data,
            params=params,
            retry_attempts=self.retry_attempts,
            retry_delay=self.retry_delay,
            rate_limiters=self.rate_limiters,
            get_domain=self._get_domain,
        )

    def _get_domain(self, url: str) -> str:
        """Extract domain from URL.

        Args:
            url: URL to extract domain from

        Returns:
            Domain name
        """
        try:
            parsed = urlparse(url)
            return parsed.hostname or "unknown"
        except Exception:
            return "unknown"

    def get_circuit_breaker_state(self, domain: str) -> Optional[str]:
        """Get circuit breaker state for domain.

        Args:
            domain: Domain name

        Returns:
            Circuit breaker state or None if not found
        """
        if domain in self.circuit_breakers:
            return self.circuit_breakers[domain].get_state().value
        return None

    def get_rate_limit_stats(self, domain: str) -> Optional[Dict[str, int]]:
        """Get rate limit statistics for domain.

        Args:
            domain: Domain name

        Returns:
            Rate limit statistics or None if not found
        """
        if domain in self.rate_limiters:
            return self.rate_limiters[domain].get_stats(domain)
        return None

    def get_statistics(self) -> Dict[str, Any]:
        """Get fetcher service statistics.

        Returns:
            Statistics dictionary
        """
        return {
            **self.stats,
            "circuit_breakers": len(self.circuit_breakers),
            "rate_limiters": len(self.rate_limiters),
            "active_connections": self.semaphore._value,
        }

    def reset_circuit_breaker(self, domain: str) -> None:
        """Reset circuit breaker for domain.

        Args:
            domain: Domain name
        """
        if domain in self.circuit_breakers:
            self.circuit_breakers[domain].reset()
            logger.info(f"Reset circuit breaker for domain {domain}")

    def reset_rate_limiter(self, domain: str) -> None:
        """Reset rate limiter for domain.

        Args:
            domain: Domain name
        """
        if domain in self.rate_limiters:
            self.rate_limiters[domain].reset(domain)
            logger.info(f"Reset rate limiter for domain {domain}")
