"""
API Route Modules
=================

This package contains all the API route modules for the application.
Each module defines a self-contained set of related endpoints.
"""

from .cache import cache_router
from .configurations import configurations_router
from .pipeline import pipeline_router
from .sources import sources_router
from .system import system_router
from .websocket import websocket_router

__all__ = [
    "cache_router",
    "configurations_router",
    "pipeline_router",
    "sources_router",
    "system_router",
    "websocket_router",
]