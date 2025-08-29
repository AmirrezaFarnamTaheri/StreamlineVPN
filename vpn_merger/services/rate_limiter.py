from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from typing import Dict


class TokenBucket:
    """Token bucket rate limiter.

    Refill rate is `rate_per_sec`; bucket holds up to `capacity` tokens.
    Each `acquire(n)` consumes tokens; if not enough, waits until available.
    """

    def __init__(self, rate_per_sec: float, capacity: int):
        self.rate = float(rate_per_sec)
        self.capacity = int(capacity)
        self.tokens = float(capacity)
        self.updated = time.time()
        self._lock = asyncio.Lock()

    def _refill(self) -> None:
        now = time.time()
        elapsed = now - self.updated
        if elapsed > 0:
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.updated = now

    async def acquire(self, n: int = 1) -> None:
        async with self._lock:
            while True:
                self._refill()
                if self.tokens >= n:
                    self.tokens -= n
                    return
                # time needed to get n tokens
                shortage = n - self.tokens
                wait_s = shortage / self.rate if self.rate > 0 else 0.1
                await asyncio.sleep(min(max(wait_s, 0.01), 1.0))


class PerHostRateLimiter:
    """Rate limiter maintaining per-host token buckets."""

    def __init__(self, per_host_rate: float = 5.0, per_host_capacity: int = 10):
        self.per_host_rate = float(per_host_rate)
        self.per_host_capacity = int(per_host_capacity)
        self._buckets: Dict[str, TokenBucket] = {}

    async def acquire(self, host: str) -> None:
        bucket = self._buckets.get(host)
        if bucket is None:
            bucket = TokenBucket(self.per_host_rate, self.per_host_capacity)
            self._buckets[host] = bucket
        await bucket.acquire(1)

