"""
Cleanup service for expired/stuck marketplace jobs.

Runs periodically to:
- Mark PENDING jobs as FAILED if too old (never started)
- Mark PROCESSING jobs as FAILED if worker died/stuck
- Optional: Cleanup old COMPLETED/FAILED jobs (retention policy)

Security Phase 2.2 (2026-01-12)

Author: Claude
Date: 2026-01-12
"""

from datetime import datetime, timezone, timedelta
from typing import Dict

from sqlalchemy import update
from sqlalchemy.orm import Session

from models.user.marketplace_job import MarketplaceJob, JobStatus
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class JobCleanupService:
    """
    Background cleanup service for marketplace jobs.

    Prevents jobs from staying in PENDING/PROCESSING state indefinitely
    when workers crash or tasks get stuck.
    """

    # Timeouts
    PENDING_TIMEOUT = timedelta(hours=24)     # Job never started
    PROCESSING_TIMEOUT = timedelta(hours=2)   # Worker died/stuck
    RETENTION_PERIOD = timedelta(days=30)     # Keep history (optional cleanup)

    @staticmethod
    def cleanup_expired_jobs(db: Session) -> Dict[str, int]:
        """
        Mark expired jobs as FAILED and optionally cleanup old jobs.

        Args:
            db: SQLAlchemy session

        Returns:
            dict with cleanup statistics:
                - pending_expired: Number of PENDING jobs marked as FAILED
                - processing_expired: Number of PROCESSING jobs marked as FAILED
                - old_jobs_deleted: Number of old jobs deleted (if retention enabled)
        """
        now = datetime.now(timezone.utc)

        # 1. Mark PENDING jobs as FAILED if too old (never started)
        pending_expired = db.execute(
            update(MarketplaceJob)
            .where(
                MarketplaceJob.status == JobStatus.PENDING,
                MarketplaceJob.created_at < now - JobCleanupService.PENDING_TIMEOUT
            )
            .values(
                status=JobStatus.FAILED,
                error_message="Job expired (never started by worker after 24h)",
                completed_at=now
            )
        ).rowcount

        # 2. Mark PROCESSING jobs as FAILED if too old (worker died/stuck)
        processing_expired = db.execute(
            update(MarketplaceJob)
            .where(
                MarketplaceJob.status == JobStatus.PROCESSING,
                MarketplaceJob.started_at < now - JobCleanupService.PROCESSING_TIMEOUT
            )
            .values(
                status=JobStatus.FAILED,
                error_message="Job timeout (worker died or stuck after 2h)",
                completed_at=now
            )
        ).rowcount

        db.commit()

        logger.info(
            f"[JobCleanup] Expired jobs marked as FAILED: "
            f"pending={pending_expired}, processing={processing_expired}"
        )

        return {
            "pending_expired": pending_expired,
            "processing_expired": processing_expired,
        }

    @staticmethod
    def cleanup_old_jobs(db: Session, retention_days: int = 30) -> int:
        """
        Delete old COMPLETED/FAILED jobs beyond retention period.

        Args:
            db: SQLAlchemy session
            retention_days: Number of days to keep job history

        Returns:
            Number of jobs deleted

        Note:
            This is optional and can be disabled if full history is needed.
            Only deletes jobs that are truly completed (not PENDING/PROCESSING).
        """
        now = datetime.now(timezone.utc)
        cutoff_date = now - timedelta(days=retention_days)

        # Delete old COMPLETED/FAILED jobs
        deleted = db.execute(
            update(MarketplaceJob)
            .where(
                MarketplaceJob.status.in_([JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]),
                MarketplaceJob.completed_at < cutoff_date
            )
            .values(deleted_at=now)  # Soft delete
        ).rowcount

        db.commit()

        if deleted > 0:
            logger.info(
                f"[JobCleanup] Old jobs soft-deleted: "
                f"{deleted} jobs older than {retention_days} days"
            )

        return deleted


# ========== Scheduled Task (for APScheduler integration) ==========

async def scheduled_job_cleanup():
    """
    Scheduled task to run job cleanup periodically.

    Should be called by APScheduler every hour (or configured interval).
    """
    from shared.database import SessionLocal

    db = SessionLocal()
    try:
        result = JobCleanupService.cleanup_expired_jobs(db)
        logger.info(
            f"[JobCleanup] Cleanup completed: "
            f"{result['pending_expired']} pending, "
            f"{result['processing_expired']} processing marked as FAILED"
        )

        # Optional: Cleanup old jobs if enabled
        # deleted = JobCleanupService.cleanup_old_jobs(db, retention_days=30)

    except Exception as e:
        logger.error(f"[JobCleanup] Cleanup failed: {e}", exc_info=True)
    finally:
        db.close()
