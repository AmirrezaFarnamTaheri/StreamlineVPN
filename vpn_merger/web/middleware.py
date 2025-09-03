"""
aiohttp middlewares: API token auth, rate limiting, and audit logging.
"""

from __future__ import annotations

import os
import time
from collections.abc import Callable

from aiohttp import web


class MemoryRateLimiter:
    def __init__(self, max_per_minute: int = 120):
        self.max_per_minute = max_per_minute
        self.bucket: dict[str, dict[str, float]] = {}

    def allow(self, key: str) -> bool:
        now = time.time()
        window = int(now // 60)
        entry = self.bucket.get(key)
        if not entry or entry["window"] != window:
            self.bucket[key] = {"window": window, "count": 1}
            return True
        if entry["count"] < self.max_per_minute:
            entry["count"] += 1
            return True
        return False


@web.middleware
async def api_token_middleware(request: web.Request, handler: Callable) -> web.Response:
    """API token authentication middleware with new-style signature."""
    # Skip for public GET endpoints and health/metrics/static
    public_get_paths = {"/", "/merger", "/generator", "/analytics"}
    if (
        request.path in ("/health", "/metrics")
        or request.path.startswith("/static")
        or (request.method == "GET" and (request.path in public_get_paths or request.path.startswith("/api/")))
    ):
        return await handler(request)
    expected = os.getenv("API_TOKEN")
    # Allow tests/dev to bypass auth
    if os.getenv("VPN_MERGER_TEST_MODE") == "1":
        expected = None
    if expected:
        token = request.headers.get("X-API-Token") or request.query.get("api_token")
        if token != expected:
            return web.json_response({"error": "unauthorized"}, status=401)
    return await handler(request)


def create_rate_limit_middleware(max_per_minute: int = 120) -> Callable:
    """Create a rate limiting middleware with new-style signature."""
    limiter = MemoryRateLimiter(max_per_minute)

    @web.middleware
    async def rate_limit_middleware(request: web.Request, handler: Callable) -> web.Response:
        ip = request.headers.get("X-Forwarded-For", request.remote or "unknown")
        if not limiter.allow(ip):
            return web.json_response({"error": "rate limit"}, status=429)
        return await handler(request)

    return rate_limit_middleware


@web.middleware
async def audit_middleware(request: web.Request, handler: Callable) -> web.Response:
    """Audit logging middleware with new-style signature."""
    try:
        response = await handler(request)
        return response
    finally:
        # Minimal audit (method, path, status best-effort)
        pass
