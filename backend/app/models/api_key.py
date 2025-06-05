"""API key model."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base


class APIKey(Base):
    __tablename__ = "api_keys"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    name = Column(String, nullable=False)
    hashed_key = Column(String, nullable=False)
    scopes = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    tenant = relationship("Tenant", backref="api_keys")