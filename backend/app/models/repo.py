"""Repository model."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base


class Repo(Base):
    __tablename__ = "repos"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    provider = Column(String, nullable=False)
    external_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    default_branch = Column(String, nullable=False, default="main")
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", backref="repos")