"""Audit log model."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base


class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)
    entity = Column(String, nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    tenant = relationship("Tenant", backref="audit_logs")
    user = relationship("User", backref="audit_logs")