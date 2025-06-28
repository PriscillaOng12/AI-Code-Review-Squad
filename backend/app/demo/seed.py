"""Seed demo data for local development."""

from ..core.database import SessionLocal
from ..models.tenant import Tenant
from ..models.project import Project
from ..models.repo import Repo


def seed() -> None:
    db = SessionLocal()
    # Create a demo tenant if none exists
    if not db.query(Tenant).first():
        tenant = Tenant(name="Demo Org", slug="demo-org")
        project = Project(name="Demo Project", tenant=tenant)
        repo = Repo(project=project, provider="github", external_id="demo/repo", name="demo-repo", default_branch="main")
        db.add_all([tenant, project, repo])
        db.commit()
        print("Seeded demo tenant, project and repo.")
    db.close()


if __name__ == "__main__":
    seed()