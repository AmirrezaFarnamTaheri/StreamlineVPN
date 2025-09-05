"""
Fetcher policy helpers
----------------------

Utilities to manage per-domain circuit breakers and rate limiters
used by the FetcherService.
"""

from __future__ import annotations

from typing import Dict, Tuple

from .circuit_breaker import CircuitBreaker, CircuitBreakerOpenException
from .rate_limiter import AdaptiveRateLimiter
from ..settings import get_fetcher_settings


def ensure_policies(
    domain: str,
    circuit_breakers: Dict[str, CircuitBreaker],
    rate_limiters: Dict[str, AdaptiveRateLimiter],
) -> Tuple[CircuitBreaker, AdaptiveRateLimiter]:
    """Ensure there is a circuit breaker and a rate limiter for a domain."""
    s = get_fetcher_settings()
    if domain not in circuit_breakers:
        circuit_breakers[domain] = CircuitBreaker(
            failure_threshold=s.cb_failure_threshold,
            recovery_timeout=s.cb_recovery_timeout_seconds,
            name=f"fetcher_{domain}",
        )
    if domain not in rate_limiters:
        rate_limiters[domain] = AdaptiveRateLimiter(
            max_requests=s.rl_max_requests,
            time_window=s.rl_time_window_seconds,
            burst_limit=s.rl_burst_limit,
        )
    return circuit_breakers[domain], rate_limiters[domain]


async def apply_rate_limit(domain: str, rate_limiter: AdaptiveRateLimiter) -> None:
    """Await rate limiter before a request."""
    await rate_limiter.wait_if_needed(domain)


async def call_with_breaker(
    breaker: CircuitBreaker,
    fn,
    *args,
    **kwargs,
):
    """Execute a coroutine behind a circuit breaker."""
    return await breaker.call(fn, *args, **kwargs)
