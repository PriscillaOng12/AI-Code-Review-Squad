"""Agents API endpoints."""
from fastapi import APIRouter
router = APIRouter()

@router.get("/status")
async def get_agents_status():
    return {"message": "All agents operational"}
