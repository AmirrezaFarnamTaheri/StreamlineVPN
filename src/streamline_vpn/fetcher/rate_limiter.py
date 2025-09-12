"""
Rate Limiter
============

Rate limiting implementation for API calls.
"""

import asyncio
import time
from typing import Dict, Optional
from collections import defaultdict, deque

from ..utils.logging import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """Rate limiter implementation."""

    def __init__(
        self,
        max_requests: int = 60,
        time_window: int = 60,
        burst_limit: int = 10,
    ):
        """Initialize rate limiter.

        Args:
            max_requests: Maximum requests per time window
            time_window: Time window in seconds
            burst_limit: Maximum burst requests
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.burst_limit = burst_limit

        # Track requests per key
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.burst_requests: Dict[str, deque] = defaultdict(deque)

        self._lock = asyncio.Lock()

    async def is_allowed(self, key: str) -> bool:
        """Check if request is allowed for given key.

        Args:
            key: Request key (e.g., IP address, user ID)

        Returns:
            True if request is allowed, False otherwise
        """
        async with self._lock:
            now = time.time()

            # Clean old requests
            self._clean_old_requests(key, now)

            # Check burst limit
            if len(self.burst_requests[key]) >= self.burst_limit:
                logger.debug("Rate limit burst exceeded for key %s", key)
                return False

            # Check rate limit
            if len(self.requests[key]) >= self.max_requests:
                logger.debug("Rate limit exceeded for key %s", key)
                return False

            # Add current request
            self.requests[key].append(now)
            self.burst_requests[key].append(now)

            return True

    async def wait_if_needed(self, key: str) -> None:
        """Wait if rate limit is exceeded.

        Args:
            key: Request key
        """
        while not await self.is_allowed(key):
            await asyncio.sleep(0.1)

    def _clean_old_requests(self, key: str, now: float) -> None:
        """Clean old requests outside time window.

        Args:
            key: Request key
            now: Current timestamp
        """
        cutoff = now - self.time_window

        # Clean regular requests
        while self.requests[key] and self.requests[key][0] < cutoff:
            self.requests[key].popleft()

        # Clean burst requests (1 second window)
        burst_cutoff = now - 1.0
        while (
            self.burst_requests[key]
            and self.burst_requests[key][0] < burst_cutoff
        ):
            self.burst_requests[key].popleft()

    def get_stats(self, key: str) -> Dict[str, int]:
        """Get rate limit statistics for key.

        Args:
            key: Request key

        Returns:
            Statistics dictionary
        """
        now = time.time()
        self._clean_old_requests(key, now)

        return {
            "current_requests": len(self.requests[key]),
            "current_burst": len(self.burst_requests[key]),
            "max_requests": self.max_requests,
            "max_burst": self.burst_limit,
            "remaining_requests": max(
                0, self.max_requests - len(self.requests[key])
            ),
            "remaining_burst": max(
                0, self.burst_limit - len(self.burst_requests[key])
            ),
        }

    def reset(self, key: Optional[str] = None) -> None:
        """Reset rate limiter.

        Args:
            key: Specific key to reset, or None for all keys
        """
        if key is None:
            self.requests.clear()
            self.burst_requests.clear()
        else:
            self.requests.pop(key, None)
            self.burst_requests.pop(key, None)


class AdaptiveRateLimiter(RateLimiter):
    """Adaptive rate limiter that adjusts based on response times."""

    def __init__(
        self,
        max_requests: int = 60,
        time_window: int = 60,
        burst_limit: int = 10,
        min_requests: int = 10,
        response_time_threshold: float = 1.0,
    ):
        """Initialize adaptive rate limiter.

        Args:
            max_requests: Maximum requests per time window
            time_window: Time window in seconds
            burst_limit: Maximum burst requests
            min_requests: Minimum requests per time window
            response_time_threshold: Response time threshold for adaptation
        """
        super().__init__(max_requests, time_window, burst_limit)
        self.min_requests = min_requests
        self.response_time_threshold = response_time_threshold
        self.response_times: Dict[str, deque] = defaultdict(deque)

    async def record_response_time(
        self, key: str, response_time: float
    ) -> None:
        """Record response time for adaptation.

        Args:
            key: Request key
            response_time: Response time in seconds
        """
        async with self._lock:
            now = time.time()
            self.response_times[key].append((now, response_time))

            # Keep only recent response times
            cutoff = now - self.time_window
            while (
                self.response_times[key]
                and self.response_times[key][0][0] < cutoff
            ):
                self.response_times[key].popleft()

            # Adapt rate limit based on response times
            await self._adapt_rate_limit(key)

    async def _adapt_rate_limit(self, key: str) -> None:
        """Adapt rate limit based on response times.

        Args:
            key: Request key
        """
        if not self.response_times[key]:
            return

        # Calculate average response time
        response_times = [rt for _, rt in self.response_times[key]]
        avg_response_time = sum(response_times) / len(response_times)

        # Adjust rate limit based on response time
        if avg_response_time > self.response_time_threshold:
            # Slow response, reduce rate limit
            self.max_requests = max(
                self.min_requests, int(self.max_requests * 0.8)
            )
            logger.debug(
                f"Reduced rate limit to {self.max_requests} for key {key}"
            )
        else:
            # Fast response, increase rate limit
            self.max_requests = min(100, int(self.max_requests * 1.1))
            logger.debug(
                f"Increased rate limit to {self.max_requests} for key {key}"
            )
