import sys
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from streamline_vpn.security.rate_limiter import RateLimiter

@pytest.fixture
def rate_limiter():
    """Fixture for RateLimiter."""
    with patch('streamline_vpn.settings.get_settings') as mock_get_settings:
        mock_settings = mock_get_settings.return_value
        mock_settings.security.rl_max_requests = 10
        mock_settings.security.rl_time_window_seconds = 60
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        return limiter

class TestRateLimiter:
    def test_initialization(self, rate_limiter):
        assert rate_limiter.max_requests == 10
        assert rate_limiter.window_seconds == 60

    def test_check_rate_limit_not_limited(self, rate_limiter):
        assert rate_limiter.check_rate_limit("key1") is False

    def test_check_rate_limit_limited(self, rate_limiter):
        for _ in range(15):
            rate_limiter.check_rate_limit("key1")
        assert rate_limiter.check_rate_limit("key1") is True

    @pytest.mark.asyncio
    async def test_is_allowed(self, rate_limiter):
        assert await rate_limiter.is_allowed("key1") is True
        for _ in range(15):
            rate_limiter.check_rate_limit("key1")
        assert await rate_limiter.is_allowed("key1") is False

    def test_get_remaining_requests(self, rate_limiter):
        assert rate_limiter.get_remaining_requests("key1") == 10
        rate_limiter.check_rate_limit("key1")
        assert rate_limiter.get_remaining_requests("key1") == 9

    def test_get_reset_time(self, rate_limiter):
        assert rate_limiter.get_reset_time("key1") > 0
        rate_limiter.check_rate_limit("key1")
        assert rate_limiter.get_reset_time("key1") > 0

    def test_get_rate_limit_stats(self, rate_limiter):
        rate_limiter.check_rate_limit("key1")
        stats = rate_limiter.get_rate_limit_stats()
        assert stats["active_rate_limits"] == 1
        assert stats["total_requests_tracked"] == 1

    def test_rate_limit_expiry(self, rate_limiter):
        for _ in range(15):
            rate_limiter.check_rate_limit("key1")
        
        # Advance time
        with patch('streamline_vpn.security.rate_limiter.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime.now() + timedelta(seconds=61)
            assert rate_limiter.check_rate_limit("key1") is False
    
    def test_clear_rate_limits(self, rate_limiter):
        rate_limiter.check_rate_limit("key1")
        rate_limiter.clear_rate_limits()
        assert rate_limiter.rate_limits == {}
