import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from streamline_vpn.utils.logging import get_logger

logger = get_logger(__name__)
websocket_router = APIRouter()

@websocket_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Handles WebSocket connections for real-time communication.
    """
    await websocket.accept()
    client_id = str(uuid.uuid4())
    logger.info(f"WebSocket client connected: {client_id}")
    await websocket.send_json(
        {"type": "connection", "status": "connected", "client_id": client_id}
    )
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            else:
                # Echo back any other messages
                await websocket.send_json({"type": "echo", "received": data})
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected: {client_id}")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}", exc_info=True)
        # Attempt to close gracefully
        await websocket.close(code=1011)