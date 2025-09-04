"""
Web Interface Handlers
=====================

Modular handlers for the enhanced web interface.
"""

from .api_handlers import APIHandlers
from .websocket_handler import WebSocketHandler
from .static_handler import StaticHandler

__all__ = [
    "APIHandlers",
    "WebSocketHandler", 
    "StaticHandler"
]

