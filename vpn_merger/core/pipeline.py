from __future__ import annotations

import asyncio
from typing import Any, List, Callable, Awaitable, Dict
import aiohttp


class StreamingConfigProcessor:
    def __init__(self, max_buffer_size: int = 10000, max_line_length: int = 10_000):
        self.max_buffer_size = max_buffer_size
        self.max_line_length = max_line_length
        self.buffer: List[str] = []

    async def process_stream(self, stream, callback: Callable[[List[str]], Awaitable[None]]):
        async for chunk in stream:
            try:
                text = chunk.decode('utf-8', 'ignore')
            except Exception:
                continue
            for line in text.splitlines():
                if not line:
                    continue
                if len(line) > self.max_line_length:
                    continue
                self.buffer.append(line)
                if len(self.buffer) >= self.max_buffer_size:
                    await self._flush(callback)
        if self.buffer:
            await self._flush(callback)

    async def _flush(self, callback: Callable[[List[str]], Awaitable[None]]):
        await callback(self.buffer)
        self.buffer.clear()
        import gc
        gc.collect()


class ConnectionPoolManager:
    _instance: 'ConnectionPoolManager' | None = None
    _pools: Dict[str, aiohttp.ClientSession] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def get_pool(self, name: str = 'default', limit: int = 100, limit_per_host: int = 10) -> aiohttp.ClientSession:
        if name not in self._pools:
            # Build a connector without conflicting keepalive/force_close flags 
            # to support a wide range of aiohttp versions.
            connector = aiohttp.TCPConnector(
                limit=limit,
                limit_per_host=limit_per_host,
                ttl_dns_cache=300,
                enable_cleanup_closed=True,
            )
            timeout = aiohttp.ClientTimeout(total=30, connect=5, sock_connect=5, sock_read=10)
            self._pools[name] = aiohttp.ClientSession(connector=connector, timeout=timeout, headers={'User-Agent': 'VPN-Merger/2.0'})
        return self._pools[name]

    async def close_all(self) -> None:
        for session in self._pools.values():
            try:
                await session.close()
            except Exception:
                pass
        self._pools.clear()


class ParallelPipeline:
    def __init__(self, stages: List[Callable[[Any], Awaitable[Any]]], concurrency: int = 10):
        self.stages = stages
        self.concurrency = concurrency

    async def process(self, items: List[Any]) -> List[Any]:
        results = items
        for stage in self.stages:
            sem = asyncio.Semaphore(self.concurrency)

            async def run(item: Any):
                async with sem:
                    return await stage(item)

            results = await asyncio.gather(*[run(item) for item in results], return_exceptions=True)
            results = [r for r in results if not isinstance(r, Exception)]
        return results
