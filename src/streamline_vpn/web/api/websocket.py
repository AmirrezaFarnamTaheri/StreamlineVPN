"""WebSocket connection manager for real-time updates."""

from datetime import datetime
from typing import Dict

from fastapi import WebSocket

from ...utils.logging import get_logger
from .models import WebSocketMessage

logger = get_logger(__name__)


class WebSocketManager:
    """WebSocket connection manager."""

    def __init__(self):
        """Initialize WebSocket manager."""
        self.connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        """Accept WebSocket connection.

        Args:
            websocket: WebSocket connection
            user_id: User ID
        """
        await websocket.accept()
        self.connections[user_id] = websocket
        logger.info(f"WebSocket connected for user {user_id}")

    async def disconnect(self, user_id: str) -> None:
        """Disconnect WebSocket connection.

        Args:
            user_id: User ID
        """
        if user_id in self.connections:
            del self.connections[user_id]
            logger.info(f"WebSocket disconnected for user {user_id}")

    async def send_message(
        self, user_id: str, message: WebSocketMessage
    ) -> bool:
        """Send message to specific user.

        Args:
            user_id: User ID
            message: WebSocket message

        Returns:
            True if message sent successfully, False otherwise
        """
        if user_id in self.connections:
            websocket = self.connections[user_id]
            try:
                await websocket.send_text(message.json())
                return True
            except Exception as e:
                logger.error(
                    f"Failed to send WebSocket message to user {user_id}: {e}"
                )
                # Remove broken connection
                await self.disconnect(user_id)
                return False
        return False

    async def send_vpn_status(self, user_id: str, status_data: Dict) -> bool:
        """Send VPN status update to user.

        Args:
            user_id: User ID
            status_data: VPN status data

        Returns:
            True if message sent successfully, False otherwise
        """
        message = WebSocketMessage(
            type="vpn_status_update",
            data=status_data,
            timestamp=datetime.utcnow().isoformat(),
        )
        return await self.send_message(user_id, message)

    async def send_connection_update(
        self, user_id: str, connection_data: Dict
    ) -> bool:
        """Send connection update to user.

        Args:
            user_id: User ID
            connection_data: Connection data

        Returns:
            True if message sent successfully, False otherwise
        """
        message = WebSocketMessage(
            type="connection_update",
            data=connection_data,
            timestamp=datetime.utcnow().isoformat(),
        )
        return await self.send_message(user_id, message)

    async def handle_message(
        self, websocket: WebSocket, user_id: str, message_data: Dict
    ) -> None:
        """Handle incoming WebSocket message.

        Args:
            websocket: WebSocket connection
            user_id: User ID
            message_data: Message data
        """
        message_type = message_data.get("type")

        if message_type == "ping":
            response = WebSocketMessage(
                type="pong", data={}, timestamp=datetime.utcnow().isoformat()
            )
            await websocket.send_text(response.json())

        elif message_type == "request_status":
            # This would trigger a status update
            logger.info(f"Status requested by user {user_id}")

    async def broadcast_message(self, message: WebSocketMessage) -> int:
        """Broadcast message to all connected users.

        Args:
            message: WebSocket message

        Returns:
            Number of users message was sent to
        """
        sent_count = 0
        for user_id in list(self.connections.keys()):
            if await self.send_message(user_id, message):
                sent_count += 1

        return sent_count

    def get_connection_count(self) -> int:
        """Get number of active WebSocket connections.

        Returns:
            Number of active connections
        """
        return len(self.connections)

    def get_connected_users(self) -> list:
        """Get list of connected user IDs.

        Returns:
            List of connected user IDs
        """
        return list(self.connections.keys())
