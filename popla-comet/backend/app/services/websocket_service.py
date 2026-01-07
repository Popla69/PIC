"""WebSocket service for real-time updates."""

from typing import Dict, Set
from fastapi import WebSocket
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.user_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        
        if client_id not in self.active_connections:
            self.active_connections[client_id] = set()
        
        self.active_connections[client_id].add(websocket)
        self.user_connections[client_id] = websocket
        
        logger.info(f"Client {client_id} connected")
        
        await self.send_personal_message(
            {"type": "connection", "message": "Connected successfully"},
            websocket
        )
    
    def disconnect(self, websocket: WebSocket, client_id: str):
        """Remove a WebSocket connection."""
        if client_id in self.active_connections:
            self.active_connections[client_id].discard(websocket)
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]
        
        if client_id in self.user_connections:
            del self.user_connections[client_id]
        
        logger.info(f"Client {client_id} disconnected")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific client."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
    
    async def send_to_client(self, message: dict, client_id: str):
        """Send a message to all connections of a client."""
        if client_id in self.active_connections:
            for connection in self.active_connections[client_id]:
                await self.send_personal_message(message, connection)
    
    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients."""
        for connections in self.active_connections.values():
            for connection in connections:
                await self.send_personal_message(message, connection)
    
    async def send_progress_update(
        self,
        client_id: str,
        analysis_id: str,
        progress: int,
        status: str,
        message: str = None
    ):
        """Send progress update to a client."""
        update = {
            "type": "progress",
            "analysis_id": analysis_id,
            "progress": progress,
            "status": status
        }
        
        if message:
            update["message"] = message
        
        await self.send_to_client(update, client_id)
    
    async def send_analysis_complete(
        self,
        client_id: str,
        analysis_id: str,
        result: dict
    ):
        """Send analysis completion notification."""
        message = {
            "type": "analysis_complete",
            "analysis_id": analysis_id,
            "result": result
        }
        
        await self.send_to_client(message, client_id)
    
    async def send_error(
        self,
        client_id: str,
        analysis_id: str,
        error: str
    ):
        """Send error notification."""
        message = {
            "type": "error",
            "analysis_id": analysis_id,
            "error": error
        }
        
        await self.send_to_client(message, client_id)


connection_manager = ConnectionManager()
