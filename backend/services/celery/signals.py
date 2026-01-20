"""
Celery signals for automatic task tracking.

These signals hook into Celery's task lifecycle to automatically
update CeleryTaskRecord entries.
"""
import asyncio

from celery.signals import (
    before_task_publish,
    task_prerun,
    task_postrun,
    task_failure,
    task_retry,
    task_revoked,
)

from shared.database import SessionLocal
from shared.logging_setup import get_logger
from services.celery.task_tracking_service import TaskTrackingService

logger = get_logger(__name__)


def _send_websocket_update(user_id: int, event: str, data: dict) -> None:
    """
    Send WebSocket update to user.

    Args:
        user_id: User ID
        event: Event name
        data: Event data
    """
    try:
        from services.websocket_service import sio

        room = f"user_{user_id}"

        # Create a new event loop for sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                sio.emit(event, data, room=room)
            )
        finally:
            loop.close()

        logger.debug(f"Sent WebSocket {event} to room {room}")
    except Exception as e:
        # Don't fail the signal if WebSocket fails
        logger.warning(f"Failed to send WebSocket update: {e}")


def _extract_task_metadata(kwargs: dict) -> dict:
    """
    Extract marketplace metadata from task kwargs.

    Args:
        kwargs: Task keyword arguments

    Returns:
        Dict with marketplace, action_code, product_id, user_id
    """
    return {
        "marketplace": kwargs.get("marketplace"),
        "action_code": _infer_action_code(kwargs),
        "product_id": kwargs.get("product_id"),
        "user_id": kwargs.get("user_id"),
    }


def _infer_action_code(kwargs: dict) -> str | None:
    """Infer action code from task name or kwargs."""
    # Try to infer from task name in headers
    # This is a fallback - usually set explicitly
    return kwargs.get("action_code")


@before_task_publish.connect
def on_task_publish(sender=None, headers=None, body=None, **kwargs):
    """
    Called before a task is published to the broker.

    Creates the initial task record with PENDING status.
    """
    try:
        task_id = headers.get("id")
        task_name = headers.get("task")

        # Extract args and kwargs from body
        # Body format depends on serializer, typically (args, kwargs, ...)
        args = body[0] if body and len(body) > 0 else []
        task_kwargs = body[1] if body and len(body) > 1 else {}

        # Get user_id from task kwargs (required for our tasks)
        user_id = task_kwargs.get("user_id")
        if not user_id:
            # Skip tracking for tasks without user_id
            return

        metadata = _extract_task_metadata(task_kwargs)

        db = SessionLocal()
        try:
            service = TaskTrackingService(db)
            service.create_task_record(
                task_id=task_id,
                name=task_name,
                user_id=user_id,
                args=list(args) if args else None,
                kwargs=task_kwargs,
                marketplace=metadata.get("marketplace"),
                action_code=metadata.get("action_code"),
                product_id=metadata.get("product_id"),
                queue=headers.get("queue"),
                eta=headers.get("eta"),
                expires=headers.get("expires"),
            )
        finally:
            db.close()

    except Exception as e:
        # Don't fail the task publish if tracking fails
        logger.error(f"Failed to create task record on publish: {e}", exc_info=True)


@task_prerun.connect
def on_task_prerun(sender=None, task_id=None, task=None, **kwargs):
    """
    Called just before a task is executed.

    Updates task record to STARTED status.
    """
    try:
        db = SessionLocal()
        try:
            service = TaskTrackingService(db)
            worker = task.request.hostname if task.request else None
            service.update_task_started(task_id=task_id, worker=worker)
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Failed to update task record on prerun: {e}", exc_info=True)


@task_postrun.connect
def on_task_postrun(sender=None, task_id=None, task=None, state=None, retval=None, **kwargs):
    """
    Called after a task is executed.

    Updates task record to SUCCESS status if successful.
    """
    try:
        if state == "SUCCESS":
            db = SessionLocal()
            try:
                service = TaskTrackingService(db)
                record = service.update_task_success(task_id=task_id, result=retval)

                # Send WebSocket notification
                if record:
                    _send_websocket_update(
                        user_id=record.user_id,
                        event="task_completed",
                        data={
                            "task_id": task_id,
                            "name": record.name,
                            "status": "SUCCESS",
                            "marketplace": record.marketplace,
                            "action_code": record.action_code,
                            "product_id": record.product_id,
                            "result": record.result,
                            "runtime_seconds": record.runtime_seconds,
                        },
                    )
            finally:
                db.close()

    except Exception as e:
        logger.error(f"Failed to update task record on postrun: {e}", exc_info=True)


@task_failure.connect
def on_task_failure(sender=None, task_id=None, exception=None, traceback=None, **kwargs):
    """
    Called when a task fails.

    Updates task record to FAILURE status.
    """
    try:
        db = SessionLocal()
        try:
            service = TaskTrackingService(db)
            error_msg = str(exception) if exception else "Unknown error"
            tb_str = "".join(format_tb(traceback)) if traceback else None
            record = service.update_task_failure(
                task_id=task_id,
                error=error_msg,
                traceback=tb_str,
            )

            # Send WebSocket notification
            if record:
                _send_websocket_update(
                    user_id=record.user_id,
                    event="task_failed",
                    data={
                        "task_id": task_id,
                        "name": record.name,
                        "status": "FAILURE",
                        "marketplace": record.marketplace,
                        "action_code": record.action_code,
                        "product_id": record.product_id,
                        "error": error_msg,
                        "retries": record.retries,
                        "max_retries": record.max_retries,
                    },
                )
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Failed to update task record on failure: {e}", exc_info=True)


def format_tb(tb):
    """Format traceback object to string list."""
    import traceback
    if tb:
        return traceback.format_tb(tb)
    return []


@task_retry.connect
def on_task_retry(sender=None, request=None, reason=None, **kwargs):
    """
    Called when a task is being retried.

    Updates task record to RETRY status.
    """
    try:
        task_id = request.id if request else None
        if not task_id:
            return

        db = SessionLocal()
        try:
            service = TaskTrackingService(db)
            retries = request.retries if request else 0
            service.update_task_retry(
                task_id=task_id,
                retries=retries,
                error=str(reason) if reason else None,
            )
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Failed to update task record on retry: {e}", exc_info=True)


@task_revoked.connect
def on_task_revoked(sender=None, request=None, terminated=None, signum=None, **kwargs):
    """
    Called when a task is revoked.

    Updates task record to REVOKED status.
    """
    try:
        task_id = request.id if request else None
        if not task_id:
            return

        db = SessionLocal()
        try:
            service = TaskTrackingService(db)
            service.update_task_revoked(task_id=task_id)
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Failed to update task record on revoke: {e}", exc_info=True)


def setup_celery_signals():
    """
    Setup function to ensure signals are connected.

    Call this from celery_app.py to register all signals.
    """
    logger.info("Celery task tracking signals registered")
