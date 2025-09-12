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


class OptimizedSessionManager:
    """Session manager with connection pooling and performance optimizations."""
    
    _instance: Optional['OptimizedSessionManager'] = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def initialize(self):
        """Initialize session manager with optimized settings."""
        if self._initialized:
            return
            
        async with self._lock:
            if self._initialized:
                return
                
            self._sessions: Dict[str, aiohttp.ClientSession] = {}
            
            # Optimized connector settings
            self._connector_config = {
                "limit": 100,  # Total connection pool
                "limit_per_host": 30,  # Per-host limit
                "ttl_dns_cache": 300,  # DNS cache TTL
                "enable_cleanup_closed": True,
                "force_close": False,
                "keepalive_timeout": 30,
            }
            
            # Optimized timeout settings
            self._timeout_config = aiohttp.ClientTimeout(
                total=30,
                connect=10,
                sock_connect=10,
                sock_read=10
            )
            
            self._initialized = True
            logger.info("Session manager initialized with optimized settings")
    
    async def get_session(self, key: str = "default") -> aiohttp.ClientSession:
        """Get or create an optimized session."""
        if not self._initialized:
            await self.initialize()
            
        if key not in self._sessions or self._sessions[key].closed:
            connector = aiohttp.TCPConnector(**self._connector_config)
            
            self._sessions[key] = aiohttp.ClientSession(
                connector=connector,
                timeout=self._timeout_config,
                headers={
                    "User-Agent": "StreamlineVPN/2.0",
                    "Accept-Encoding": "gzip, deflate",
                    "Connection": "keep-alive",
                },
                trust_env=True,
                trace_configs=[self._create_trace_config()] if logger.level <= 10 else None
            )
            
        return self._sessions[key]
    
    def _create_trace_config(self) -> aiohttp.TraceConfig:
        """Create trace configuration for debugging."""
        trace_config = aiohttp.TraceConfig()
        
        async def on_request_start(session, trace_config_ctx, params):
            logger.debug("Starting request to %s", params.url)
            
        async def on_request_end(session, trace_config_ctx, params):
            logger.debug("Request completed in %.2fs", params.elapsed.total_seconds())
            
        trace_config.on_request_start.append(on_request_start)
        trace_config.on_request_end.append(on_request_end)
        
        return trace_config
    
    async def close(self):
        """Close all sessions gracefully."""
        if not self._initialized:
            return
            
        for key, session in self._sessions.items():
            if not session.closed:
                await session.close()
                logger.debug("Closed session: %s", key)
                
        self._sessions.clear()
        self._initialized = False

# Global optimized session manager
session_manager = OptimizedSessionManager()


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
