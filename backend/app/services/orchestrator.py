"""Orchestrates multi-agent review processing."""

from sqlalchemy.orm import Session
from typing import List
from ..core.database import SessionLocal
from ..models.review import Review, ReviewStatus
from ..models.agent_run import AgentRun, AgentRunStatus
from .diff_fetcher import fetch_changed_files
from ..workers.celery_app import celery_app


AGENT_NAMES = ["security", "style", "logic", "performance", "architecture"]


def start_review(review_id: str) -> None:
    """Fetch diffs and enqueue tasks for each agent."""
    db: Session = SessionLocal()
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        db.close()
        return
    review.status = ReviewStatus.running
    db.commit()
    # Create AgentRun entries and schedule tasks
    for agent_name in AGENT_NAMES:
        run = AgentRun(review_id=review.id, agent_name=agent_name, status=AgentRunStatus.pending)
        db.add(run)
        db.commit()
        db.refresh(run)
        celery_app.send_task(f"tasks.run_{agent_name}_agent", args=[str(review.id), str(run.id)])
    db.close()