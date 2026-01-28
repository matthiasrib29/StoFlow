"""
Temporal Activity Helpers & Plugin Connection Activity.

Shared helpers for DB session configuration in Temporal activities,
and plugin connection check activity.

Author: Claude
Date: 2026-01-27 - Extracted from vinted_activities.py
Updated: 2026-01-28 - Removed MarketplaceJob state activities (table dropped)
"""

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
        activity.logger.warning(f"Error checking plugin connection for user {user_id}: {e}", exc_info=True)
        return False


# Activities for Temporal worker registration
JOB_STATE_ACTIVITIES = [
    check_plugin_connection,
]
