"""
WebSocket handlers for real-time code review updates.
"""

import json
from typing import Dict, Any, List
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.code_review import CodeReview, ReviewStatus
from app.models.user import User


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """Accept new WebSocket connection."""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, user_id: int):
        """Remove WebSocket connection."""
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
    
    async def send_personal_message(self, message: str, user_id: int):
        """Send message to specific user."""
        if user_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(message)
                except:
                    disconnected.append(connection)
            
            # Clean up disconnected connections
            for conn in disconnected:
                self.active_connections[user_id].remove(conn)
    
    async def send_review_update(self, review_id: int, user_id: int, update_data: Dict[str, Any]):
        """Send review update to user."""
        message = json.dumps({
            "type": "review_update",
            "review_id": review_id,
            "data": update_data
        })
        await self.send_personal_message(message, user_id)
    
    async def send_finding_update(self, review_id: int, user_id: int, finding_data: Dict[str, Any]):
        """Send new finding to user."""
        message = json.dumps({
            "type": "new_finding",
            "review_id": review_id,
            "finding": finding_data
        })
        await self.send_personal_message(message, user_id)
    
    async def send_review_complete(self, review_id: int, user_id: int, summary: Dict[str, Any]):
        """Send review completion notification."""
        message = json.dumps({
            "type": "review_complete",
            "review_id": review_id,
            "summary": summary
        })
        await self.send_personal_message(message, user_id)
    
    async def send_agent_progress(self, review_id: int, user_id: int, agent_name: str, progress: Dict[str, Any]):
        """Send agent progress update."""
        message = json.dumps({
            "type": "agent_progress",
            "review_id": review_id,
            "agent": agent_name,
            "progress": progress
        })
        await self.send_personal_message(message, user_id)


# Global connection manager instance
manager = ConnectionManager()


class WebSocketService:
    """Service for WebSocket operations."""
    
    @staticmethod
    async def notify_review_status_change(review_id: int, status: ReviewStatus):
        """Notify user of review status change."""
        # Get review and user info
        db = next(get_db())
        try:
            review = db.query(CodeReview).filter(CodeReview.id == review_id).first()
            if not review:
                return
            
            user_id = review.repository.user_id
            
            await manager.send_review_update(
                review_id=review_id,
                user_id=user_id,
                update_data={
                    "status": status.value,
                    "timestamp": review.updated_at.isoformat() if review.updated_at else None
                }
            )
        finally:
            db.close()
    
    @staticmethod
    async def notify_new_finding(review_id: int, finding_data: Dict[str, Any]):
        """Notify user of new finding."""
        db = next(get_db())
        try:
            review = db.query(CodeReview).filter(CodeReview.id == review_id).first()
            if not review:
                return
            
            user_id = review.repository.user_id
            
            await manager.send_finding_update(
                review_id=review_id,
                user_id=user_id,
                finding_data=finding_data
            )
        finally:
            db.close()
    
    @staticmethod
    async def notify_review_complete(review_id: int, summary: Dict[str, Any]):
        """Notify user of review completion."""
        db = next(get_db())
        try:
            review = db.query(CodeReview).filter(CodeReview.id == review_id).first()
            if not review:
                return
            
            user_id = review.repository.user_id
            
            await manager.send_review_complete(
                review_id=review_id,
                user_id=user_id,
                summary=summary
            )
        finally:
            db.close()
    
    @staticmethod
    async def notify_agent_progress(review_id: int, agent_name: str, progress: Dict[str, Any]):
        """Notify user of agent progress."""
        db = next(get_db())
        try:
            review = db.query(CodeReview).filter(CodeReview.id == review_id).first()
            if not review:
                return
            
            user_id = review.repository.user_id
            
            await manager.send_agent_progress(
                review_id=review_id,
                user_id=user_id,
                agent_name=agent_name,
                progress=progress
            )
        finally:
            db.close()


async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """Main WebSocket endpoint handler."""
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "ping":
                    # Respond to ping with pong
                    await websocket.send_text(json.dumps({"type": "pong"}))
                
                elif message_type == "subscribe_review":
                    # Subscribe to specific review updates
                    review_id = message.get("review_id")
                    if review_id:
                        # Verify user has access to this review
                        db = next(get_db())
                        try:
                            review = db.query(CodeReview).join(CodeReview.repository).filter(
                                CodeReview.id == review_id,
                                CodeReview.repository.has(user_id=user_id)
                            ).first()
                            
                            if review:
                                await websocket.send_text(json.dumps({
                                    "type": "subscribed",
                                    "review_id": review_id
                                }))
                            else:
                                await websocket.send_text(json.dumps({
                                    "type": "error",
                                    "message": "Access denied or review not found"
                                }))
                        finally:
                            db.close()
                
                else:
                    # Unknown message type
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": f"Unknown message type: {message_type}"
                    }))
            
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        print(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(websocket, user_id)
