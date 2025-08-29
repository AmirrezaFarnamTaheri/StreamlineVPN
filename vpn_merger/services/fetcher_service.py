from __future__ import annotations

from typing import Callable, List, Optional, Tuple

import asyncio
import zlib

import aiohttp
from urllib.parse import urlparse

from .reliability import ExponentialBackoff, CircuitBreaker
from .rate_limiter import PerHostRateLimiter
from vpn_merger.monitoring.logging import log_json  # type: ignore

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
        # Configure circuit breaker from runtime config if available
        try:
            mon = getattr(getattr(base, 'monitoring', None), '__dict__', None) or getattr(base, 'monitoring', None)
            ft = int(getattr(mon, 'failure_threshold', 3)) if mon is not None else 3
            cd = float(getattr(mon, 'cooldown_seconds', 30.0)) if mon is not None else 30.0
        except Exception:
            ft, cd = 3, 30.0
        self._cb = CircuitBreaker(failure_threshold=ft, cooldown_seconds=cd)
        # Initial placeholders; real values set in _refresh_from_config()
        self._backoff = ExponentialBackoff(base=0.3, max_delay=4.0)
        self._rate = PerHostRateLimiter(per_host_rate=5.0, per_host_capacity=10)
        self._refresh_from_config()

    def _refresh_from_config(self) -> None:
        """Refresh backoff, rate limiter, and circuit breaker from runtime config.

        Reads from either self.config (if set) or processor.config, so callers
        may inject configuration after construction but before open().
        """
        base = getattr(self, 'config', None) or getattr(getattr(self, 'processor', None), 'config', None)
        try:
            nb = float(getattr(getattr(base, 'network', None), 'backoff_base', 0.3))
            mx = float(getattr(getattr(base, 'network', None), 'backoff_max_delay', 4.0))
        except Exception:
            nb, mx = 0.3, 4.0
        try:
            rate = float(getattr(getattr(base, 'network', None), 'per_host_rate_per_sec', 5.0))
            cap = int(getattr(getattr(base, 'network', None), 'per_host_capacity', 10))
        except Exception:
            rate, cap = 5.0, 10
        self._backoff = ExponentialBackoff(base=nb, max_delay=mx)
        self._rate = PerHostRateLimiter(per_host_rate=rate, per_host_capacity=cap)
        try:
            mon = getattr(getattr(base, 'monitoring', None), '__dict__', None) or getattr(base, 'monitoring', None)
            ft = int(getattr(mon, 'failure_threshold', 3)) if mon is not None else 3
            cd = float(getattr(mon, 'cooldown_seconds', 30.0)) if mon is not None else 30.0
        except Exception:
            ft, cd = 3, 30.0
        self._cb = CircuitBreaker(failure_threshold=ft, cooldown_seconds=cd)

    async def __aenter__(self):  # pragma: no cover
        return await self.open()

    async def __aexit__(self, *exc):  # pragma: no cover
        await self.close()

    async def open(self):
        # Ensure runtime config is applied before starting any requests
        try:
            self._refresh_from_config()
        except Exception:
            pass
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
            if self._cb.is_open(url):
                return url, []
            host = urlparse(url).hostname or ""
            for attempt in range(3):
                try:
                    if host:
                        await self._rate.acquire(host)
                    async with self.session.get(url, allow_redirects=True) as r:
                        if r.status != 200:
                            log_json(logging.INFO, "fetch_non_200", url=url, status=r.status)
                            self._cb.record_failure(url)
                            await asyncio.sleep(self._backoff.get_delay(attempt))
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
                        self._cb.record_success(url)
                        return url, self.processor(text)
                except Exception as e:
                    log_json(logging.WARNING, "fetch_error", url=url, attempt=attempt+1, error=str(e))
                    self._cb.record_failure(url)
                    await asyncio.sleep(self._backoff.get_delay(attempt))
            return url, []

    async def fetch_many(self, urls: List[str], progress_cb: Optional[Callable[[int, int], Awaitable[None] | None]] = None) -> List[Tuple[str, List[str]]]:
        async def stage(u: str) -> Tuple[str, List[str]]:
            return await self._fetch_url(u)
        # If no progress callback requested, try fast path
        if progress_cb is None:
            try:
                from vpn_merger.core.pipeline import ParallelPipeline  # type: ignore
                pipeline = ParallelPipeline([stage], concurrency=self.sem._value)  # type: ignore[attr-defined]
                return await pipeline.process(urls)
            except Exception:
                tasks = [asyncio.create_task(self._fetch_url(u)) for u in urls]
                return await asyncio.gather(*tasks)
        # Progress-aware path: run with bounded concurrency and update after each completion
        total = len(urls)
        completed = 0
        out: List[Tuple[str, List[str]]] = []
        sem = asyncio.Semaphore(self.sem._value)

        async def _one(u: str) -> None:
            nonlocal completed
            async with sem:
                res = await self._fetch_url(u)
                out.append(res)
                completed += 1
                try:
                    cb = progress_cb
                    if cb:
                        await cb(completed, total)  # type: ignore[misc]
                except Exception:
                    pass

        await asyncio.gather(*[asyncio.create_task(_one(u)) for u in urls])
        return out


