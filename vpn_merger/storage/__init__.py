"""
Storage package for VPN Merger.

This package provides storage-related functionality including caching,
persistence, and data management.
"""

from .cache import MultiTierCache

__all__ = ["MultiTierCache"]
