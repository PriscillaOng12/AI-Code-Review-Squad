"""
Celery configuration for async task processing.
"""

from celery import Celery
from app.core.config import settings

# Create Celery instance
celery = Celery(
    "ai-code-review-squad",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.services.tasks"]
)

# Celery configuration
celery.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    
    # Task routing
    task_routes={
        "app.services.tasks.process_code_review": {"queue": "reviews"},
        "app.services.tasks.cleanup_old_reviews": {"queue": "maintenance"},
        "app.services.tasks.send_notification": {"queue": "notifications"},
    },
    
    # Beat schedule for periodic tasks
    beat_schedule={
        "cleanup-old-reviews": {
            "task": "app.services.tasks.cleanup_old_reviews",
            "schedule": 3600.0,  # Run every hour
        },
        "health-check-agents": {
            "task": "app.services.tasks.health_check_agents",
            "schedule": 300.0,  # Run every 5 minutes
        },
    },
    
    # Result backend settings
    result_expires=3600,
    result_persistent=True,
    
    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_time_limit=settings.review_timeout_minutes * 60,
    task_soft_time_limit=(settings.review_timeout_minutes - 1) * 60,
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)
