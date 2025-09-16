"""
WebSocket routes for real-time communication.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
import json
import asyncio

websocket_router = APIRouter()

# Store active connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Remove broken connections
                self.active_connections.remove(connection)

manager = ConnectionManager()


@websocket_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "ping":
                await manager.send_personal_message(
                    json.dumps({"type": "pong", "timestamp": "2024-01-01T00:00:00Z"}),
                    websocket
                )
            elif message.get("type") == "subscribe":
                # Subscribe to updates
                await manager.send_personal_message(
                    json.dumps({"type": "subscribed", "channel": message.get("channel")}),
                    websocket
                )
            elif message.get("type") == "get_status":
                # Send current status
                status = await get_current_status()
                await manager.send_personal_message(
                    json.dumps({"type": "status", "data": status}),
                    websocket
                )
            else:
                # Echo back unknown messages
                await manager.send_personal_message(
                    json.dumps({"type": "echo", "original": message}),
                    websocket
                )
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


async def get_current_status() -> Dict[str, Any]:
    """Get current system status for WebSocket clients."""
    try:
        from ...core.source_manager import SourceManager
        from ...core.merger import StreamlineVPNMerger
        
        source_manager = SourceManager()
        merger = StreamlineVPNMerger()
        
        sources = source_manager.get_all_sources()
        stats = merger.get_statistics()
        
        return {
            "sources_count": len(sources),
            "statistics": stats,
            "status": "healthy"
        }
    except Exception as e:
        return {
            "error": str(e),
            "status": "error"
        }


async def broadcast_status_update():
    """Broadcast status update to all connected clients."""
    status = await get_current_status()
    await manager.broadcast(json.dumps({
        "type": "status_update",
        "data": status,
        "timestamp": "2024-01-01T00:00:00Z"
    }))


async def broadcast_processing_update(update: Dict[str, Any]):
    """Broadcast processing update to all connected clients."""
    await manager.broadcast(json.dumps({
        "type": "processing_update",
        "data": update,
        "timestamp": "2024-01-01T00:00:00Z"
    }))

