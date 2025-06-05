"""Database session and engine setup."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .config import settings


# SQLAlchemy engine; echo is disabled for production
engine = create_engine(settings.database_url, echo=False, future=True)

# Session factory
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

# Import Base from models to avoid duplication
from ..models.base import Base  # noqa: E402


def get_db():
    """Provide a SQLAlchemy session to FastAPI dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()