#!/usr/bin/env python3
"""
Enhanced Web Interface - Refactored
==================================

Refactored enhanced web interface with modular handlers and clean architecture.
"""

import asyncio
import logging
from typing import Any, Dict, Optional

from aiohttp import web
try:
    from aiohttp_cors import setup as cors_setup, ResourceOptions
except Exception:  # optional dependency
    cors_setup = None
    ResourceOptions = None

from ..core.merger import VPNSubscriptionMerger
from ..core.observers import get_event_bus
from ..monitoring.health_monitor import get_health_monitor
from .handlers import APIHandlers, WebSocketHandler, StaticHandler

logger = logging.getLogger(__name__)


class EnhancedWebInterface:
    """Enhanced web interface with modular architecture."""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        """Initialize the enhanced web interface.
        
        Args:
            host: Host address to bind to
            port: Port number to bind to
        """
        self.host = host
        self.port = port
        self.app = web.Application()
        self.runner = None
        self.site = None
        
        # Initialize components
        self.merger = VPNSubscriptionMerger()
        self.event_bus = get_event_bus()
        self.health_monitor = get_health_monitor()
        self.monitoring_dashboard = None
        
        # Initialize handlers
        self.api_handlers = APIHandlers(self.merger, self.health_monitor)
        self.websocket_handler = WebSocketHandler()
        self.static_handler = StaticHandler()
        
        # Setup CORS if available
        cors = None
        if cors_setup and ResourceOptions:
            cors = cors_setup(self.app, defaults={
                "*": ResourceOptions(
                    allow_credentials=True,
                    expose_headers="*",
                    allow_headers="*",
                    allow_methods="*"
                )
            })
        
        # Setup routes
        self._setup_routes()
        
        # Add CORS to all routes if configured
        if cors:
            for route in list(self.app.router.routes()):
                cors.add(route)
        
        logger.info(f"Enhanced web interface initialized on {host}:{port}")
    
    def _setup_routes(self) -> None:
        """Setup web application routes."""
        # Main interface
        self.app.router.add_get("/", self.static_handler.handle_main_interface)
        
        # API endpoints
        self.app.router.add_get("/api/status", self.api_handlers.handle_status_api)
        self.app.router.add_get("/api/health", self.api_handlers.handle_health_api)
        self.app.router.add_get("/api/sources", self.api_handlers.handle_sources_api)
        self.app.router.add_get("/api/configs", self.api_handlers.handle_configs_api)
        self.app.router.add_get("/api/statistics", self.api_handlers.handle_statistics_api)
        
        # Action endpoints
        self.app.router.add_post("/api/merge", self.api_handlers.handle_merge_api)
        self.app.router.add_post("/api/export", self.api_handlers.handle_export_api)
        self.app.router.add_post("/api/validate", self.api_handlers.handle_validate_api)
        
        # Configuration endpoints
        self.app.router.add_get("/api/config", self.api_handlers.handle_get_config_api)
        self.app.router.add_post("/api/config", self.api_handlers.handle_update_config_api)
        
        # Monitoring endpoints
        self.app.router.add_get("/api/monitoring", self.api_handlers.handle_monitoring_api)
        self.app.router.add_post("/api/monitoring/start", self.api_handlers.handle_start_monitoring_api)
        self.app.router.add_post("/api/monitoring/stop", self.api_handlers.handle_stop_monitoring_api)
        
        # WebSocket for real-time updates
        self.app.router.add_get("/ws", self.websocket_handler.handle_websocket)
        
        # Static files
        static_dir = self.static_handler.static_dir
        if static_dir.exists():
            self.app.router.add_static("/static", static_dir)
    
    async def start(self) -> None:
        """Start the enhanced web interface."""
        try:
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            
            self.site = web.TCPSite(self.runner, self.host, self.port)
            await self.site.start()
            
            logger.info(f"Enhanced web interface started at http://{self.host}:{self.port}")
            
            # Start background tasks
            await self.websocket_handler.start_background_updates()
            
        except Exception as e:
            logger.error(f"Failed to start enhanced web interface: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the enhanced web interface."""
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        
        # Stop background tasks
        await self.websocket_handler.stop_background_updates()
        self.websocket_handler.close_all_connections()
        
        logger.info("Enhanced web interface stopped")
    
    async def broadcast_update(self, event_type: str, data: Dict[str, Any]) -> None:
        """Broadcast update to all WebSocket connections."""
        await self.websocket_handler.broadcast_update(event_type, data)
    
    def get_connection_count(self) -> int:
        """Get the number of active WebSocket connections."""
        return self.websocket_handler.get_connection_count()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current interface status."""
        return {
            "host": self.host,
            "port": self.port,
            "active_connections": self.get_connection_count(),
            "monitoring_active": self.monitoring_dashboard is not None,
            "status": "running" if self.site else "stopped"
        }

