"""
HTTP IO helpers for FetcherService.
"""

from __future__ import annotations

import asyncio
import atexit
import time
import weakref
from typing import Any, Dict, List, Optional

import aiohttp

from ..utils.logging import get_logger

logger = get_logger(__name__)


# Track created sessions for best-effort cleanup in tests and at exit
_SESSIONS: "weakref.WeakSet[aiohttp.ClientSession]" = weakref.WeakSet()


class SessionManager:
    """Manage reusable aiohttp sessions with connection pooling."""

    def __init__(self) -> None:
        self._default_headers = {
            "User-Agent": "StreamlineVPN/2.0.0",
            "Accept": "text/plain, application/json, */*",
            "Accept-Encoding": "gzip, deflate",
        }
        self._sessions: Dict[str, aiohttp.ClientSession] = {}
        self._limits = {
            "limit": 100,
            "limit_per_host": 30,
            "ttl_dns_cache": 300,
            "use_dns_cache": True,
        }
        self._timeout_total = 30

    async def get_session(self, key: str = "default") -> aiohttp.ClientSession:
        sess = self._sessions.get(key)
        # If an existing session is bound to a different (closed) event loop, recreate it
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            current_loop = None
        if sess and not sess.closed:
            sess_loop = getattr(sess, "_loop", None)
            if current_loop is not None and sess_loop is not current_loop:
                try:
                    await sess.close()
                except Exception:
                    pass
                self._sessions.pop(key, None)
                sess = None

        if not sess or sess.closed:
            connector = aiohttp.TCPConnector(**self._limits)
            timeout = aiohttp.ClientTimeout(total=self._timeout_total)
            sess = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=self._default_headers,
            )
            _track_session(sess)
            self._sessions[key] = sess
        return sess

    async def close_all(self) -> None:
        for sess in list(self._sessions.values()):
            try:
                if not sess.closed:
                    await sess.close()
            except Exception:
                pass
        self._sessions.clear()


_SESSION_MANAGER = SessionManager()


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
    # Backwards-compatible factory that now draws from SessionManager
    # Ignores per-call limits in favor of centralized pooling.
    # For legacy callers, still create a dedicated session if needed.
    # Here, we map to the shared default pool.
    # Note: We cannot await here; use get_event_loop to fetch session.
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        # Create a temporary future to run async getter
        return loop.run_until_complete(_SESSION_MANAGER.get_session("default"))  # type: ignore
    else:
        return asyncio.run(_SESSION_MANAGER.get_session("default"))


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
            logger.info("Fetching URL: %s %s", method, url)
            # Ensure we use a live session (in case callers passed a closed one)
            active_session = session
            if active_session is None or getattr(active_session, "closed", False):
                active_session = await _SESSION_MANAGER.get_session("default")
            async with active_session.request(
                method=method,
                url=url,
                headers=headers,
                data=data,
                params=params,
            ) as resp:
                logger.info("Response for %s: %s", url, resp.status)
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
            logger.error("Attempt %d failed for %s: %s", attempt + 1, url, e)
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
            try:
                await _SESSION_MANAGER.close_all()
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
