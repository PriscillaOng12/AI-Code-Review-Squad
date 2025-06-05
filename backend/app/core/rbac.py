"""Role based access control helpers."""

from fastapi import HTTPException, status
from typing import List
from .auth import User


ROLE_HIERARCHY = ["Viewer", "Reviewer", "Maintainer", "Owner"]


def require_role(user: User, allowed: List[str]) -> None:
    """Ensure that the user’s role is in the allowed list or higher."""
    user_index = ROLE_HIERARCHY.index(user.role)
    allowed_indices = [ROLE_HIERARCHY.index(role) for role in allowed]
    if user_index < min(allowed_indices):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")