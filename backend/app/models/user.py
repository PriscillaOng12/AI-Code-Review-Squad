"""User model."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    email = Column(String, nullable=False, unique=True)
    role = Column(String, nullable=False, default="Viewer")
    github_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    tenant = relationship("Tenant", backref="users")