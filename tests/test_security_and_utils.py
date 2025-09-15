import os
import pytest
from streamline_vpn.security.validator import SecurityValidator
from streamline_vpn.utils.error_handling import CircuitBreaker, retry_with_backoff, ErrorRecovery


def test_security_validator_url_and_port(monkeypatch):
    # Ensure safe lists from default settings are honored
    v = SecurityValidator()
    assert v.validate_url("https://test-server.example/configs.txt") is True
    assert v.validate_url("javascript:alert('xss')") is False
    assert v.validate_port(443) is True
    assert v.validate_port(0) is False


@pytest.mark.asyncio
async def test_circuit_breaker_and_retry():
    # Circuit breaker opens after threshold
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1)

    calls = {"n": 0}

    @cb
    async def flaky():
        calls["n"] += 1
        raise RuntimeError("boom")

    # Two failures triggers OPEN
    with pytest.raises(RuntimeError):
        await flaky()
    with pytest.raises(RuntimeError):
        await flaky()
    # Now circuit should be OPEN and raise CircuitBreakerError directly
    from streamline_vpn.utils.error_handling import CircuitBreakerError
    with pytest.raises(CircuitBreakerError):
        await flaky()

    # Retry decorator succeeds after two failures
    attempts = {"n": 0}

    @retry_with_backoff(max_attempts=3, base_delay=0.01)
    async def flaky_retry():
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise RuntimeError("fail")
        return "ok"

    res = await flaky_retry()
    assert res == "ok"


@pytest.mark.asyncio
async def test_error_recovery():
    async def primary():
        raise ValueError("primary failed")

    async def fallback():
        return 42

    result = await ErrorRecovery.with_fallback(primary, fallback)
    assert result == 42

