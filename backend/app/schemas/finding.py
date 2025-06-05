"""Schemas for findings."""

from pydantic import BaseModel
from datetime import datetime


class FindingOut(BaseModel):
    id: str
    review_id: str
    agent_run_id: str
    file_path: str
    start_line: int
    end_line: int
    severity: str
    title: str
    description: str
    suggested_fix: str | None
    confidence: float | None
    rule_id: str | None
    created_at: datetime

    class Config:
        orm_mode = True