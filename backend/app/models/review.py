"""Review model."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base


class ReviewStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class Review(Base):
    __tablename__ = "reviews"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repo_id = Column(UUID(as_uuid=True), ForeignKey("repos.id"), nullable=False)
    pr_number = Column(String, nullable=False)
    status = Column(Enum(ReviewStatus), nullable=False, default=ReviewStatus.pending)
    stats_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    repo = relationship("Repo", backref="reviews")