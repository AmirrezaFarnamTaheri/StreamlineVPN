#!/usr/bin/env python3
"""
WebSocket Handler for Enhanced Web Interface
===========================================

Handles WebSocket connections and real-time communication.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List

from aiohttp import web

logger = logging.getLogger(__name__)


class WebSocketHandler:
    """Handles WebSocket connections and real-time communication."""
    
    def __init__(self):
        """Initialize WebSocket handler."""
        self.connections: List[web.WebSocketResponse] = []
        self._is_running = False
    
    async def handle_websocket(self, request: web.Request) -> web.WebSocketResponse:
        """Handle WebSocket connection."""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        # Add to connections list
        self.connections.append(ws)
        logger.info(f"WebSocket connection established. Total connections: {len(self.connections)}")
        
        try:
            while not ws.closed:
                # Send periodic status updates
                status_data = {
                    "timestamp": datetime.now().isoformat(),
                    "type": "status_update",
                    "data": {
                        "active_connections": len(self.connections),
                        "monitoring_active": False  # Will be set by main interface
                    }
                }
                
                await ws.send_str(json.dumps(status_data))
                await asyncio.sleep(30)  # Send update every 30 seconds
                
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            # Remove from connections list
            if ws in self.connections:
                self.connections.remove(ws)
            logger.info(f"WebSocket connection closed. Total connections: {len(self.connections)}")
        
        return ws
    
    async def broadcast_update(self, event_type: str, data: Dict[str, Any]) -> None:
        """Broadcast update to all WebSocket connections."""
        if not self.connections:
            return
        
        message = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "data": data
        }
        
        # Send to all connected clients
        disconnected = []
        for ws in self.connections:
            try:
                await ws.send_str(json.dumps(message))
            except Exception as e:
                logger.warning(f"Failed to send WebSocket message: {e}")
                disconnected.append(ws)
        
        # Remove disconnected clients
        for ws in disconnected:
            if ws in self.connections:
                self.connections.remove(ws)
    
    async def start_background_updates(self) -> None:
        """Start background task for status updates."""
        if self._is_running:
            return
        
        self._is_running = True
        asyncio.create_task(self._background_status_updates())
    
    async def stop_background_updates(self) -> None:
        """Stop background task for status updates."""
        self._is_running = False
    
    async def _background_status_updates(self) -> None:
        """Background task for status updates."""
        while self._is_running:
            try:
                # Send periodic status updates to WebSocket connections
                if self.connections:
                    status_data = {
                        "timestamp": datetime.now().isoformat(),
                        "type": "background_update",
                        "data": {
                            "active_connections": len(self.connections),
                            "monitoring_active": False,  # Will be set by main interface
                            "health_status": "healthy"  # Will be set by main interface
                        }
                    }
                    
                    await self.broadcast_update("background_update", status_data)
                
                await asyncio.sleep(60)  # Update every minute
                
            except Exception as e:
                logger.error(f"Background status update error: {e}")
                await asyncio.sleep(10)
    
    def get_connection_count(self) -> int:
        """Get the number of active WebSocket connections."""
        return len(self.connections)
    
    def close_all_connections(self) -> None:
        """Close all WebSocket connections."""
        for ws in self.connections:
            if not ws.closed:
                asyncio.create_task(ws.close())
        self.connections.clear()

