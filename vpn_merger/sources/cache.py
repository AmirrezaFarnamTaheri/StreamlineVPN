from __future__ import annotations

from typing import List, Optional

try:
    from vpn_merger.storage.cache import MultiTierCache  # type: ignore
except Exception:  # pragma: no cover
    MultiTierCache = None  # type: ignore


class SourceCache:
    def __init__(self, ttl_seconds: int = 3600):
        self.ttl = int(ttl_seconds)
        self.cache = MultiTierCache() if MultiTierCache else None

    async def get(self, key: str) -> Optional[List[str]]:
        if not self.cache:
            return None
        return await self.cache.get(key)

    async def set(self, key: str, urls: List[str]) -> None:
        if not self.cache:
            return None
        await self.cache.set(key, urls, ttl=self.ttl)

