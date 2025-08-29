from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
import pickle


@dataclass
class CacheEntry:
    value: Any
    expires_at: datetime
    last_access: datetime = field(default_factory=datetime.now)
    access_count: int = 0

    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at


@dataclass
class CacheStats:
    l1_hits: int = 0
    l2_hits: int = 0
    misses: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.l1_hits + self.l2_hits + self.misses
        return 0.0 if total == 0 else (self.l1_hits + self.l2_hits) / total


class MultiTierCache:
    """L1 in-memory cache with optional L2 async client (Redis-like).

    L2 client must implement async get(key: str) -> bytes|None and
    async setex(key: str, ttl: int, value: bytes) -> None
    """

    def __init__(self, redis_client: Any | None = None, l1_max_size: int = 1000):
        self.l1_cache: Dict[str, CacheEntry] = {}
        self.l1_max_size = int(l1_max_size)
        self.redis = redis_client
        self.stats = CacheStats()

    async def get(self, key: str, tier: str = "all") -> Optional[Any]:
        if tier in ("all", "l1") and key in self.l1_cache:
            entry = self.l1_cache[key]
            if not entry.is_expired():
                entry.last_access = datetime.now()
                entry.access_count += 1
                self.stats.l1_hits += 1
                return entry.value
            # drop expired
            self.l1_cache.pop(key, None)

        if tier in ("all", "l2") and self.redis is not None:
            try:
                raw = await self.redis.get(f"cache:{key}")
                if raw:
                    self.stats.l2_hits += 1
                    val = pickle.loads(raw)
                    if tier == "all":
                        self._add_to_l1(key, val, 300)
                    return val
            except Exception:
                # ignore L2 failures for resilience
                pass

        self.stats.misses += 1
        return None

    async def set(self, key: str, value: Any, ttl: int = 3600, tier: str = "all") -> None:
        if tier in ("all", "l1"):
            self._add_to_l1(key, value, ttl)
        if tier in ("all", "l2") and self.redis is not None:
            try:
                await self.redis.setex(f"cache:{key}", int(ttl), pickle.dumps(value))
            except Exception:
                pass

    def _add_to_l1(self, key: str, value: Any, ttl: int) -> None:
        if len(self.l1_cache) >= self.l1_max_size:
            # LRU eviction: remove the least recently accessed
            lru_key = min(self.l1_cache.items(), key=lambda kv: kv[1].last_access)[0]
            self.l1_cache.pop(lru_key, None)
        self.l1_cache[key] = CacheEntry(value=value, expires_at=datetime.now() + timedelta(seconds=int(ttl)))

