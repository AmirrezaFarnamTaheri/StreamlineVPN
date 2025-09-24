from typing import Any, Dict, List, Optional
from pymemcache.client.base import Client
from pymemcache.client.retrying import RetryingClient
from pymemcache.exceptions import MemcacheError

from ...utils.logging import get_logger

logger = get_logger(__name__)

class MemcachedClient:
    """A client for interacting with a Memcached cluster."""

    def __init__(self, servers: List[str]):
        """Initialize the Memcached client.

        Args:
            servers: A list of Memcached server addresses (e.g., ["host1:port1", "host2:port2"]).
        """
        self._client = None
        if servers:
            try:
                host, port = servers[0].split(":")
                server = (host, int(port))
                base_client = Client(server, connect_timeout=1, timeout=1)
                self._client = RetryingClient(base_client)
                logger.info("Memcached client initialized with server: %s", server)
            except Exception as e:
                logger.error("Failed to initialize Memcached client: %s", e)

    async def get(self, key: str) -> Optional[Any]:
        """Get a value from Memcached."""
        if not self._client:
            return None
        try:
            value = self._client.get(key)
            return value.decode("utf-8") if value else None
        except MemcacheError as e:
            logger.error("Memcached get error for key %s: %s", key, e)
            return None

    async def set(self, key: str, value: Any, ttl: int = 0) -> bool:
        """Set a value in Memcached."""
        if not self._client:
            return False
        try:
            self._client.set(key, value, expire=ttl)
            return True
        except MemcacheError as e:
            logger.error("Memcached set error for key %s: %s", key, e)
            return False

    async def delete(self, key: str) -> bool:
        """Delete a key from Memcached."""
        if not self._client:
            return False
        try:
            return self._client.delete(key)
        except MemcacheError as e:
            logger.error("Memcached delete error for key %s: %s", key, e)
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get Memcached stats."""
        if not self._client:
            return {}
        try:
            return self._client.stats()
        except MemcacheError as e:
            logger.error("Failed to get Memcached stats: %s", e)
            return {}
