"""Authentication and authorisation utilities."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from pydantic import BaseModel
from typing import Optional
from .config import settings

SECURITY_SCHEME = HTTPBearer(auto_error=False)


class User(BaseModel):
    id: int
    tenant_id: int
    email: str
    role: str


def decode_jwt(token: str) -> Optional[dict]:
    """Decode a JWT without verification in mock mode."""
    try:
        if settings.mock_llm:
            # In mock mode, accept any token and return dummy user info
            return {"sub": "1", "tenant": 1, "email": "demo@example.com", "role": "Owner"}
        payload = jwt.decode(token, settings.github_app_private_key_base64 or "", algorithms=["HS256"])
        return payload
    except JWTError:
        return None


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(SECURITY_SCHEME)) -> User:
    if credentials is None:
        # unauthenticated; in mock mode return a default user
        if settings.mock_llm:
            return User(id=1, tenant_id=1, email="demo@example.com", role="Owner")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = credentials.credentials
    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return User(id=int(payload.get("sub")), tenant_id=int(payload.get("tenant")), email=payload.get("email"), role=payload.get("role", "Viewer"))