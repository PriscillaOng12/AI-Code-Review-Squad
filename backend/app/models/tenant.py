"""Tenant model."""

import uuid
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from .base import Base


class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)