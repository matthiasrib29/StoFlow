"""
DataDome Scheduler - Periodic ping to maintain Vinted sessions

This scheduler runs in the background and sends DataDome ping tasks
to all connected Vinted users every 5 minutes.

Architecture:
- APScheduler for scheduled tasks
- Iterates through all user schemas with active Vinted connections
- Creates datadome_ping task for each user needing a ping
- Updates VintedConnection.last_datadome_ping on success

Usage:
    # Start the scheduler
    from services.datadome_scheduler import start_datadome_scheduler
    scheduler = start_datadome_scheduler()

    # Stop the scheduler
    from services.datadome_scheduler import stop_datadome_scheduler
    stop_datadome_scheduler(scheduler)

Author: Claude
Date: 2025-12-19
"""

import asyncio
import os
from datetime import datetime, timezone
from typing import List, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from models.user.vinted_connection import VintedConnection, DataDomeStatus
# Temporary constant until DataDome ping is re-implemented with WebSocket
DATADOME_PING_INTERVAL_SECONDS = 60
from shared.config import settings
from shared.logging import get_logger

logger = get_logger(__name__)

# Database Session Setup
engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ========== CONFIGURATION ==========

# Polling interval (in minutes) - configurable via env
DATADOME_POLL_INTERVAL_MINUTES = int(
    os.getenv("DATADOME_POLL_INTERVAL_MINUTES", "5")
)


# ========== HELPER FUNCTIONS ==========


def get_all_user_schemas(db: Session) -> List[str]:
    """
    Get all user schemas from the database.

    Returns:
        List of schema names (user_1, user_2, etc.)
    """
    result = db.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
        AND schema_name <> 'user_invalid'
        ORDER BY schema_name
    """))
    return [row[0] for row in result.fetchall()]


def get_connected_vinted_users(db: Session, schema: str) -> List[VintedConnection]:
    """
    Get all connected Vinted users in a specific schema.

    Args:
        db: Database session
        schema: Schema name (user_X)

    Returns:
        List of VintedConnection objects with is_connected=True
    """
    try:
        # Use schema_translate_map for ORM queries (survives commit/rollback)
        from shared.schema import configure_schema_translate_map
        configure_schema_translate_map(db, schema)
        schema_db = db  # Use same session (connection is now configured)

        # Check if table exists
        table_exists = db.execute(text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = '{schema}'
                AND table_name = 'vinted_connection'
            )
        """)).scalar()

        if not table_exists:
            return []

        # Query connected users with schema-aware session
        connections = schema_db.query(VintedConnection).filter(
            VintedConnection.is_connected == True
        ).all()

        return connections

    except Exception as e:
        logger.error(f"Error getting connected users in {schema}: {e}", exc_info=True)
        return []


# ========== POLLING TASK ==========


def ping_datadome_for_all_users():
    """
    DISABLED (2026-01-09): DataDomePingService uses PluginTask (obsolete).

    Ping DataDome for all connected Vinted users.

    This task runs every DATADOME_POLL_INTERVAL_MINUTES minutes.
    It iterates through all user schemas and pings DataDome for
    users that need it (haven't been pinged in 5 minutes).
    """
    logger.info("🛡️ DataDome ping DISABLED (WebSocket migration in progress)")
    return  # TEMPORARY: Disabled until re-implemented with WebSocket

    logger.info("🛡️ Starting DataDome ping cycle")
    start_time = datetime.now(timezone.utc)

    db: Session = SessionLocal()
    total_pinged = 0
    total_success = 0
    total_failed = 0
    total_skipped = 0

    try:
        # Get all user schemas
        schemas = get_all_user_schemas(db)
        logger.debug(f"Found {len(schemas)} user schemas")

        for schema in schemas:
            try:
                # Get connected users in this schema
                connections = get_connected_vinted_users(db, schema)

                if not connections:
                    continue

                for connection in connections:
                    # Check if ping is needed
                    if not DataDomePingService.needs_ping(connection):
                        total_skipped += 1
                        logger.debug(
                            f"Skipping {schema} - pinged recently "
                            f"(last: {connection.last_datadome_ping})"
                        )
                        continue

                    total_pinged += 1
                    logger.debug(
                        f"Pinging DataDome for {schema} "
                        f"(vinted_user_id={connection.vinted_user_id})"
                    )

                    # Execute ping (async in sync context)
                    try:
                        success = asyncio.run(
                            DataDomePingService.ping_and_update_status(
                                db, connection
                            )
                        )

                        if success:
                            total_success += 1
                        else:
                            total_failed += 1

                    except Exception as e:
                        total_failed += 1
                        logger.error(
                            f"DataDome ping failed for {schema}: {e}",
                            exc_info=True
                        )

                        # Update status to failed
                        connection.update_datadome_status(False)
                        db.commit()

            except Exception as e:
                logger.error(f"Error processing schema {schema}: {e}")
                continue

    except Exception as e:
        logger.error(f"DataDome ping cycle error: {e}", exc_info=True)

    finally:
        db.close()

    # Log summary
    elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
    logger.info(
        f"🛡️ DataDome ping cycle completed in {elapsed:.2f}s - "
        f"Pinged: {total_pinged}, Success: {total_success}, "
        f"Failed: {total_failed}, Skipped: {total_skipped}"
    )


# ========== SCHEDULER MANAGEMENT ==========


_scheduler: Optional[BackgroundScheduler] = None


def start_datadome_scheduler() -> BackgroundScheduler:
    """
    Start the DataDome ping scheduler.

    Returns:
        BackgroundScheduler instance

    Example:
        scheduler = start_datadome_scheduler()
        # Keep running...
        time.sleep(3600)
        stop_datadome_scheduler(scheduler)
    """
    global _scheduler

    if _scheduler is not None and _scheduler.running:
        logger.warning("DataDome scheduler is already running")
        return _scheduler

    _scheduler = BackgroundScheduler(timezone="UTC")

    # Add the ping job
    _scheduler.add_job(
        func=ping_datadome_for_all_users,
        trigger=IntervalTrigger(minutes=DATADOME_POLL_INTERVAL_MINUTES),
        id="datadome_ping",
        name="DataDome Ping All Users",
        replace_existing=True,
    )

    _scheduler.start()

    logger.info(
        f"🛡️ DataDome scheduler started "
        f"(interval: {DATADOME_POLL_INTERVAL_MINUTES} minutes)"
    )

    # Run initial ping immediately
    logger.info("🛡️ Running initial DataDome ping...")
    ping_datadome_for_all_users()

    return _scheduler


def stop_datadome_scheduler(scheduler: Optional[BackgroundScheduler] = None):
    """
    Stop the DataDome ping scheduler.

    Args:
        scheduler: Scheduler instance (uses global if not provided)
    """
    global _scheduler

    sched = scheduler or _scheduler

    if sched is not None and sched.running:
        sched.shutdown(wait=False)
        logger.info("🛡️ DataDome scheduler stopped")

    _scheduler = None


def get_datadome_scheduler() -> Optional[BackgroundScheduler]:
    """
    Get the current DataDome scheduler instance.

    Returns:
        BackgroundScheduler or None if not running
    """
    return _scheduler


# ========== STANDALONE RUNNER ==========


if __name__ == "__main__":
    import time

    logger.info("Starting DataDome scheduler (standalone mode)")

    scheduler = start_datadome_scheduler()

    try:
        # Keep running
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        stop_datadome_scheduler(scheduler)
