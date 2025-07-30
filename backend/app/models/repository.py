"""
Repository model for GitHub repositories.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base


class Repository(Base):
    """Repository model for GitHub repositories."""
    __tablename__ = "repositories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False, unique=True, index=True)  # owner/repo
    github_id = Column(Integer, nullable=False, unique=True, index=True)
    clone_url = Column(String(500), nullable=False)
    webhook_secret = Column(String(255), nullable=True)
    default_branch = Column(String(100), default="main")
    language = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Configuration
    auto_review_enabled = Column(Boolean, default=True)
    review_on_pr = Column(Boolean, default=True)
    review_on_push = Column(Boolean, default=False)
    
    # Owner
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="repositories")
    reviews = relationship("CodeReview", back_populates="repository")
