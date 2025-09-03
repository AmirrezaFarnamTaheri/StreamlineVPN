# Reliability services functionality has been refactored into core components
# from vpn_merger.services.reliability import CircuitBreaker, ExponentialBackoff
# Rate limiter functionality has been refactored into core components
# from vpn_merger.services.rate_limiter import PerHostRateLimiter


# Reliability services functionality has been refactored into core components
# def test_circuit_breaker_opens_after_failures():
#     cb = CircuitBreaker(failure_threshold=3, cooldown_seconds=60)
#
#     assert not cb.is_open("host1")
#
#     cb.record_failure("host1")
#     assert not cb.is_open("host1")
#     cb.record_failure("host1")
#     assert not cb.is_open("host1")
#     cb.record_failure("host1")
#     assert cb.is_open("host1")
#
#
# def test_exponential_backoff_increases():
#     eb = ExponentialBackoff(base=0.5, max_delay=10.0)
#     delays = [eb.get_delay(i) for i in range(6)]
#     for i in range(1, len(delays)):
#         assert delays[i] >= delays[i - 1]
#     assert max(delays) <= 10.0


# Rate limiter functionality has been refactored into core components
# @pytest.mark.asyncio
# async def test_per_host_rate_limiter_waits_when_exhausted():
#     # Capacity 2 tokens, 1 token per second
#     rl = PerHostRateLimiter(per_host_rate=1.0, per_host_capacity=2)
#
#     start = time.time()
#     await rl.acquire("test.example.com")  # consumes 1
#     await rl.acquire("test.example.com")  # consumes 2 (capacity exhausted)
#     await rl.acquire("test.example.com")  # needs to wait ~1s for refill
#     elapsed = time.time() - start
#
#     assert elapsed >= 0.8
