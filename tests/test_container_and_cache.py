import asyncio
import os
import sys

# Ensure repo root is on sys.path for package imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from vpn_merger.core.container import ServiceContainer
from vpn_merger.storage.cache import MultiTierCache


def test_service_container_register_and_get_instance():
    class A:
        pass

    c = ServiceContainer()
    inst = A()
    c.register(A, instance=inst)
    assert c.get(A) is inst


def test_service_container_factory_lazy_singleton():
    class B:
        def __init__(self):
            self.x = 1

    c = ServiceContainer()
    c.register(B, factory=B)
    b1 = c.get(B)
    b2 = c.get(B)
    assert b1 is b2
    assert isinstance(b1, B)


def test_service_container_scope():
    class C:
        def __init__(self):
            self.y = 2

    parent = ServiceContainer()
    parent.register(C, factory=C)

    scope = parent.create_scope()
    c1 = scope.get(C)
    c2 = parent.get(C)
    assert isinstance(c1, C) and isinstance(c2, C)


class DummyRedis:
    def __init__(self):
        self._store = {}

    async def get(self, key: str):
        return self._store.get(key)

    async def setex(self, key: str, ttl: int, value: bytes):
        # ignore ttl for dummy; store raw
        self._store[key] = value


async def _cache_roundtrip():
    c = MultiTierCache(redis_client=DummyRedis(), l1_max_size=2)
    await c.set("a", {"v": 1}, ttl=1)
    v1 = await c.get("a")
    assert v1 == {"v": 1}
    # Cause L1 eviction by adding more entries
    await c.set("b", 2, ttl=10)
    await c.set("c", 3, ttl=10)
    # One of a/b likely evicted (LRU); access ensures no crash
    _ = await c.get("a")
    # L2 should still have a
    _ = await c.get("a", tier="l2")


def test_cache_roundtrip_event_loop():
    asyncio.run(_cache_roundtrip())
