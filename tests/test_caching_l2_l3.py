import asyncio
import json
import pytest

from streamline_vpn.core.caching import service as cache_service_module


class FakeRedisClient:
    def __init__(self, *args, **kwargs):
        self.store = {}
        self.fail = False
        self.stats = {"hits": 0, "misses": 0, "total_requests": 0, "avg_response_time": 0.0}

    async def get(self, key: str):
        if self.fail:
            raise RuntimeError("redis down")
        self.stats["total_requests"] += 1
        if key in self.store:
            self.stats["hits"] += 1
            return self.store[key]
        self.stats["misses"] += 1
        return None

    async def set(self, key: str, value: str, ttl=None):
        if self.fail:
            raise RuntimeError("redis down")
        self.store[key] = value
        return True

    async def delete(self, key: str):
        if self.fail:
            raise RuntimeError("redis down")
        self.store.pop(key, None)
        return True

    async def scan(self, pattern: str, count: int = 100):
        return []

    def get_stats(self):
        return self.stats


@pytest.mark.asyncio
async def test_cache_set_get_delete_with_l3_fallback(tmp_path, monkeypatch):
    # Ensure we don't construct a real RedisClusterClient
    monkeypatch.setattr(cache_service_module, "RedisClusterClient", FakeRedisClient)

    db_path = tmp_path / "cache.db"
    svc = cache_service_module.VPNCacheService(redis_nodes=[], l1_cache_size=10, l3_db_path=str(db_path))

    key = "k1"
    value = {"x": 1}
    ok = await svc.set(key, value, ttl=60)
    assert ok is True

    # L1 hit
    v1 = await svc.get(key)
    assert v1 == value

    # Bust L1 and force Redis failure to test L3 path
    await svc.l1_cache.delete(key)
    assert await svc.get(key) == value  # should hydrate from Redis or L3

    # Simulate Redis outage and ensure L3 still serves
    svc.redis_client.fail = True
    await svc.l1_cache.delete(key)
    v2 = await svc.get(key)
    assert v2 == value  # served via L3

    # Delete should clear all levels (no exception if Redis down)
    assert await svc.delete(key) is True
    await svc.l1_cache.delete(key)
    assert await svc.get(key) is None

    # Exercise get() JSON decode error path from Redis
    svc.redis_client.fail = False
    svc.redis_client.store["badjson"] = "{not-json}"
    await svc.l1_cache.delete("badjson")
    assert await svc.get("badjson") is None

    # Exercise L3 get exception path
    original_l3_get = svc.l3_cache.get
    async def _raise_l3(*args, **kwargs):
        raise RuntimeError("l3 down")
    svc.l3_cache.get = _raise_l3  # type: ignore
    await svc.l1_cache.delete("missing-l3")
    assert await svc.get("missing-l3") is None
    svc.l3_cache.get = original_l3_get  # type: ignore


@pytest.mark.asyncio
async def test_circuit_breaker_opens_and_recovers(tmp_path, monkeypatch):
    monkeypatch.setattr(cache_service_module, "RedisClusterClient", FakeRedisClient)
    db_path = tmp_path / "cache2.db"
    svc = cache_service_module.VPNCacheService(redis_nodes=[{"host": "localhost", "port": "6379"}], l1_cache_size=1, l3_db_path=str(db_path))

    # Trip CB by repeated failures
    svc.redis_client.fail = True
    for _ in range(svc.circuit_breaker_threshold + 1):
        await svc.get("missing")
    assert svc._is_circuit_breaker_open() is True

    # Set value while CB open; value still persists to L3
    await svc.set("cbkey", {"a": 2}, ttl=30)
    await svc.l1_cache.delete("cbkey")
    # Should be served from L3 since CB is open and Redis disabled
    v = await svc.get("cbkey")
    assert v == {"a": 2}

    # Cache stats endpoint
    stats = svc.get_cache_stats()
    assert "l1_cache" in stats and "l2_cache" in stats and "circuit_breaker" in stats


@pytest.mark.asyncio
async def test_cache_set_and_delete_error_branches(tmp_path, monkeypatch):
    monkeypatch.setattr(cache_service_module, "RedisClusterClient", FakeRedisClient)
    db_path = tmp_path / "cache3.db"
    svc = cache_service_module.VPNCacheService(redis_nodes=[], l1_cache_size=1, l3_db_path=str(db_path))

    # Redis set returns False path + L3 set exception
    async def _false_set(key, value, ttl=None):
        return False
    svc.redis_client.set = _false_set  # type: ignore
    async def _raise_l3_set(key, value, ttl=None):
        raise RuntimeError("l3-set")
    svc.l3_cache.set = _raise_l3_set  # type: ignore
    ok = await svc.set("k", {"y": 1}, ttl=5)
    assert ok is True

    # Top-level set exception (L1 failure)
    async def _raise_l1_set(*args, **kwargs):
        raise RuntimeError("l1-set")
    svc.l1_cache.set = _raise_l1_set  # type: ignore
    ok2 = await svc.set("k2", {"z": 2})
    assert ok2 is False

    # Delete L3 exception branch
    async def _raise_l3_del(k):
        raise RuntimeError("l3-del")
    svc.l3_cache.delete = _raise_l3_del  # type: ignore
    assert await svc.delete("k") is True

    # Top-level delete exception (L1 failure)
    async def _raise_l1_del(k):
        raise RuntimeError("l1-del")
    svc.l1_cache.delete = _raise_l1_del  # type: ignore
    assert await svc.delete("k2") is False

    # Invalidation calls
    async def _fake_inval(event_type, context, l2_cache):
        return 7
    svc.invalidation_service.invalidate_cache_pattern = _fake_inval  # type: ignore
    assert await svc.invalidate_user_cache("u1") == 7
    assert await svc.invalidate_server_cache("s1") == 7
