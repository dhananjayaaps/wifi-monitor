"""Celery tasks placeholder for future async jobs.

Uses in-memory broker/backend to avoid external Redis dependency. Replace with a
real broker (e.g., RabbitMQ/SQS) when scaling background tasks.
"""
from celery import Celery


celery_app = Celery(
	"wifi_monitor_tasks",
	broker="memory://",
	backend="cache+memory://",
)


@celery_app.task
def ping() -> str:
	return "pong"
