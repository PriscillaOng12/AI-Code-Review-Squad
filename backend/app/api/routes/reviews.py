"""Review API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..deps import get_db, get_current_active_user, enforce_rate_limit
from ...models.review import Review, ReviewStatus
from ...schemas.review import ReviewOut, ReviewDetailOut
from ...core.rbac import require_role

router = APIRouter()


@router.get("/reviews", response_model=List[ReviewOut])
def list_reviews(
    status: Optional[ReviewStatus] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user = Depends(get_current_active_user),
    _ = Depends(enforce_rate_limit),
) -> List[ReviewOut]:
    require_role(user, ["Viewer"])
    query = db.query(Review)
    if status:
        query = query.filter(Review.status == status)
    reviews = query.offset(offset).limit(limit).all()
    return reviews


@router.get("/reviews/{review_id}", response_model=ReviewDetailOut)
def get_review(review_id: str, db: Session = Depends(get_db), user = Depends(get_current_active_user), _ = Depends(enforce_rate_limit)) -> ReviewDetailOut:
    require_role(user, ["Viewer"])
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    # preload findings
    _ = review.findings
    return review