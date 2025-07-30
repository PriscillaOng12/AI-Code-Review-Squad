"""
Pydantic schemas for code reviews.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

from app.core.config import ReviewStatus, Severity, Confidence


class ReviewCreate(BaseModel):
    """Schema for creating a new review."""
    repository_id: UUID
    commit_hash: str = Field(..., min_length=40, max_length=40)
    pr_number: Optional[int] = None
    branch: Optional[str] = None
    trigger_event: Optional[str] = "manual"


class ReviewUpdate(BaseModel):
    """Schema for updating a review."""
    status: Optional[ReviewStatus] = None
    overall_score: Optional[float] = Field(None, ge=0, le=100)
    recommendation: Optional[str] = None


class AgentResponseSchema(BaseModel):
    """Schema for agent response data."""
    id: UUID
    agent_type: str
    findings: Optional[Dict[str, Any]] = None
    summary: Optional[str] = None
    confidence: Confidence
    severity: Severity
    execution_time_ms: Optional[int] = None
    tokens_used: Optional[int] = None
    cost_cents: Optional[int] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class FileAnalysisSchema(BaseModel):
    """Schema for file analysis data."""
    id: UUID
    file_path: str
    file_hash: str
    language: Optional[str] = None
    security_findings: Optional[Dict[str, Any]] = None
    performance_findings: Optional[Dict[str, Any]] = None
    style_findings: Optional[Dict[str, Any]] = None
    logic_findings: Optional[Dict[str, Any]] = None
    architecture_findings: Optional[Dict[str, Any]] = None
    complexity_score: Optional[float] = None
    maintainability_score: Optional[float] = None

    class Config:
        from_attributes = True


class ReviewResponse(BaseModel):
    """Schema for review response data."""
    id: UUID
    repository_id: UUID
    commit_hash: str
    pr_number: Optional[int] = None
    branch: Optional[str] = None
    status: ReviewStatus
    trigger_event: Optional[str] = None
    
    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    
    # Statistics
    total_files: int = 0
    analyzed_files: int = 0
    total_findings: int = 0
    critical_findings: int = 0
    high_findings: int = 0
    medium_findings: int = 0
    low_findings: int = 0
    
    # Assessment
    overall_score: Optional[float] = None
    recommendation: Optional[str] = None
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    # Related data
    agent_responses: List[AgentResponseSchema] = []
    file_analyses: List[FileAnalysisSchema] = []

    class Config:
        from_attributes = True


class ReviewSummary(BaseModel):
    """Condensed review summary for list views."""
    id: UUID
    repository_id: UUID
    commit_hash: str
    status: ReviewStatus
    total_findings: int
    overall_score: Optional[float] = None
    created_at: datetime
    duration_seconds: Optional[int] = None

    class Config:
        from_attributes = True
