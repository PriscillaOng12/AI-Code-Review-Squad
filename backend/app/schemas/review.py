"""Schemas for reviews."""

from pydantic import BaseModel
from typing import Optional, List
from .finding import FindingOut
from datetime import datetime


class ReviewOut(BaseModel):
    id: str
    repo_id: str
    pr_number: str
    status: str
    created_at: datetime
    updated_at: datetime
    stats_json: Optional[dict] = None

    class Config:
        orm_mode = True


class ReviewDetailOut(ReviewOut):
    findings: List[FindingOut]