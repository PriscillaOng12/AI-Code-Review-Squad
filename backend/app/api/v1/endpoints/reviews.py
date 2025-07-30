"""
Reviews API endpoints.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.code_review import CodeReview
from app.schemas.review import ReviewCreate, ReviewResponse, ReviewUpdate
from app.services.review_service import ReviewService
from app.services.websocket_manager import WebSocketManager

router = APIRouter()
websocket_manager = WebSocketManager()


@router.post("/", response_model=ReviewResponse)
async def create_review(
    review_data: ReviewCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new code review."""
    review_service = ReviewService(db)
    return await review_service.create_review(review_data)


@router.get("/", response_model=List[ReviewResponse])
async def list_reviews(
    skip: int = 0,
    limit: int = 100,
    repository_id: Optional[UUID] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List code reviews with optional filtering."""
    review_service = ReviewService(db)
    return await review_service.list_reviews(
        skip=skip,
        limit=limit,
        repository_id=repository_id,
        status=status
    )


@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review(
    review_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific code review by ID."""
    review_service = ReviewService(db)
    review = await review_service.get_review(review_id)
    
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    return review


@router.put("/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_id: UUID,
    review_update: ReviewUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a code review."""
    review_service = ReviewService(db)
    review = await review_service.update_review(review_id, review_update)
    
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    return review


@router.delete("/{review_id}")
async def delete_review(
    review_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a code review."""
    review_service = ReviewService(db)
    success = await review_service.delete_review(review_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Review not found")
    
    return {"message": "Review deleted successfully"}


@router.post("/{review_id}/trigger")
async def trigger_review(
    review_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger a code review analysis."""
    review_service = ReviewService(db)
    success = await review_service.trigger_review_analysis(review_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Review not found")
    
    return {"message": "Review analysis triggered"}


@router.websocket("/{review_id}/ws")
async def review_websocket(websocket: WebSocket, review_id: UUID):
    """WebSocket endpoint for real-time review updates."""
    await websocket_manager.connect(websocket, str(review_id))
    
    try:
        while True:
            # Keep connection alive and handle any incoming messages
            data = await websocket.receive_text()
            # Echo back for heartbeat
            await websocket.send_text(f"pong: {data}")
    
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, str(review_id))


@router.get("/{review_id}/agents", response_model=List[dict])
async def get_review_agent_responses(
    review_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get all agent responses for a specific review."""
    review_service = ReviewService(db)
    responses = await review_service.get_agent_responses(review_id)
    return responses


@router.get("/{review_id}/files")
async def get_review_files(
    review_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get file analysis results for a specific review."""
    review_service = ReviewService(db)
    files = await review_service.get_file_analyses(review_id)
    return files


@router.get("/{review_id}/metrics")
async def get_review_metrics(
    review_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get metrics and statistics for a specific review."""
    review_service = ReviewService(db)
    metrics = await review_service.get_review_metrics(review_id)
    return metrics
