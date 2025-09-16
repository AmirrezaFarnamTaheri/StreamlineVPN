"""
Tests for RateLimiter.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from streamline_vpn.security.rate_limiter import RateLimiter


class TestRateLimiter:
    """Test RateLimiter class"""
    
    def test_initialization(self):
        """Test rate limiter initialization"""
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        assert limiter.max_requests == 10
        assert limiter.window_seconds == 60
        assert hasattr(limiter, 'requests')
    
    @pytest.mark.asyncio
    async def test_is_allowed_within_limit(self):
        """Test rate limiting within allowed limit"""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        
        # Should allow first 5 requests
        for i in range(5):
            assert await limiter.is_allowed("test_key") is True
    
    @pytest.mark.asyncio
    async def test_is_allowed_exceeds_limit(self):
        """Test rate limiting when exceeding limit"""
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        
        # First 2 requests should be allowed
        assert await limiter.is_allowed("test_key") is True
        assert await limiter.is_allowed("test_key") is True
        
        # Third request should be blocked
        assert await limiter.is_allowed("test_key") is False
    
    @pytest.mark.asyncio
    async def test_different_keys(self):
        """Test rate limiting with different keys"""
        limiter = RateLimiter(max_requests=1, window_seconds=60)
        
        # Different keys should be independent
        assert await limiter.is_allowed("key1") is True
        assert await limiter.is_allowed("key2") is True
        assert await limiter.is_allowed("key1") is False
        assert await limiter.is_allowed("key2") is False
    
    @pytest.mark.asyncio
    async def test_window_reset(self):
        """Test rate limit window reset"""
        limiter = RateLimiter(max_requests=1, window_seconds=0.1)  # Very short window
        
        # First request should be allowed
        assert await limiter.is_allowed("test_key") is True
        
        # Second request should be blocked
        assert await limiter.is_allowed("test_key") is False
        
        # Wait for window to reset
        await asyncio.sleep(0.2)
        
        # Should be allowed again
        assert await limiter.is_allowed("test_key") is True
    
    def test_get_remaining_requests(self):
        """Test getting remaining requests"""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        
        # Initially should have all requests available
        assert limiter.get_remaining_requests("test_key") == 5
    
    def test_get_reset_time(self):
        """Test getting reset time"""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        
        # Should return a valid timestamp
        reset_time = limiter.get_reset_time("test_key")
        assert isinstance(reset_time, (int, float))
        assert reset_time > 0

