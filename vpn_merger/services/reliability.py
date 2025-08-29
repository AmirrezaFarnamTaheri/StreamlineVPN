from __future__ import annotations

import time
from typing import Dict, Optional


class ExponentialBackoff:
    """Simple exponential backoff policy with jitterless delays.

    delay(attempt) = base * (2 ** attempt), capped by max_delay.
    """

    def __init__(self, base: float = 0.3, max_delay: float = 8.0):
        self.base = float(base)
        self.max_delay = float(max_delay)

    def get_delay(self, attempt: int) -> float:
        if attempt <= 0:
            return self.base
        d = self.base * (2 ** attempt)
        return min(d, self.max_delay)


class CircuitBreaker:
    """Lightweight circuit breaker keyed by URL.

    - Opens after `failure_threshold` consecutive failures
    - Remains open for `cooldown_seconds`
    - Half-opens after cooldown (next call permitted; on success closes, on fail re-opens)
    """

    def __init__(self, failure_threshold: int = 3, cooldown_seconds: float = 30.0):
        self.failure_threshold = int(failure_threshold)
        self.cooldown_seconds = float(cooldown_seconds)
        self._failures: Dict[str, int] = {}
        self._opened_at: Dict[str, float] = {}

    def is_open(self, key: str) -> bool:
        now = time.time()
        opened = self._opened_at.get(key)
        if opened is None:
            return False
        if now - opened >= self.cooldown_seconds:
            # Half-open: allow one trial by clearing open marker but keep failures
            self._opened_at.pop(key, None)
            return False
        return True

    def record_success(self, key: str) -> None:
        self._failures.pop(key, None)
        self._opened_at.pop(key, None)

    def record_failure(self, key: str) -> None:
        n = self._failures.get(key, 0) + 1
        self._failures[key] = n
        if n >= self.failure_threshold:
            self._opened_at[key] = time.time()

