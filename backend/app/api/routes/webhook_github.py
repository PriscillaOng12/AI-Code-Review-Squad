"""GitHub webhook handler."""

from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from ..deps import get_db
from ...core.config import settings
from ...models import review as review_model, repo as repo_model
from ...workers.celery_app import celery_app
import hmac
import hashlib
import json

router = APIRouter()


def verify_signature(request: Request, body: bytes) -> None:
    """Verify the GitHub webhook signature."""
    secret = settings.github_webhook_secret
    if not secret:
        return
    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        raise HTTPException(status_code=401, detail="Missing signature")
    sha_name, signature = signature.split("=", 1)
    mac = hmac.new(secret.encode(), msg=body, digestmod=hashlib.sha256)
    if not hmac.compare_digest(mac.hexdigest(), signature):
        raise HTTPException(status_code=401, detail="Invalid signature")


@router.post("/github")
async def handle_github_webhook(request: Request, db: Session = Depends(get_db)) -> dict[str, str]:
    raw_body = await request.body()
    verify_signature(request, raw_body)
    payload = request.headers.get("content-type")
    event = request.headers.get("X-GitHub-Event")
    data = await request.json()
    # Only handle pull_request events
    if event != "pull_request":
        return {"status": "ignored"}
    action = data.get("action")
    if action not in ("opened", "synchronize", "reopened"):
        return {"status": "ignored"}
    pr = data.get("pull_request", {})
    repo = data.get("repository", {})
    owner = repo.get("owner", {}).get("login")
    repo_name = repo.get("name")
    repo_external_id = str(repo.get("id"))
    # Ensure repo exists
    repository = db.query(repo_model.Repo).filter_by(external_id=repo_external_id).first()
    if not repository:
        # Create a tenant and repo on the fly in mock mode
        from ...models.tenant import Tenant
        from ...models.project import Project
        tenant = Tenant(name=owner, slug=owner)
        project = Project(tenant=tenant, name=repo_name)
        repository = repo_model.Repo(project=project, provider="github", external_id=repo_external_id, name=repo_name, default_branch=repo.get("default_branch", "main"))
        db.add_all([tenant, project, repository])
        db.commit()
    # Create review
    review = review_model.Review(repo=repository, pr_number=str(pr.get("number")), status=review_model.ReviewStatus.pending)
    db.add(review)
    db.commit()
    db.refresh(review)
    # Enqueue Celery task
    celery_app.send_task("tasks.process_review", args=[str(review.id)])
    return {"status": "accepted", "review_id": str(review.id)}