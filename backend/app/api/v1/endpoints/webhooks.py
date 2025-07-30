"""
Webhook endpoints for GitHub integration.
"""

from fastapi import APIRouter, Request, HTTPException, Depends, Header
from typing import Optional
import json
import hashlib
import hmac

from app.core.config import settings
from app.services.webhook_service import WebhookService

router = APIRouter()


async def verify_github_signature(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None)
) -> bool:
    """Verify GitHub webhook signature."""
    if not x_hub_signature_256 or not settings.github_webhook_secret:
        return False
    
    body = await request.body()
    expected_signature = hmac.new(
        settings.github_webhook_secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    received_signature = x_hub_signature_256.replace("sha256=", "")
    return hmac.compare_digest(expected_signature, received_signature)


@router.post("/github")
async def github_webhook(
    request: Request,
    x_github_event: Optional[str] = Header(None),
    verified: bool = Depends(verify_github_signature)
):
    """Handle GitHub webhook events."""
    
    if not verified:
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    if not x_github_event:
        raise HTTPException(status_code=400, detail="Missing event type")
    
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    webhook_service = WebhookService()
    
    # Handle different event types
    if x_github_event == "pull_request":
        return await webhook_service.handle_pull_request(payload)
    elif x_github_event == "push":
        return await webhook_service.handle_push(payload)
    elif x_github_event == "ping":
        return {"message": "pong"}
    else:
        return {"message": f"Event {x_github_event} not handled"}


@router.get("/test")
async def test_webhook():
    """Test endpoint for webhook functionality."""
    return {
        "message": "Webhook endpoint is working",
        "signature_verification": "enabled" if settings.github_webhook_secret else "disabled"
    }
