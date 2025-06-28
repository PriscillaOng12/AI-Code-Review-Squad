"""Routes for querying findings."""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from sqlalchemy.orm import Session
from ..deps import get_db, get_current_active_user, enforce_rate_limit
from ...models.finding import Finding, Severity
from ...models.review import Review
from ...schemas.finding import FindingOut
from ...core.rbac import require_role

router = APIRouter()


@router.get("/reviews/{review_id}/findings", response_model=List[FindingOut])
def list_findings(
    review_id: str,
    severity: Optional[Severity] = Query(None),
    agent_name: Optional[str] = Query(None),
    file_path: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user = Depends(get_current_active_user),
    _ = Depends(enforce_rate_limit),
) -> List[FindingOut]:
    require_role(user, ["Viewer"])
    # ensure review exists
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    query = db.query(Finding).filter(Finding.review_id == review_id)
    if severity:
        query = query.filter(Finding.severity == severity)
    if agent_name:
        query = query.filter(Finding.agent_run.has(agent_name=agent_name))
    if file_path:
        query = query.filter(Finding.file_path.ilike(f"%{file_path}%"))
    return query.offset(offset).limit(limit).all()