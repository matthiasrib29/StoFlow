"""
Celery tasks for user notifications.
"""
from typing import Any

from celery import shared_task
from celery.utils.log import get_task_logger

from shared.database import SessionLocal

logger = get_task_logger(__name__)


@shared_task(
    bind=True,
    name="tasks.notification_tasks.send_task_completion_notification",
    autoretry_for=(ConnectionError,),
    retry_backoff=10,
    max_retries=2,
)
def send_task_completion_notification(
    self,
    user_id: int,
    task_type: str,
    task_id: str,
    status: str,
    result: dict[str, Any] | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    """
    Send notification to user when a task completes.

    This can be via WebSocket, email, or push notification depending
    on user preferences.

    Args:
        user_id: User ID to notify
        task_type: Type of task (e.g., "publish", "sync")
        task_id: Celery task ID
        status: Task status (SUCCESS, FAILURE)
        result: Task result data (if success)
        error: Error message (if failure)

    Returns:
        Dict with notification result
    """
    logger.info(
        f"Sending {status} notification to user {user_id} for task {task_id}"
    )

    db = SessionLocal()
    try:
        # Send WebSocket notification
        _send_websocket_notification(
            user_id=user_id,
            event="task_completed",
            data={
                "task_id": task_id,
                "task_type": task_type,
                "status": status,
                "result": result,
                "error": error,
            },
        )

        # Optionally send email for failures
        if status == "FAILURE":
            _send_email_notification(
                db=db,
                user_id=user_id,
                task_type=task_type,
                error=error,
            )

        return {
            "success": True,
            "user_id": user_id,
            "task_id": task_id,
            "notification_type": "websocket",
        }

    except Exception as exc:
        logger.error(
            f"Failed to send notification to user {user_id}: {exc}",
            exc_info=True,
        )
        raise
    finally:
        db.close()


def _send_websocket_notification(
    user_id: int,
    event: str,
    data: dict[str, Any],
) -> None:
    """
    Send notification via WebSocket.

    Args:
        user_id: User ID to notify
        event: Event name
        data: Event data
    """
    try:
        from services.websocket_service import sio

        room = f"user_{user_id}"
        sio.emit(event, data, room=room)
        logger.debug(f"Sent WebSocket notification to room {room}")

    except Exception as exc:
        logger.warning(f"Failed to send WebSocket notification: {exc}")
        # Don't raise - WebSocket failure shouldn't block the task


def _send_email_notification(
    db,
    user_id: int,
    task_type: str,
    error: str | None,
) -> None:
    """
    Send email notification for task failures.

    Args:
        db: Database session
        user_id: User ID to notify
        task_type: Type of task that failed
        error: Error message
    """
    try:
        from models.public.user import User
        from services.email_service import EmailService

        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.email:
            logger.warning(f"Cannot send email: user {user_id} not found or no email")
            return

        # Check user preferences for email notifications
        # TODO: Add user notification preferences

        email_service = EmailService()
        email_service.send_task_failure_email(
            to_email=user.email,
            user_name=user.first_name or "User",
            task_type=task_type,
            error_message=error or "Unknown error",
        )
        logger.info(f"Sent failure email to user {user_id}")

    except Exception as exc:
        logger.warning(f"Failed to send email notification: {exc}")
        # Don't raise - email failure shouldn't block the task


@shared_task(
    bind=True,
    name="tasks.notification_tasks.send_batch_completion_notification",
    max_retries=2,
)
def send_batch_completion_notification(
    self,
    user_id: int,
    batch_id: str,
    marketplace: str,
    action_code: str,
    total_count: int,
    success_count: int,
    failure_count: int,
) -> dict[str, Any]:
    """
    Send notification when a batch job completes.

    Args:
        user_id: User ID to notify
        batch_id: Batch job ID
        marketplace: Marketplace name
        action_code: Action type (publish, update, etc.)
        total_count: Total jobs in batch
        success_count: Successful jobs
        failure_count: Failed jobs

    Returns:
        Dict with notification result
    """
    logger.info(
        f"Sending batch completion notification to user {user_id} "
        f"for batch {batch_id}"
    )

    status = "partial" if failure_count > 0 and success_count > 0 else (
        "success" if failure_count == 0 else "failure"
    )

    _send_websocket_notification(
        user_id=user_id,
        event="batch_completed",
        data={
            "batch_id": batch_id,
            "marketplace": marketplace,
            "action_code": action_code,
            "status": status,
            "total_count": total_count,
            "success_count": success_count,
            "failure_count": failure_count,
        },
    )

    return {
        "success": True,
        "user_id": user_id,
        "batch_id": batch_id,
        "status": status,
    }
