import pytest
from unittest.mock import MagicMock, patch
from streamline_vpn.core.caching.memcached_client import MemcachedClient

@pytest.fixture
def mock_pymemcache_client():
    with patch('pymemcache.client.base.Client') as mock_client_class:
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance
        yield mock_client_instance

@pytest.mark.asyncio
async def test_memcached_client_get(mock_pymemcache_client):
    client = MemcachedClient(servers=["localhost:11211"])
    client._client = mock_pymemcache_client
    mock_pymemcache_client.get.return_value = b"test_value"
    value = await client.get("test_key")
    assert value == "test_value"
    mock_pymemcache_client.get.assert_called_once_with("test_key")

@pytest.mark.asyncio
async def test_memcached_client_set(mock_pymemcache_client):
    client = MemcachedClient(servers=["localhost:11211"])
    client._client = mock_pymemcache_client
    await client.set("test_key", "test_value", ttl=60)
    mock_pymemcache_client.set.assert_called_once_with("test_key", "test_value", expire=60)

@pytest.mark.asyncio
async def test_memcached_client_delete(mock_pymemcache_client):
    client = MemcachedClient(servers=["localhost:11211"])
    client._client = mock_pymemcache_client
    await client.delete("test_key")
    mock_pymemcache_client.delete.assert_called_once_with("test_key")

def test_memcached_client_get_stats(mock_pymemcache_client):
    client = MemcachedClient(servers=["localhost:11211"])
    client._client = mock_pymemcache_client
    mock_pymemcache_client.stats.return_value = {"get_hits": 10}
    stats = client.get_stats()
    assert stats == {"get_hits": 10}
    mock_pymemcache_client.stats.assert_called_once()
