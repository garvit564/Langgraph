import logging
from celery import Celery
from worker_service.config import get_worker_settings

logger = logging.getLogger(__name__)
settings = get_worker_settings()

celery_app = Celery(
    "agent_desk_worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["worker_service.tasks.email_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
)
