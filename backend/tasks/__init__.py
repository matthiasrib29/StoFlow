"""
Celery tasks for StoFlow.

This package contains all asynchronous tasks handled by Celery workers.

Task modules:
- marketplace_tasks: Publication, sync, and deletion for all marketplaces
- cleanup_tasks: Periodic cleanup and maintenance tasks
- notification_tasks: User notifications and alerts
"""
from tasks.marketplace_tasks import (
    publish_product,
    update_listing,
    delete_listing,
    sync_inventory,
    sync_orders,
    sync_all_marketplace_orders,
)
from tasks.cleanup_tasks import (
    cleanup_old_task_records,
    cleanup_expired_jobs,
)
from tasks.notification_tasks import (
    send_task_completion_notification,
)

__all__ = [
    # Marketplace tasks
    "publish_product",
    "update_listing",
    "delete_listing",
    "sync_inventory",
    "sync_orders",
    "sync_all_marketplace_orders",
    # Cleanup tasks
    "cleanup_old_task_records",
    "cleanup_expired_jobs",
    # Notification tasks
    "send_task_completion_notification",
]
