"""
Job State Activities for Temporal.

Generic activities for managing marketplace job state (progress, completion, failure, pause).
Reusable across all marketplaces (Vinted, eBay, Etsy).

Also provides shared helpers for DB session configuration in Temporal activities.

Author: Claude
Date: 2026-01-27 - Extracted from vinted_activities.py
"""

import json

from sqlalchemy import text
from temporalio import activity

from shared.database import SessionLocal
from shared.logging import get_logger

logger = get_logger(__name__)


def get_schema_name(user_id: int) -> str:
    """Get schema name for user."""
    return f"user_{user_id}"


def configure_activity_session(db, user_id: int) -> None:
    """Configure DB session for user schema in Temporal activities."""
    from shared.schema import configure_schema_translate_map

    schema_name = get_schema_name(user_id)
    configure_schema_translate_map(db, schema_name)
    db.execute(text(f"SET search_path TO {schema_name}, public"))


@activity.defn(name="vinted_update_job_progress")
async def update_job_progress(
    user_id: int,
    job_id: int,
    current: int,
    label: str,
) -> None:
    """
    Update job progress in the database.

    Args:
        user_id: User ID for schema isolation
        job_id: MarketplaceJob ID
        current: Current progress count
        label: Progress label text
    """
    db = SessionLocal()
    try:
        schema_name = get_schema_name(user_id)
        db.execute(text(f"SET search_path TO {schema_name}, public"))

        data = json.dumps({"current": current, "label": label})

        db.execute(
            text("UPDATE marketplace_jobs SET result_data = :data WHERE id = :job_id"),
            {"data": data, "job_id": job_id},
        )
        db.commit()

        activity.logger.debug(f"Job #{job_id} progress: {current} - {label}")

    finally:
        db.close()


@activity.defn(name="vinted_mark_job_completed")
async def mark_job_completed(
    user_id: int,
    job_id: int,
    final_count: int,
) -> None:
    """
    Mark job as completed.

    Args:
        user_id: User ID for schema isolation
        job_id: MarketplaceJob ID
        final_count: Final synced product count
    """
    db = SessionLocal()
    try:
        schema_name = get_schema_name(user_id)
        db.execute(text(f"SET search_path TO {schema_name}, public"))

        data = json.dumps({"current": final_count, "label": "produits synchronisés"})

        db.execute(
            text(
                "UPDATE marketplace_jobs SET status = 'completed', result_data = :data "
                "WHERE id = :job_id"
            ),
            {"data": data, "job_id": job_id},
        )
        db.commit()

        activity.logger.info(f"Job #{job_id} completed: {final_count} products")

    finally:
        db.close()


@activity.defn(name="vinted_mark_job_failed")
async def mark_job_failed(
    user_id: int,
    job_id: int,
    error_msg: str,
) -> None:
    """
    Mark job as failed.

    Args:
        user_id: User ID for schema isolation
        job_id: MarketplaceJob ID
        error_msg: Error message
    """
    db = SessionLocal()
    try:
        schema_name = get_schema_name(user_id)
        db.execute(text(f"SET search_path TO {schema_name}, public"))

        safe_error = error_msg[:500]

        db.execute(
            text(
                "UPDATE marketplace_jobs SET status = 'failed', error_message = :error "
                "WHERE id = :job_id"
            ),
            {"error": safe_error, "job_id": job_id},
        )
        db.commit()

        activity.logger.info(f"Job #{job_id} failed: {safe_error}")

    finally:
        db.close()


@activity.defn(name="vinted_mark_job_paused")
async def mark_job_paused(
    user_id: int,
    job_id: int,
    reason: str,
) -> None:
    """
    Mark job as paused in the database.

    Args:
        user_id: User ID for schema isolation
        job_id: MarketplaceJob ID
        reason: Reason for pausing
    """
    db = SessionLocal()
    try:
        schema_name = get_schema_name(user_id)
        db.execute(text(f"SET search_path TO {schema_name}, public"))

        data = json.dumps({"paused_reason": reason})

        db.execute(
            text(
                "UPDATE marketplace_jobs SET status = 'paused', result_data = :data "
                "WHERE id = :job_id"
            ),
            {"data": data, "job_id": job_id},
        )
        db.commit()

        activity.logger.info(f"Job #{job_id} paused: {reason}")

    finally:
        db.close()


@activity.defn(name="vinted_check_plugin_connection")
async def check_plugin_connection(user_id: int) -> bool:
    """
    Check if the plugin is connected via WebSocket.

    Args:
        user_id: User ID to check connection for

    Returns:
        True if plugin is connected, False otherwise
    """
    try:
        from services.websocket_service import sio

        room = f"user_{user_id}"
        rooms = sio.manager.rooms.get("/", {})
        room_sids = rooms.get(room, set())

        is_connected = len(room_sids) > 0
        activity.logger.debug(
            f"Plugin connection check for user {user_id}: "
            f"{'connected' if is_connected else 'disconnected'} ({len(room_sids)} clients)"
        )
        return is_connected

    except Exception as e:
        activity.logger.warning(f"Error checking plugin connection for user {user_id}: {e}")
        return False


# All job state activities
JOB_STATE_ACTIVITIES = [
    update_job_progress,
    mark_job_completed,
    mark_job_failed,
    mark_job_paused,
    check_plugin_connection,
]
