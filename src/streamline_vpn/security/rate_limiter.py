"""
Rate Limiter
============

Rate limiting functionality for security management.
"""

from typing import Dict, List, Any
from datetime import datetime, timedelta

from ..utils.logging import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """Rate limiter for security management."""
    
    def __init__(self, max_requests_per_minute: int = 60):
        """Initialize rate limiter.
        
        Args:
            max_requests_per_minute: Maximum requests per minute
        """
        self.max_requests_per_minute = max_requests_per_minute
        self.rate_limits: Dict[str, List[datetime]] = {}
    
    def check_rate_limit(self, source_url: str) -> bool:
        """Check if source is rate limited.
        
        Args:
            source_url: Source URL to check
            
        Returns:
            True if rate limited, False otherwise
        """
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        # Clean old entries
        if source_url in self.rate_limits:
            self.rate_limits[source_url] = [
                timestamp for timestamp in self.rate_limits[source_url]
                if timestamp > minute_ago
            ]
        else:
            self.rate_limits[source_url] = []
        
        # Check rate limit
        if len(self.rate_limits[source_url]) >= self.max_requests_per_minute:
            return True
        
        # Add current request
        self.rate_limits[source_url].append(now)
        return False
    
    def get_rate_limit_stats(self) -> Dict[str, Any]:
        """Get rate limiting statistics.
        
        Returns:
            Rate limiting statistics
        """
        return {
            "max_requests_per_minute": self.max_requests_per_minute,
            "active_rate_limits": len(self.rate_limits),
            "total_requests_tracked": sum(len(requests) for requests in self.rate_limits.values())
        }
    
    def clear_rate_limits(self) -> None:
        """Clear all rate limits."""
        self.rate_limits.clear()
        logger.info("All rate limits cleared")
