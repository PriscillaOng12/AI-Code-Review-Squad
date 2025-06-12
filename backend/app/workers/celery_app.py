"""Celery application setup."""

from celery import Celery
from ..core.config import settings

celery_app = Celery(
    "ai_code_review",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],
)

# Configure task routes for agents
celery_app.conf.task_routes = {
    "tasks.run_security_agent": {"queue": "security"},
    "tasks.run_style_agent": {"queue": "style"},
    "tasks.run_logic_agent": {"queue": "logic"},
    "tasks.run_performance_agent": {"queue": "performance"},
    "tasks.run_architecture_agent": {"queue": "architecture"},
    "tasks.process_review": {"queue": "default"},
}

celery_app.conf.task_default_queue = "default"