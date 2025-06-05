"""Base model that other SQLAlchemy models inherit from."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass