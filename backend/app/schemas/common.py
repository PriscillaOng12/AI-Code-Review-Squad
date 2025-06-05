"""Common schema utilities."""

from pydantic import BaseModel


class TimestampMixin(BaseModel):
    created_at: str
    class Config:
        orm_mode = True