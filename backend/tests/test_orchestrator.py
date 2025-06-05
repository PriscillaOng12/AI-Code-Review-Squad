"""Tests for orchestrator logic."""

from app.services.orchestrator import start_review
from app.models.review import Review, ReviewStatus
from app.models.repo import Repo
from app.models.project import Project
from app.models.tenant import Tenant


def test_start_review_creates_agent_runs(db_session):
    tenant = Tenant(name="t", slug="t")
    project = Project(name="p", tenant=tenant)
    repo = Repo(name="r", provider="github", external_id="1", project=project, default_branch="main")
    review = Review(repo=repo, pr_number="1")
    db_session.add_all([tenant, project, repo, review])
    db_session.commit()
    start_review(str(review.id))
    # after start_review, review status should be running
    db_session.refresh(review)
    assert review.status == ReviewStatus.running
    # There should be 5 agent runs
    assert len(review.agent_runs) == 5