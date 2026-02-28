from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery_app = Celery(
    "taskflow",
    broker=settings.celery_broker,
    backend=settings.celery_backend,
    include=["app.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    task_soft_time_limit=240,
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_retry_delay=60,
    task_max_retries=3,
)

# Scheduled tasks
celery_app.conf.beat_schedule = {
    "calculate-project-health-metrics": {
        "task": "app.tasks.calculate_project_health",
        "schedule": crontab(minute="*/30"),  # Every 30 minutes
    },
}
