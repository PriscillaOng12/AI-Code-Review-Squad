"""AgentRun model."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base


class AgentRunStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class AgentRun(Base):
    __tablename__ = "agent_runs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id = Column(UUID(as_uuid=True), ForeignKey("reviews.id"), nullable=False)
    agent_name = Column(String, nullable=False)
    status = Column(Enum(AgentRunStatus), nullable=False, default=AgentRunStatus.pending)
    duration_ms = Column(Integer, nullable=True)
    metrics_json = Column(JSON, nullable=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    review = relationship("Review", backref="agent_runs")