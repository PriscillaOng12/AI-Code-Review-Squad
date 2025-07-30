"""
Agent response model for individual agent analysis results.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base
from app.core.config import Severity, Confidence


class AgentResponse(Base):
    """Agent response model for individual agent analysis results."""
    __tablename__ = "agent_responses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Review association
    review_id = Column(UUID(as_uuid=True), ForeignKey("code_reviews.id"), nullable=False)
    
    # Agent information
    agent_type = Column(String(50), nullable=False, index=True)  # security, performance, style, logic, architecture
    agent_version = Column(String(20), nullable=True)
    
    # Analysis results
    findings = Column(JSON, nullable=True)  # Structured findings data
    summary = Column(Text, nullable=True)
    confidence = Column(Enum(Confidence), nullable=False)
    severity = Column(Enum(Severity), nullable=False)
    
    # Metrics
    execution_time_ms = Column(Integer, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    cost_cents = Column(Integer, nullable=True)
    
    # Status
    status = Column(String(20), default="completed")  # completed, failed, timeout
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    review = relationship("CodeReview", back_populates="agent_responses")
