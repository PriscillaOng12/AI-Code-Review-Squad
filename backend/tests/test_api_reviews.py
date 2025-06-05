"""Tests for review API endpoints."""

import json
from app.models.tenant import Tenant
from app.models.project import Project
from app.models.repo import Repo
from app.models.review import Review


def test_list_reviews_empty(client):
    response = client.get('/api/reviews')
    assert response.status_code == 200
    assert response.json() == []


def test_create_review_and_list(client, db_session):
    # create tenant, project, repo, review
    tenant = Tenant(name="t", slug="t")
    project = Project(name="p", tenant=tenant)
    repo = Repo(name="r", provider="github", external_id="1", project=project, default_branch="main")
    review = Review(repo=repo, pr_number="1")
    db_session.add_all([tenant, project, repo, review])
    db_session.commit()
    r = client.get('/api/reviews')
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1