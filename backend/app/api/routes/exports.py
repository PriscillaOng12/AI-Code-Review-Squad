"""Export endpoints for SARIF and analytics."""

import json
import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from ..deps import get_db, get_current_active_user
from ...models.review import Review
from ...models.finding import Finding
from ...core.rbac import require_role

router = APIRouter()


def generate_sarif(findings: list[Finding]) -> Dict[str, Any]:
    """Generate a minimal SARIF v2.1.0 document from findings."""
    results = []
    rules = {}
    for f in findings:
        rule_id = f.rule_id or f.agent_run.agent_name
        if rule_id not in rules:
            rules[rule_id] = {
                "id": rule_id,
                "name": f.title,
                "shortDescription": {"text": f.title},
                "fullDescription": {"text": f.description},
                "defaultConfiguration": {"level": f.severity},
            }
        results.append({
            "ruleId": rule_id,
            "message": {"text": f.description},
            "locations": [{
                "physicalLocation": {
                    "artifactLocation": {"uri": f.file_path},
                    "region": {"startLine": f.start_line, "endLine": f.end_line}
                }
            }]
        })
    sarif_doc = {
        "version": "2.1.0",
        "runs": [
            {
                "tool": {"driver": {"name": "ai-code-review-squad", "rules": list(rules.values())}},
                "results": results
            }
        ]
    }
    return sarif_doc


@router.get("/reviews/{review_id}/sarif")
def export_sarif(review_id: str, db: Session = Depends(get_db), user=Depends(get_current_active_user)):
    require_role(user, ["Viewer"])
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    findings = db.query(Finding).filter(Finding.review_id == review_id).all()
    return generate_sarif(findings)


@router.get("/reviews/{review_id}/comments", response_class=None)
def export_comments(review_id: str, db: Session = Depends(get_db), user=Depends(get_current_active_user)):
    require_role(user, ["Viewer"])
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    findings = db.query(Finding).filter(Finding.review_id == review_id).all()
    md_lines = []
    for f in findings:
        md_lines.append(f"### {f.title} ({f.severity})\n")
        md_lines.append(f"**File:** {f.file_path} ({f.start_line}-{f.end_line})\n")
        md_lines.append(f"**Description:** {f.description}\n")
        if f.suggested_fix:
            md_lines.append(f"**Suggested fix:** {f.suggested_fix}\n")
        md_lines.append("\n")
    return "\n".join(md_lines)


@router.get("/analytics/latest-manifest")
def get_latest_manifest(user=Depends(get_current_active_user)):
    """Return the latest manifest files for analytics tables."""
    require_role(user, ["Owner", "Maintainer"])
    manifest_dir = os.path.join(os.getcwd(), "analytics", "data", "_manifests")
    manifests: dict[str, dict[str, str]] = {}
    if not os.path.isdir(manifest_dir):
        return manifests
    for table in os.listdir(manifest_dir):
        table_path = os.path.join(manifest_dir, table)
        if not os.path.isdir(table_path):
            continue
        dates = sorted(os.listdir(table_path), reverse=True)
        if not dates:
            continue
        latest_date = dates[0]
        with open(os.path.join(table_path, latest_date), "r") as f:
            manifests[table] = json.load(f)
    return manifests