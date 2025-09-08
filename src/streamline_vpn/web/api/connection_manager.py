"""
Connection Manager
=================

Manages VPN connections and their state.
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from ...utils.logging import get_logger

logger = get_logger(__name__)


class ConnectionStatus(Enum):
    """VPN connection status."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    ERROR = "error"


@dataclass
class ConnectionInfo:
    """VPN connection information."""
    id: str
    user_id: str
    server_id: str
    status: ConnectionStatus
    connected_at: Optional[datetime] = None
    bytes_uploaded: int = 0
    bytes_downloaded: int = 0
    session_duration: int = 0
    error_message: Optional[str] = None


class ConnectionManager:
    """Manages VPN connections."""
    
    def __init__(self):
        self._connections: Dict[str, ConnectionInfo] = {}
        self._user_connections: Dict[str, List[str]] = {}
        self._lock = asyncio.Lock()
    
    async def create_connection(
        self, 
        user_id: str, 
        server_id: str,
        connection_id: Optional[str] = None
    ) -> ConnectionInfo:
        """Create a new VPN connection."""
        if connection_id is None:
            connection_id = f"conn_{user_id}_{server_id}_{int(datetime.now().timestamp())}"
        
        async with self._lock:
            connection = ConnectionInfo(
                id=connection_id,
                user_id=user_id,
                server_id=server_id,
                status=ConnectionStatus.CONNECTING,
                connected_at=datetime.now(timezone.utc)
            )
            
            self._connections[connection_id] = connection
            
            if user_id not in self._user_connections:
                self._user_connections[user_id] = []
            self._user_connections[user_id].append(connection_id)
            
            logger.info(f"Created connection {connection_id} for user {user_id}")
            return connection
    
    async def get_connection(self, connection_id: str) -> Optional[ConnectionInfo]:
        """Get connection by ID."""
        return self._connections.get(connection_id)
    
    async def get_user_connections(self, user_id: str) -> List[ConnectionInfo]:
        """Get all connections for a user."""
        connection_ids = self._user_connections.get(user_id, [])
        return [self._connections[cid] for cid in connection_ids if cid in self._connections]
    
    async def update_connection_status(
        self, 
        connection_id: str, 
        status: ConnectionStatus,
        error_message: Optional[str] = None
    ) -> bool:
        """Update connection status."""
        async with self._lock:
            if connection_id not in self._connections:
                return False
            
            connection = self._connections[connection_id]
            connection.status = status
            if error_message:
                connection.error_message = error_message
            
            if status == ConnectionStatus.CONNECTED:
                connection.connected_at = datetime.now(timezone.utc)
            elif status == ConnectionStatus.DISCONNECTED:
                connection.connected_at = None
            
            logger.info(f"Updated connection {connection_id} status to {status.value}")
            return True
    
    async def update_connection_stats(
        self, 
        connection_id: str, 
        bytes_uploaded: int = 0, 
        bytes_downloaded: int = 0
    ) -> bool:
        """Update connection statistics."""
        async with self._lock:
            if connection_id not in self._connections:
                return False
            
            connection = self._connections[connection_id]
            connection.bytes_uploaded += bytes_uploaded
            connection.bytes_downloaded += bytes_downloaded
            
            if connection.connected_at:
                connection.session_duration = int(
                    (datetime.now(timezone.utc) - connection.connected_at).total_seconds()
                )
            
            return True
    
    async def disconnect_connection(self, connection_id: str) -> bool:
        """Disconnect a VPN connection."""
        async with self._lock:
            if connection_id not in self._connections:
                return False
            
            connection = self._connections[connection_id]
            connection.status = ConnectionStatus.DISCONNECTING
            
            # Simulate disconnection process
            await asyncio.sleep(0.1)
            
            connection.status = ConnectionStatus.DISCONNECTED
            connection.connected_at = None
            
            logger.info(f"Disconnected connection {connection_id}")
            return True
    
    async def remove_connection(self, connection_id: str) -> bool:
        """Remove a connection completely."""
        async with self._lock:
            if connection_id not in self._connections:
                return False
            
            connection = self._connections[connection_id]
            user_id = connection.user_id
            
            # Remove from user connections
            if user_id in self._user_connections:
                try:
                    self._user_connections[user_id].remove(connection_id)
                except ValueError:
                    pass
            
            # Remove from connections
            del self._connections[connection_id]
            
            logger.info(f"Removed connection {connection_id}")
            return True
    
    async def cleanup_old_connections(self, max_age_hours: int = 24) -> int:
        """Clean up old disconnected connections."""
        cutoff_time = datetime.now(timezone.utc).timestamp() - (max_age_hours * 3600)
        removed_count = 0
        
        async with self._lock:
            connections_to_remove = []
            
            for conn_id, connection in self._connections.items():
                if (connection.status == ConnectionStatus.DISCONNECTED and 
                    connection.connected_at and 
                    connection.connected_at.timestamp() < cutoff_time):
                    connections_to_remove.append(conn_id)
            
            for conn_id in connections_to_remove:
                await self.remove_connection(conn_id)
                removed_count += 1
        
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old connections")
        
        return removed_count


# Global connection manager instance
_connection_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager instance."""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager
