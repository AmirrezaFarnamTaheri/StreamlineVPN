from __future__ import annotations

from typing import Callable, List, Optional, Tuple

import asyncio
import zlib

import aiohttp

try:
    import brotli  # type: ignore
except Exception:  # pragma: no cover
    brotli = None


TextProcessor = Callable[[str], List[str]]


class AsyncSourceFetcher:
    """Async HTTP fetcher with retries and compression handling."""

    def __init__(self, processor: TextProcessor, concurrency: int = 12, per_host: int = 4, use_pool: bool = False, pool_name: str = 'default'):
        self.processor = processor
        self.sem = asyncio.Semaphore(concurrency)
        self.per_host = per_host
        self.session: Optional[aiohttp.ClientSession] = None
        self.use_pool = use_pool
        self.pool_name = pool_name

    async def __aenter__(self):  # pragma: no cover
        return await self.open()

    async def __aexit__(self, *exc):  # pragma: no cover
        await self.close()

    async def open(self):
        if not self.session:
            if self.use_pool:
                try:
                    from vpn_merger.core.pipeline import ConnectionPoolManager  # type: ignore
                    self.session = await ConnectionPoolManager().get_pool(name=self.pool_name, limit=self.sem._value, limit_per_host=self.per_host)  # type: ignore[attr-defined]
                except Exception:
                    # Fallback to dedicated session
                    self.session = aiohttp.ClientSession(
                        headers={"user-agent": "submerger/1.0"},
                        timeout=aiohttp.ClientTimeout(total=15),
                        trust_env=True,
                    )
            else:
                self.session = aiohttp.ClientSession(
                    headers={"user-agent": "submerger/1.0"},
                    timeout=aiohttp.ClientTimeout(total=15),
                    trust_env=True,
                )
        return self

    async def close(self):
        if self.session and not self.use_pool:
            await self.session.close()
            self.session = None

    async def _fetch_url(self, url: str) -> Tuple[str, List[str]]:
        assert self.session, "Call open() first"
        async with self.sem:
            for attempt in range(3):
                try:
                    async with self.session.get(url, allow_redirects=True) as r:
                        if r.status != 200:
                            await asyncio.sleep(0.4 * (attempt + 1))
                            continue
                        data = await r.read()
                        enc = r.headers.get("content-encoding", "").lower()
                        if "br" in enc and brotli is not None:
                            try:
                                data = brotli.decompress(data)  # type: ignore[attr-defined]
                            except Exception:
                                pass
                        elif "gzip" in enc:
                            try:
                                data = zlib.decompress(data, 16 + zlib.MAX_WBITS)
                            except Exception:
                                pass
                        text = data.decode("utf-8", errors="replace")
                        return url, self.processor(text)
                except Exception:
                    await asyncio.sleep(0.6 * (attempt + 1))
            return url, []

    async def fetch_many(self, urls: List[str]) -> List[Tuple[str, List[str]]]:
        async def stage(u: str) -> Tuple[str, List[str]]:
            return await self._fetch_url(u)
        try:
            from vpn_merger.core.pipeline import ParallelPipeline  # type: ignore
            pipeline = ParallelPipeline([stage], concurrency=self.sem._value)  # type: ignore[attr-defined]
            return await pipeline.process(urls)
        except Exception:
            # Fallback: gather
            tasks = [asyncio.create_task(self._fetch_url(u)) for u in urls]
            return await asyncio.gather(*tasks)


