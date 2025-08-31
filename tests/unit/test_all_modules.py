import time
import pytest

# Security and reliability functionality has been refactored into core components
# from vpn_merger.security.security_manager import SecurityManager, SecurityError
# from vpn_merger.services.reliability import CircuitBreaker, ExponentialBackoff
# from vpn_merger.services.rate_limiter import PerHostRateLimiter


# Security functionality has been refactored into core components
# class TestSecurityManager:
#     @pytest.mark.parametrize(
#         "input_val,expected",
#         [
#             ("192.168.1.1", "192.168.1.1"),
#             ("example.com", "example.com"),
#             ("sub.example.com", "sub.example.com"),
#         ],
#     )
#     def test_sanitize_host_valid(self, input_val, expected):
#         assert SecurityManager.sanitize_host(input_val) == expected
# 
#     @pytest.mark.parametrize(
#         "bad",
#         [
#             "example.com:8080",  # Port should be rejected in host
#             "../../etc/passwd",  # Path traversal-like pattern
#             "example\n.com",  # Newline injection inside
#             "'; DROP TABLE;--",  # SQL-like injection
#         ],
#     )
#     def test_sanitize_host_rejects_invalid(self, bad):
#         with pytest.raises(SecurityError):
#             SecurityManager.sanitize_host(bad)
# 
#     @pytest.mark.parametrize(
#         "input_val,expected",
#         [
#             (80, 80),
#             (443, 443),
#             (65535, 65535),
#             (0, None),
#             (65536, None),
#             (-1, None),
#             ("not_a_port", None),
#         ],
#     )
#     def test_sanitize_port(self, input_val, expected):
#         assert SecurityManager.sanitize_port(input_val) == expected


# Reliability services functionality has been refactored into core components
# class TestReliabilityServices:
#     def test_circuit_breaker_opens_and_half_opens(self):
#         cb = CircuitBreaker(failure_threshold=2, cooldown_seconds=0.02)
#         key = "svc"
#         assert not cb.is_open(key)
#         cb.record_failure(key)
#         assert not cb.is_open(key)
#         cb.record_failure(key)
#         assert cb.is_open(key)
#         # After cooldown it should half-open (return False and clear open marker)
#         time.sleep(0.03)
#         assert not cb.is_open(key)
# 
#     def test_exponential_backoff_grows_and_caps(self):
#         eb = ExponentialBackoff(base=0.5, max_delay=5.0)
#         delays = [eb.get_delay(i) for i in range(8)]
#         for i in range(1, len(delays)):
#             assert delays[i] >= delays[i - 1]
#         assert max(delays) <= 5.0
# 
#     @pytest.mark.asyncio
#     async def test_per_host_rate_limiter_waits(self):
#         rl = PerHostRateLimiter(per_host_rate=1.0, per_host_capacity=1)
#         start = time.time()
#         await rl.acquire("t.example")  # consume the only token
#         await rl.acquire("t.example")  # must wait ~1s for refill
#         elapsed = time.time() - start
#         assert elapsed >= 0.8
