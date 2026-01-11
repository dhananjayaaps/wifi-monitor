"""Celery tasks placeholder for future async jobs."""
from celery import Celery
import os


celery_app = Celery(
	"wifi_monitor_tasks",
	broker=os.getenv("CELERY_BROKER_URL", os.getenv("REDIS_URL", "redis://localhost:6379/0")),
	backend=os.getenv("CELERY_RESULT_BACKEND", os.getenv("REDIS_URL", "redis://localhost:6379/0")),
)


@celery_app.task
def ping() -> str:
	return "pong"
