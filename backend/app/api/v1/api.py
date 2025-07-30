"""
Main API router for version 1.
"""

from fastapi import APIRouter

# Import endpoint routers
from app.api.v1.endpoints import reviews, repositories, agents, webhooks, users

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
api_router.include_router(repositories.router, prefix="/repositories", tags=["repositories"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
