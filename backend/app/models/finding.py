"""Finding model."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Integer, Float, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base


class Severity(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    info = "info"


class Finding(Base):
    __tablename__ = "findings"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id = Column(UUID(as_uuid=True), ForeignKey("reviews.id"), nullable=False)
    agent_run_id = Column(UUID(as_uuid=True), ForeignKey("agent_runs.id"), nullable=False)
    file_path = Column(String, nullable=False)
    start_line = Column(Integer, nullable=False)
    end_line = Column(Integer, nullable=False)
    severity = Column(Enum(Severity), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    suggested_fix = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    rule_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    review = relationship("Review", backref="findings")
    agent_run = relationship("AgentRun", backref="findings")