import asyncio
from time import sleep

import pytest

from streamline_vpn.core.caching.l1_cache import L1ApplicationCache


@pytest.mark.asyncio
async def test_l1_cache_set_get_ttl_and_eviction():
    cache = L1ApplicationCache(max_size=2, default_ttl=1)

    # Miss then set then hit
    assert await cache.get("a") is None
    await cache.set("a", 1)
    val = await cache.get("a")
    assert val == 1

    # TTL expiry
    await asyncio.sleep(1.1)
    assert await cache.get("a") is None

    # Eviction LRU
    await cache.set("a", 1, ttl=5)
    await cache.set("b", 2, ttl=5)
    # Access order: a, b
    await cache.set("c", 3, ttl=5)  # should evict 'a'
    assert await cache.get("a") is None
    assert await cache.get("b") == 2
    assert await cache.get("c") == 3

    # Invalidate by tags
    await cache.set("x", 99, ttl=5, tags=["t1"])  # evicts b or c depending on LRU, ensure delete by tag works
    invalidated = await cache.invalidate_by_tags(["t1"])
    assert invalidated >= 1

    stats = cache.get_stats()
    assert "hits" in stats and "misses" in stats and "evictions" in stats

