"""
Celery application configuration for StoFlow.

This module configures Celery for asynchronous task processing.
Tasks are defined in the tasks/ directory.

Usage:
    # Start worker
    celery -A celery_app worker --loglevel=info --concurrency=4

    # Start beat scheduler
    celery -A celery_app beat --loglevel=info

    # Start Flower monitoring (optional)
    celery -A celery_app flower --port=5555
"""
from celery import Celery
from kombu import Exchange, Queue

from shared.config import settings

# Create Celery app
celery_app = Celery(
    "stoflow",
    broker=settings.celery_broker,
    backend=settings.celery_backend,
    include=[
        "tasks.marketplace_tasks",
        "tasks.cleanup_tasks",
        "tasks.notification_tasks",
    ],
)

# Celery configuration
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # Timezone
    timezone="Europe/Paris",
    enable_utc=True,

    # Task tracking
    task_track_started=True,
    result_extended=True,  # Store additional task metadata

    # Task execution limits
    task_time_limit=settings.celery_task_time_limit,
    task_soft_time_limit=settings.celery_task_soft_time_limit,

    # Worker settings
    worker_prefetch_multiplier=settings.celery_worker_prefetch_multiplier,
    worker_concurrency=settings.celery_worker_concurrency,

    # Reliability
    task_acks_late=True,  # Acknowledge after task completes
    task_reject_on_worker_lost=True,  # Requeue if worker dies

    # Result backend
    result_expires=86400,  # Results expire after 24 hours

    # Task routing (queues)
    task_default_queue="default",
    task_queues=(
        Queue("default", Exchange("default"), routing_key="default"),
        Queue("marketplace", Exchange("marketplace"), routing_key="marketplace.#"),
        Queue("cleanup", Exchange("cleanup"), routing_key="cleanup.#"),
        Queue("notifications", Exchange("notifications"), routing_key="notification.#"),
    ),
    task_routes={
        "tasks.marketplace_tasks.*": {"queue": "marketplace"},
        "tasks.cleanup_tasks.*": {"queue": "cleanup"},
        "tasks.notification_tasks.*": {"queue": "notifications"},
    },

    # Beat schedule (periodic tasks)
    beat_schedule={
        "cleanup-old-tasks": {
            "task": "tasks.cleanup_tasks.cleanup_old_task_records",
            "schedule": 3600.0,  # Every hour
        },
        "sync-marketplace-orders": {
            "task": "tasks.marketplace_tasks.sync_all_marketplace_orders",
            "schedule": 900.0,  # Every 15 minutes
        },
    },
)


# Task base class with default retry settings
class BaseTaskWithRetry(celery_app.Task):
    """Base task class with default retry behavior."""

    autoretry_for = (Exception,)
    retry_backoff = True
    retry_backoff_max = 600  # Max 10 minutes between retries
    retry_jitter = True
    max_retries = 3


# Register as default base
celery_app.Task = BaseTaskWithRetry


# Register task tracking signals
from services.celery.signals import setup_celery_signals
setup_celery_signals()


if __name__ == "__main__":
    celery_app.start()
