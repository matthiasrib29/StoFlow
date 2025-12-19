"""
DataDome Ping Service - Maintains DataDome session via plugin tasks

This service handles periodic DataDome pings to keep the Vinted session
alive and prevent bot detection when the plugin makes API requests.

Architecture:
- Backend sends datadome_ping task to plugin every 5 minutes
- Plugin executes ping via DataDomeHandler in stoflow-vinted-api.js
- Plugin returns success/failure, backend updates VintedConnection status

Business Rules:
- Ping interval: 5 minutes (300 seconds)
- Retry count: 3 attempts on failure
- Timeout per ping: 10 seconds
- Only ping connected users (is_connected = True)

Author: Claude
Date: 2025-12-19
"""

import asyncio
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from models.user.vinted_connection import VintedConnection, DataDomeStatus
from models.user.plugin_task import PluginTask, TaskStatus
from services.plugin_task_helper import PluginTaskHelper, _commit_and_restore_path
from shared.logging_setup import get_logger

logger = get_logger(__name__)


# Configuration
DATADOME_PING_INTERVAL_SECONDS = 300  # 5 minutes
DATADOME_PING_TIMEOUT_SECONDS = 10    # Timeout per ping attempt
DATADOME_PING_MAX_RETRIES = 3         # Number of retry attempts


class DataDomePingService:
    """
    Service for managing DataDome ping tasks.

    The ping is executed via the browser plugin which has access
    to DataDome's JavaScript API on the Vinted page.
    """

    @staticmethod
    async def ping_datadome(
        db: Session,
        max_retries: int = DATADOME_PING_MAX_RETRIES,
        timeout: int = DATADOME_PING_TIMEOUT_SECONDS
    ) -> bool:
        """
        Send a DataDome ping task to the plugin.

        Creates a special task 'datadome_ping' and waits for completion.
        Retries up to max_retries times on failure.

        Args:
            db: SQLAlchemy session (with user schema set)
            max_retries: Number of retry attempts (default: 3)
            timeout: Timeout per attempt in seconds (default: 10)

        Returns:
            bool: True if ping successful, False otherwise

        Example:
            success = await DataDomePingService.ping_datadome(db)
            if success:
                logger.info("DataDome session is healthy")
        """
        for attempt in range(1, max_retries + 1):
            try:
                logger.debug(
                    f"[DataDome] Ping attempt {attempt}/{max_retries}"
                )

                # Create the ping task
                task = PluginTaskHelper.create_special_task(
                    db=db,
                    task_type="datadome_ping",
                    platform="vinted",
                    payload={
                        "action": "ping",
                        "attempt": attempt,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                )

                # Wait for plugin to execute
                result = await PluginTaskHelper.wait_for_task_completion(
                    db=db,
                    task_id=task.id,
                    timeout=timeout,
                    poll_interval=0.5  # Faster polling for quick ping
                )

                # Check result
                success = result.get("success", False)
                ping_count = result.get("ping_count", 0)

                if success:
                    logger.info(
                        f"[DataDome] Ping successful (attempt {attempt}, "
                        f"total pings: {ping_count})"
                    )
                    return True
                else:
                    error = result.get("error", "Unknown error")
                    logger.warning(
                        f"[DataDome] Ping failed (attempt {attempt}): {error}"
                    )

            except TimeoutError:
                logger.warning(
                    f"[DataDome] Ping timeout (attempt {attempt}/{max_retries})"
                )
            except Exception as e:
                logger.error(
                    f"[DataDome] Ping error (attempt {attempt}): {e}",
                    exc_info=True
                )

            # Wait before retry (exponential backoff)
            if attempt < max_retries:
                wait_time = 2 ** attempt  # 2s, 4s, 8s
                logger.debug(f"[DataDome] Waiting {wait_time}s before retry")
                await asyncio.sleep(wait_time)

        logger.error(
            f"[DataDome] All {max_retries} ping attempts failed"
        )
        return False

    @staticmethod
    async def ping_and_update_status(
        db: Session,
        vinted_connection: VintedConnection
    ) -> bool:
        """
        Ping DataDome and update the VintedConnection status.

        Args:
            db: SQLAlchemy session
            vinted_connection: The connection to update

        Returns:
            bool: True if ping successful
        """
        success = await DataDomePingService.ping_datadome(db)

        # Update connection status
        vinted_connection.update_datadome_status(success)
        _commit_and_restore_path(db)

        if success:
            logger.info(
                f"[DataDome] Updated connection status: OK "
                f"(vinted_user_id={vinted_connection.vinted_user_id})"
            )
        else:
            logger.warning(
                f"[DataDome] Updated connection status: FAILED "
                f"(vinted_user_id={vinted_connection.vinted_user_id})"
            )

        return success

    @staticmethod
    def needs_ping(connection: VintedConnection) -> bool:
        """
        Check if a connection needs a DataDome ping.

        Args:
            connection: VintedConnection to check

        Returns:
            bool: True if ping is needed
        """
        if not connection.is_connected:
            return False

        return connection.needs_datadome_ping(DATADOME_PING_INTERVAL_SECONDS)

    @staticmethod
    def get_connected_users_needing_ping(db: Session) -> list[VintedConnection]:
        """
        Get all connected users that need a DataDome ping.

        Args:
            db: SQLAlchemy session

        Returns:
            List of VintedConnection objects needing ping
        """
        connections = db.query(VintedConnection).filter(
            VintedConnection.is_connected == True
        ).all()

        return [
            conn for conn in connections
            if DataDomePingService.needs_ping(conn)
        ]


async def ping_datadome_for_user(
    db: Session,
    user_id: int
) -> bool:
    """
    Convenience function to ping DataDome for a specific user.

    Sets the user schema and executes the ping.

    Args:
        db: SQLAlchemy session
        user_id: Stoflow user ID

    Returns:
        bool: True if ping successful
    """
    # Set user schema
    schema_name = f"user_{user_id}"
    db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))

    # Get connection
    connection = db.query(VintedConnection).filter(
        VintedConnection.user_id == user_id,
        VintedConnection.is_connected == True
    ).first()

    if not connection:
        logger.debug(f"[DataDome] No active connection for user {user_id}")
        return False

    return await DataDomePingService.ping_and_update_status(db, connection)
