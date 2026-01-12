"""
Job Cleanup Scheduler - Periodic cleanup of expired/stuck marketplace jobs.

Runs periodically to:
- Mark PENDING jobs as FAILED if too old (never started)
- Mark PROCESSING jobs as FAILED if worker died/stuck

Architecture:
- APScheduler for scheduled tasks
- Iterates through all user schemas
- Applies cleanup rules to MarketplaceJob table in each schema

Usage:
    # Start the scheduler
    from services.marketplace.job_cleanup_scheduler import start_job_cleanup_scheduler
    scheduler = start_job_cleanup_scheduler()

    # Stop the scheduler
    from services.marketplace.job_cleanup_scheduler import stop_job_cleanup_scheduler
    stop_job_cleanup_scheduler(scheduler)

Security Phase 2.2 (2026-01-12)

Author: Claude
Date: 2026-01-12
"""

import os
from datetime import datetime, timezone
from typing import List, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from services.marketplace.job_cleanup_service import JobCleanupService
from shared.config import settings
from shared.logging_setup import get_logger

logger = get_logger(__name__)

# Database Session Setup
engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ========== CONFIGURATION ==========

# Cleanup interval (in minutes) - configurable via env
JOB_CLEANUP_INTERVAL_MINUTES = int(
    os.getenv("JOB_CLEANUP_INTERVAL_MINUTES", "60")  # Default: 1 hour
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


# ========== CLEANUP TASK ==========


def cleanup_jobs_for_all_users():
    """
    Run job cleanup for all user schemas.

    This task runs every JOB_CLEANUP_INTERVAL_MINUTES minutes.
    It iterates through all user schemas and marks expired/stuck jobs as FAILED.
    """
    logger.info("🧹 Starting job cleanup cycle")
    start_time = datetime.now(timezone.utc)

    db: Session = SessionLocal()
    total_pending_expired = 0
    total_processing_expired = 0
    schemas_processed = 0

    try:
        # Get all user schemas
        schemas = get_all_user_schemas(db)
        logger.debug(f"Found {len(schemas)} user schemas")

        for schema in schemas:
            try:
                # Set schema
                db.execute(text(f"SET LOCAL search_path TO {schema}, public"))

                # Check if marketplace_jobs table exists
                table_exists = db.execute(text(f"""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_schema = '{schema}'
                        AND table_name = 'marketplace_jobs'
                    )
                """)).scalar()

                if not table_exists:
                    logger.debug(f"Schema {schema} has no marketplace_jobs table, skipping")
                    continue

                # Run cleanup
                result = JobCleanupService.cleanup_expired_jobs(db)

                total_pending_expired += result["pending_expired"]
                total_processing_expired += result["processing_expired"]
                schemas_processed += 1

                if result["pending_expired"] > 0 or result["processing_expired"] > 0:
                    logger.info(
                        f"[{schema}] Cleaned up: "
                        f"{result['pending_expired']} pending, "
                        f"{result['processing_expired']} processing"
                    )

            except Exception as e:
                logger.error(f"Error cleaning up jobs in {schema}: {e}", exc_info=True)
                continue

    except Exception as e:
        logger.error(f"Job cleanup cycle error: {e}", exc_info=True)

    finally:
        db.close()

    # Log summary
    elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
    logger.info(
        f"🧹 Job cleanup cycle completed in {elapsed:.2f}s - "
        f"Schemas: {schemas_processed}, "
        f"Pending expired: {total_pending_expired}, "
        f"Processing expired: {total_processing_expired}"
    )


# ========== SCHEDULER MANAGEMENT ==========


_scheduler: Optional[BackgroundScheduler] = None


def start_job_cleanup_scheduler() -> BackgroundScheduler:
    """
    Start the job cleanup scheduler.

    Returns:
        BackgroundScheduler instance

    Example:
        scheduler = start_job_cleanup_scheduler()
        # Keep running...
        time.sleep(3600)
        stop_job_cleanup_scheduler(scheduler)
    """
    global _scheduler

    if _scheduler is not None and _scheduler.running:
        logger.warning("Job cleanup scheduler is already running")
        return _scheduler

    _scheduler = BackgroundScheduler(timezone="UTC")

    # Add the cleanup job
    _scheduler.add_job(
        func=cleanup_jobs_for_all_users,
        trigger=IntervalTrigger(minutes=JOB_CLEANUP_INTERVAL_MINUTES),
        id="job_cleanup",
        name="Marketplace Job Cleanup",
        replace_existing=True,
    )

    _scheduler.start()

    logger.info(
        f"🧹 Job cleanup scheduler started "
        f"(interval: {JOB_CLEANUP_INTERVAL_MINUTES} minutes)"
    )

    # Run initial cleanup immediately
    logger.info("🧹 Running initial job cleanup...")
    cleanup_jobs_for_all_users()

    return _scheduler


def stop_job_cleanup_scheduler(scheduler: Optional[BackgroundScheduler] = None):
    """
    Stop the job cleanup scheduler.

    Args:
        scheduler: Scheduler instance (uses global if not provided)
    """
    global _scheduler

    sched = scheduler or _scheduler

    if sched is not None and sched.running:
        sched.shutdown(wait=False)
        logger.info("🧹 Job cleanup scheduler stopped")

    _scheduler = None


def get_job_cleanup_scheduler() -> Optional[BackgroundScheduler]:
    """
    Get the current job cleanup scheduler instance.

    Returns:
        BackgroundScheduler or None if not running
    """
    return _scheduler


# ========== STANDALONE RUNNER ==========


if __name__ == "__main__":
    import time

    logger.info("Starting job cleanup scheduler (standalone mode)")

    scheduler = start_job_cleanup_scheduler()

    try:
        # Keep running
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        stop_job_cleanup_scheduler(scheduler)
