"""Common dependencies for API routes."""

from fastapi import Depends
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..core.auth import get_current_user, User
from ..core.rate_limit import RateLimiter


# Global rate limiter: allow 100 requests per minute per user
rate_limiter = RateLimiter(capacity=100, refill_rate=100/60)


def get_db() -> Session:
    yield from get_db()


async def get_current_active_user(user: User = Depends(get_current_user)) -> User:
    # Additional checks (e.g. disabled accounts) can be implemented here
    return user


def enforce_rate_limit(user: User = Depends(get_current_user)) -> None:
    key = f"{user.tenant_id}:{user.id}"
    rate_limiter.check(key)