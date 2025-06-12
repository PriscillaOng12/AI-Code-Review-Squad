"""Celery tasks for processing reviews and running agents."""

from celery import shared_task
from ..services.orchestrator import start_review
from ..services.diff_fetcher import fetch_changed_files
from ..services.agents.security_agent import SecurityAgent
from ..services.agents.style_agent import StyleAgent
from ..services.agents.logic_agent import LogicAgent
from ..services.agents.performance_agent import PerformanceAgent
from ..services.agents.architecture_agent import ArchitectureAgent
from ..core.database import SessionLocal
from ..models import review as review_model
from ..models.agent_run import AgentRun, AgentRunStatus
from ..models.finding import Finding
from datetime import datetime


@shared_task(name="tasks.process_review")
def process_review_task(review_id: str) -> None:
    """Celery entrypoint to start a review."""
    start_review(review_id)


def _run_agent(review_id: str, agent_run_id: str, agent) -> None:
    db = SessionLocal()
    run = db.query(AgentRun).filter(AgentRun.id == agent_run_id).first()
    if not run:
        db.close()
        return
    run.status = AgentRunStatus.running
    run.started_at = datetime.utcnow()
    db.commit()
    review = db.query(review_model.Review).filter(review_model.Review.id == review_id).first()
    changed_files = fetch_changed_files(review.repo.name, review.pr_number)
    findings_data = agent.analyze(changed_files)
    findings_objs = []
    for f in findings_data:
        finding = Finding(
            review_id=review.id,
            agent_run_id=run.id,
            file_path=f["file_path"],
            start_line=f["start_line"],
            end_line=f["end_line"],
            severity=f["severity"],
            title=f["title"],
            description=f["description"],
            suggested_fix=f.get("suggested_fix"),
            confidence=f.get("confidence"),
            rule_id=f.get("rule_id"),
        )
        findings_objs.append(finding)
    db.add_all(findings_objs)
    run.status = AgentRunStatus.completed
    run.finished_at = datetime.utcnow()
    run.duration_ms = int((run.finished_at - run.started_at).total_seconds() * 1000)
    db.commit()
    # If all agent runs are completed, set review status
    runs = db.query(AgentRun).filter(AgentRun.review_id == review_id).all()
    if runs and all(r.status == AgentRunStatus.completed for r in runs):
        review.status = review_model.ReviewStatus.completed
        db.commit()
    db.close()


@shared_task(name="tasks.run_security_agent")
def run_security_agent(review_id: str, agent_run_id: str) -> None:
    _run_agent(review_id, agent_run_id, SecurityAgent())


@shared_task(name="tasks.run_style_agent")
def run_style_agent(review_id: str, agent_run_id: str) -> None:
    _run_agent(review_id, agent_run_id, StyleAgent())


@shared_task(name="tasks.run_logic_agent")
def run_logic_agent(review_id: str, agent_run_id: str) -> None:
    _run_agent(review_id, agent_run_id, LogicAgent())


@shared_task(name="tasks.run_performance_agent")
def run_performance_agent(review_id: str, agent_run_id: str) -> None:
    _run_agent(review_id, agent_run_id, PerformanceAgent())


@shared_task(name="tasks.run_architecture_agent")
def run_architecture_agent(review_id: str, agent_run_id: str) -> None:
    _run_agent(review_id, agent_run_id, ArchitectureAgent())