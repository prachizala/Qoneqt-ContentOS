import os
import logging
from celery import Celery

logger = logging.getLogger("qoneqt_celery")

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "qoneqt_content_factory",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["workers.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_routes={
        "workers.tasks.pipeline_orchestrator": {"queue": "default"}
    }
)
