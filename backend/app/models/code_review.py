"""
Code review model for tracking review sessions.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base
from app.core.config import ReviewStatus


class CodeReview(Base):
    """Code review model for tracking review sessions."""
    __tablename__ = "code_reviews"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # GitHub information
    repository_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id"), nullable=False)
    commit_hash = Column(String(40), nullable=False, index=True)
    pr_number = Column(Integer, nullable=True, index=True)
    branch = Column(String(255), nullable=True)
    
    # Review metadata
    status = Column(Enum(ReviewStatus), default=ReviewStatus.PENDING, index=True)
    trigger_event = Column(String(50), nullable=True)  # webhook, manual, scheduled
    
    # Timing information
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Summary statistics
    total_files = Column(Integer, default=0)
    analyzed_files = Column(Integer, default=0)
    total_findings = Column(Integer, default=0)
    critical_findings = Column(Integer, default=0)
    high_findings = Column(Integer, default=0)
    medium_findings = Column(Integer, default=0)
    low_findings = Column(Integer, default=0)
    
    # Overall assessment
    overall_score = Column(Float, nullable=True)  # 0-100 quality score
    recommendation = Column(Text, nullable=True)
    
    # Foreign keys
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    repository = relationship("Repository", back_populates="reviews")
    created_by = relationship("User", back_populates="reviews")
    agent_responses = relationship("AgentResponse", back_populates="review", cascade="all, delete-orphan")
    file_analyses = relationship("FileAnalysis", back_populates="review", cascade="all, delete-orphan")
