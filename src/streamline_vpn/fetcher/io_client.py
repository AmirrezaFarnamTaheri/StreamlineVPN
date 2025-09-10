"""
HTTP IO helpers for FetcherService.
"""

from __future__ import annotations

import asyncio
import time
from typing import Optional, Dict, Any, List
import atexit
import weakref

import aiohttp


# Track created sessions for best-effort cleanup in tests and at exit
_SESSIONS: "weakref.WeakSet[aiohttp.ClientSession]" = weakref.WeakSet()


def _track_session(sess: aiohttp.ClientSession) -> None:
    try:
        _SESSIONS.add(sess)
    except Exception:
        pass


def get_tracked_sessions() -> List[aiohttp.ClientSession]:
    """Return a snapshot of tracked sessions (for test cleanup)."""
    try:
        return [s for s in list(_SESSIONS) if s is not None]
    except Exception:
        return []


def make_session(
    max_concurrent: int, timeout_seconds: int
) -> aiohttp.ClientSession:
    connector = aiohttp.TCPConnector(
        limit=max_concurrent,
        limit_per_host=10,
        ttl_dns_cache=300,
        use_dns_cache=True,
    )
    timeout = aiohttp.ClientTimeout(total=timeout_seconds)
    session = aiohttp.ClientSession(
        connector=connector,
        timeout=timeout,
        headers={
            "User-Agent": "StreamlineVPN/2.0.0",
            "Accept": "text/plain, application/json, */*",
            "Accept-Encoding": "gzip, deflate",
        },
    )
    _track_session(session)
    return session


async def execute_request(
    session: aiohttp.ClientSession,
    url: str,
    *,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    data: Optional[Any] = None,
    params: Optional[Dict[str, Any]] = None,
    retry_attempts: int = 3,
    retry_delay: float = 1.0,
    rate_limiters: Optional[Dict[str, Any]] = None,
    get_domain=None,
) -> str:
    from ..utils.logging import get_logger
    logger = get_logger(__name__)

    last_exc: Optional[BaseException] = None
    for attempt in range(retry_attempts + 1):
        try:
            start = time.time()
            logger.info(f"Fetching URL: {method} {url}")
            async with session.request(
                method=method,
                url=url,
                headers=headers,
                data=data,
                params=params,
            ) as resp:
                logger.info(f"Response for {url}: {resp.status}")
                resp.raise_for_status()
                content = await resp.text()
                # record response time
                if rate_limiters and get_domain:
                    domain = get_domain(url)
                    rl = rate_limiters.get(domain)
                    if rl is not None:
                        await rl.record_response_time(
                            domain, time.time() - start
                        )
                return content
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed for {url}: {e}")
            last_exc = e
            if attempt < retry_attempts:
                await asyncio.sleep(retry_delay * (2**attempt))
            else:
                break
    assert last_exc is not None
    raise last_exc


def _cleanup_sessions_at_exit() -> None:  # pragma: no cover - best-effort
    try:
        sessions = [s for s in _SESSIONS if not s.closed]
        if not sessions:
            return
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = None

        async def _close_all():
            for s in sessions:
                try:
                    await s.close()
                except Exception:
                    pass

        if loop and loop.is_running():
            for s in sessions:
                try:
                    loop.create_task(s.close())
                except Exception:
                    pass
        else:
            try:
                asyncio.run(_close_all())
            except Exception:
                pass
    except Exception:
        pass


atexit.register(_cleanup_sessions_at_exit)
