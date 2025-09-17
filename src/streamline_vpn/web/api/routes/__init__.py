"""
API route modules.
"""

from .health import health_router
from .sources import sources_router
from .configurations import configurations_router
from .diagnostics import diagnostics_router
from .websocket import websocket_router

__all__ = [
    "health_router",
    "sources_router",
    "configurations_router",
    "diagnostics_router",
    "websocket_router",
]
