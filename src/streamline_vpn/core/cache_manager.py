"""
Cache Manager
=============

Cache manager providing backward compatibility with VPNCacheService.
"""

from .caching.service import VPNCacheService

# Alias for backward compatibility
CacheManager = VPNCacheService

# Re-export for convenience
__all__ = ["CacheManager", "VPNCacheService"]
