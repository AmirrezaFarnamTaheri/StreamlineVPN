import logging
from pathlib import Path

import pytest

from streamline_vpn.utils.logging import get_logger, setup_logging, log_performance, log_error
from streamline_vpn.utils.error_handling import (
    CircuitBreaker,
    CircuitBreakerError,
    retry_with_backoff,
    timeout_handler,
    ErrorRecovery,
)


def test_setup_logging_and_get_logger(tmp_path: Path, caplog):
    caplog.set_level(logging.INFO)
    log_file = tmp_path / "logs" / "app.log"
    setup_logging(level="INFO", log_file=str(log_file))
    logger = get_logger(__name__)
    logger.info("hello")
    log_performance("unit_test", 0.01, items=1)
    try:
        raise ValueError("boom")
    except Exception as e:
        log_error(e, context="testing")
    # File created
    assert log_file.exists()


@pytest.mark.asyncio
async def test_circuit_breaker_and_retry_and_timeout(monkeypatch):
    # Circuit breaker opens after threshold
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1, expected_exception=RuntimeError)

    calls = {"n": 0}

    @cb
    async def flaky():
        calls["n"] += 1
        raise RuntimeError("fail")

    # First failure increments counter
    with pytest.raises(RuntimeError):
        await flaky()
    # Second failure reaches threshold (opens breaker) but still raises original error
    with pytest.raises(RuntimeError):
        await flaky()
    # Third call while OPEN raises CircuitBreakerError
    with pytest.raises(CircuitBreakerError):
        await flaky()

    # After timeout, half-open -> next failure keeps it open
    import asyncio

    await asyncio.sleep(0.11)
    with pytest.raises(RuntimeError):
        await flaky()

    # Retry with backoff
    attempts = {"n": 0}

    @retry_with_backoff(max_attempts=2, base_delay=0.01, max_delay=0.02, jitter=False)
    async def sometimes():
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise RuntimeError("first")
        return "ok"

    assert await sometimes() == "ok"

    # Timeout handler
    @timeout_handler(timeout_seconds=0.01)
    async def slow():
        await asyncio.sleep(0.05)

    with pytest.raises(Exception):
        await slow()


@pytest.mark.asyncio
async def test_error_recovery():
    async def primary():
        raise ValueError("nope")

    async def fallback():
        return 42

    result = await ErrorRecovery.with_fallback(primary, fallback)
    assert result == 42
