"""Test webhook processing."""

import json
from app.models.review import Review


def test_webhook_creates_review(client, db_session):
    payload = {
        "action": "opened",
        "pull_request": {"number": 1},
        "repository": {
            "id": 123,
            "name": "demo-repo",
            "owner": {"login": "demo"},
            "default_branch": "main",
        },
    }
    headers = {"X-GitHub-Event": "pull_request", "Content-Type": "application/json"}
    res = client.post("/api/webhooks/github", data=json.dumps(payload), headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "accepted"
    # verify review created
    review = db_session.query(Review).first()
    assert review is not None