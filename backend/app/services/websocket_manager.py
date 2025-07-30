"""
WebSocket manager for real-time updates.
"""

from typing import Dict, List
from fastapi import WebSocket


class WebSocketManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, review_id: str):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        
        if review_id not in self.active_connections:
            self.active_connections[review_id] = []
        
        self.active_connections[review_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, review_id: str):
        """Remove a WebSocket connection."""
        if review_id in self.active_connections:
            self.active_connections[review_id].remove(websocket)
            
            if not self.active_connections[review_id]:
                del self.active_connections[review_id]
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket."""
        await websocket.send_text(message)
    
    async def broadcast_to_review(self, message: str, review_id: str):
        """Broadcast a message to all connections for a specific review."""
        if review_id in self.active_connections:
            for connection in self.active_connections[review_id]:
                try:
                    await connection.send_text(message)
                except:
                    # Remove broken connections
                    self.active_connections[review_id].remove(connection)
