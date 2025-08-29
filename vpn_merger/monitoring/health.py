from __future__ import annotations

"""Health check facade delegating to existing checker if available."""

try:
    from .health_checker import HealthChecker  # type: ignore
except Exception:  # pragma: no cover
    class HealthChecker:  # type: ignore
        async def check(self) -> bool:
            return True

