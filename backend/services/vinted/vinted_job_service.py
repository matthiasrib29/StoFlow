"""
Vinted Job Service

Orchestrates Vinted jobs with priority management, status tracking,
and integration with the plugin task system.

Business Rules (2025-12-19):
- 1 Job = 1 product operation
- Jobs grouped by batch_id for batch operations
- Priority: 1=CRITICAL, 2=HIGH, 3=NORMAL, 4=LOW
- Expiration: 1 hour for pending jobs
- Retry: 3 attempts max, then FAILED
- Rate limit per action type

Author: Claude
Date: 2025-12-19
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import and_, func, text
from sqlalchemy.orm import Session

from models.public.marketplace_action_type import MarketplaceActionType
from models.user.marketplace_job import JobStatus, MarketplaceJob
from models.user.batch_job import BatchJob
from models.user.marketplace_job_stats import MarketplaceJobStats
from shared.advisory_locks import AdvisoryLockHelper
from shared.logging_setup import get_logger

logger = get_logger(__name__)


# Job expiration time (1 hour)
JOB_EXPIRATION_HOURS = 1

# Marketplace identifier for Vinted
VINTED_MARKETPLACE = "vinted"


class VintedJobService:
    """
    Service for managing Vinted jobs.

    Handles job creation, status updates, priority management,
    and statistics tracking.
    """

    def __init__(self, db: Session):
        self.db = db
        self._action_types_cache: dict[str, MarketplaceActionType] = {}

    # =========================================================================
    # ACTION TYPES
    # =========================================================================

    def get_action_type(self, code: str) -> MarketplaceActionType | None:
        """
        Get action type by code (with caching).

        Args:
            code: Action type code (publish, sync, orders, etc.)

        Returns:
            MarketplaceActionType or None
        """
        if code not in self._action_types_cache:
            action_type = (
                self.db.query(MarketplaceActionType)
                .filter(
                    MarketplaceActionType.marketplace == VINTED_MARKETPLACE,
                    MarketplaceActionType.code == code
                )
                .first()
            )
            if action_type:
                self._action_types_cache[code] = action_type
        return self._action_types_cache.get(code)

    def get_action_type_by_id(self, action_type_id: int) -> MarketplaceActionType | None:
        """Get action type by ID."""
        return (
            self.db.query(MarketplaceActionType)
            .filter(MarketplaceActionType.id == action_type_id)
            .first()
        )

    # =========================================================================
    # JOB CREATION
    # =========================================================================

    def create_job(
        self,
        action_code: str,
        product_id: int | None = None,
        batch_job_id: int | None = None,
        priority: int | None = None,
        result_data: dict | None = None,
    ) -> MarketplaceJob:
        """
        Create a new Vinted job.

        Args:
            action_code: Action type code (publish, sync, etc.)
            product_id: Product ID (optional)
            batch_job_id: BatchJob ID for grouping (optional)
            priority: Override priority (optional, uses action_type default)
            result_data: Initial data/parameters for the job (optional)

        Returns:
            Created MarketplaceJob

        Raises:
            ValueError: If action_code is invalid
        """
        action_type = self.get_action_type(action_code)
        if not action_type:
            raise ValueError(f"Invalid action code: {action_code}")

        # Calculate expiration time
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=JOB_EXPIRATION_HOURS)

        job = MarketplaceJob(
            marketplace="vinted",  # Explicit marketplace for Vinted jobs
            action_type_id=action_type.id,
            product_id=product_id,
            batch_job_id=batch_job_id,
            status=JobStatus.PENDING,
            priority=priority if priority is not None else action_type.priority,
            expires_at=expires_at,
            created_at=now,
            result_data=result_data,
        )

        self.db.add(job)
        self.db.flush()  # Get ID without committing

        logger.debug(
            f"[VintedJobService] Created job #{job.id} "
            f"(action={action_code}, product={product_id}, batch_job_id={batch_job_id})"
        )

        return job

    def create_batch_jobs(
        self,
        action_code: str,
        product_ids: list[int],
        priority: int | None = None,
    ) -> tuple[str, list[MarketplaceJob]]:
        """
        Create multiple jobs for a batch operation.

        Args:
            action_code: Action type code
            product_ids: List of product IDs
            priority: Override priority (optional)

        Returns:
            Tuple of (batch_id, list of created jobs)
        """
        batch_id = f"{action_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

        jobs = []
        for product_id in product_ids:
            job = self.create_job(
                action_code=action_code,
                product_id=product_id,
                batch_job_id=None,  # No BatchJob FK for this legacy method
                priority=priority,
            )
            jobs.append(job)

        self.db.commit()

        logger.info(
            f"[VintedJobService] Created batch {batch_id} with {len(jobs)} jobs"
        )

        return batch_id, jobs

    # =========================================================================
    # JOB STATUS MANAGEMENT
    # =========================================================================

    def start_job(self, job_id: int) -> MarketplaceJob | None:
        """
        Mark a job as running.

        Args:
            job_id: Job ID

        Returns:
            Updated MarketplaceJob or None if not found
        """
        job = self.db.query(MarketplaceJob).filter(MarketplaceJob.id == job_id).first()
        if not job:
            return None

        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(timezone.utc)
        self.db.commit()

        logger.debug(f"[VintedJobService] Started job #{job_id}")
        return job

    def complete_job(self, job_id: int) -> MarketplaceJob | None:
        """
        Mark a job as completed successfully.

        Args:
            job_id: Job ID

        Returns:
            Updated MarketplaceJob or None if not found
        """
        job = self.db.query(MarketplaceJob).filter(MarketplaceJob.id == job_id).first()
        if not job:
            return None

        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.now(timezone.utc)
        self.db.commit()

        # Update stats
        self._update_job_stats(job, success=True)

        logger.info(f"[VintedJobService] Completed job #{job_id}")
        return job

    def fail_job(self, job_id: int, error_message: str) -> MarketplaceJob | None:
        """
        Mark a job as failed.

        Args:
            job_id: Job ID
            error_message: Error description

        Returns:
            Updated MarketplaceJob or None if not found
        """
        job = self.db.query(MarketplaceJob).filter(MarketplaceJob.id == job_id).first()
        if not job:
            return None

        job.status = JobStatus.FAILED
        job.error_message = error_message
        job.completed_at = datetime.now(timezone.utc)
        self.db.commit()

        # Update stats
        self._update_job_stats(job, success=False)

        logger.warning(f"[VintedJobService] Failed job #{job_id}: {error_message}")
        return job

    def pause_job(self, job_id: int) -> MarketplaceJob | None:
        """
        Pause a running job.

        Args:
            job_id: Job ID

        Returns:
            Updated MarketplaceJob or None if not found
        """
        job = self.db.query(MarketplaceJob).filter(MarketplaceJob.id == job_id).first()
        if not job or job.status not in (JobStatus.PENDING, JobStatus.RUNNING):
            return None

        job.status = JobStatus.PAUSED
        self.db.commit()

        logger.info(f"[VintedJobService] Paused job #{job_id}")
        return job

    def resume_job(self, job_id: int) -> MarketplaceJob | None:
        """
        Resume a paused job.

        Args:
            job_id: Job ID

        Returns:
            Updated MarketplaceJob or None if not found
        """
        job = self.db.query(MarketplaceJob).filter(MarketplaceJob.id == job_id).first()
        if not job or job.status != JobStatus.PAUSED:
            return None

        job.status = JobStatus.PENDING
        # Reset expiration
        job.expires_at = datetime.now(timezone.utc) + timedelta(hours=JOB_EXPIRATION_HOURS)
        self.db.commit()

        logger.info(f"[VintedJobService] Resumed job #{job_id}")
        return job

    def cancel_job(self, job_id: int) -> MarketplaceJob | None:
        """
        Request job cancellation using advisory lock signaling (2026-01-19).

        For PENDING jobs: cancels immediately (no lock needed)
        For RUNNING jobs: signals via advisory lock (non-blocking, instant)
        For TERMINAL jobs: returns None (already finished)

        The advisory lock pattern ensures the cancel API returns immediately
        without waiting for row locks held by the running job.

        Args:
            job_id: Job ID

        Returns:
            Updated MarketplaceJob or None if not found/terminal
        """
        job = self.db.query(MarketplaceJob).filter(MarketplaceJob.id == job_id).first()

        if not job:
            return None

        # Terminal jobs can't be cancelled
        if job.is_terminal:
            logger.warning(f"[VintedJobService] Cannot cancel job #{job_id} - already terminal ({job.status})")
            return None

        # If job is PENDING, cancel immediately (not started yet)
        if job.status == JobStatus.PENDING:
            try:
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.now(timezone.utc)
                self.db.commit()

                # Cancel associated pending tasks
                self._cancel_job_tasks(job_id)

                logger.info(f"[VintedJobService] Job #{job_id} cancelled immediately (was pending)")
                return job
            except Exception as e:
                self.db.rollback()
                logger.error(f"[VintedJobService] Failed to cancel pending job #{job_id}: {e}")
                return None

        # If job is RUNNING, signal via advisory lock AND mark as cancelled
        if job.status == JobStatus.RUNNING:
            try:
                # Signal cancellation via advisory lock (for active workers)
                AdvisoryLockHelper.signal_cancel(self.db, job_id)

                # Mark job as CANCELLED immediately
                # This ensures the UI reflects the change even if no worker is active
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.now(timezone.utc)
                job.cancel_requested = False  # Reset flag since we're cancelling now
                self.db.commit()

                # Cancel associated pending tasks
                self._cancel_job_tasks(job_id)

                # Release advisory lock (cleanup)
                AdvisoryLockHelper.release_cancel_signal(self.db, job_id)

                logger.info(f"[VintedJobService] Job #{job_id} cancelled (was running)")
                return job

            except Exception as e:
                self.db.rollback()
                logger.error(f"[VintedJobService] Failed to cancel running job #{job_id}: {e}")
                return None

        # Other statuses (shouldn't happen but handle gracefully)
        return job

    def mark_job_cancelled(self, job_id: int) -> None:
        """
        Mark a job as cancelled and cleanup advisory locks (2026-01-19).

        This is the final step of cooperative cancellation.
        Called by handlers after they detect cancel signal and clean up.

        Args:
            job_id: Job ID to mark as cancelled
        """
        job = self.db.query(MarketplaceJob).filter(MarketplaceJob.id == job_id).first()

        if not job:
            return

        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.now(timezone.utc)
        job.cancel_requested = False  # Reset flag
        self.db.commit()

        # Release cancel signal lock if held (cleanup)
        AdvisoryLockHelper.release_cancel_signal(self.db, job_id)

        logger.info(f"[VintedJobService] Job #{job_id} marked as CANCELLED")

    def increment_retry(self, job_id: int) -> tuple[MarketplaceJob | None, bool]:
        """
        Increment retry count and check if max retries reached.

        Args:
            job_id: Job ID

        Returns:
            Tuple of (job, can_retry)
        """
        job = self.db.query(MarketplaceJob).filter(MarketplaceJob.id == job_id).first()
        if not job:
            return None, False

        action_type = self.get_action_type_by_id(job.action_type_id)
        max_retries = action_type.max_retries if action_type else 3

        job.retry_count += 1
        can_retry = job.retry_count < max_retries

        if not can_retry:
            job.status = JobStatus.FAILED
            job.error_message = f"Max retries ({max_retries}) exceeded"
            job.completed_at = datetime.now(timezone.utc)
            self._update_job_stats(job, success=False)

        self.db.commit()
        return job, can_retry

    # =========================================================================
    # JOB QUERIES
    # =========================================================================

    def get_job(self, job_id: int) -> MarketplaceJob | None:
        """Get job by ID."""
        return self.db.query(MarketplaceJob).filter(MarketplaceJob.id == job_id).first()

    def get_next_pending_job(self) -> MarketplaceJob | None:
        """
        Get the next job to process (highest priority, oldest first).

        Returns:
            Next pending MarketplaceJob or None
        """
        return (
            self.db.query(MarketplaceJob)
            .filter(MarketplaceJob.status == JobStatus.PENDING)
            .order_by(MarketplaceJob.priority, MarketplaceJob.created_at)
            .first()
        )

    def get_pending_jobs(self, limit: int = 10) -> list[MarketplaceJob]:
        """
        Get pending jobs ordered by priority.

        Args:
            limit: Maximum number of jobs

        Returns:
            List of pending MarketplaceJob
        """
        return (
            self.db.query(MarketplaceJob)
            .filter(MarketplaceJob.status == JobStatus.PENDING)
            .order_by(MarketplaceJob.priority, MarketplaceJob.created_at)
            .limit(limit)
            .all()
        )

    def get_batch_jobs(self, batch_id: str) -> list[MarketplaceJob]:
        """
        Get all jobs in a batch.

        Args:
            batch_id: Batch ID

        Returns:
            List of MarketplaceJob in the batch
        """
        # Get BatchJob by batch_id string first
        batch = self.db.query(BatchJob).filter(BatchJob.batch_id == batch_id).first()
        if not batch:
            return []

        # Then filter by FK
        return (
            self.db.query(MarketplaceJob)
            .filter(MarketplaceJob.batch_job_id == batch.id)
            .order_by(MarketplaceJob.created_at)
            .all()
        )

    def get_batch_summary(self, batch_id: str) -> dict:
        """
        Get summary of a batch.

        Args:
            batch_id: Batch ID

        Returns:
            Dict with batch statistics
        """
        jobs = self.get_batch_jobs(batch_id)
        if not jobs:
            return {"batch_id": batch_id, "total": 0}

        status_counts = {}
        for job in jobs:
            status = job.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "batch_id": batch_id,
            "total": len(jobs),
            "completed": status_counts.get("completed", 0),
            "failed": status_counts.get("failed", 0),
            "pending": status_counts.get("pending", 0),
            "running": status_counts.get("running", 0),
            "paused": status_counts.get("paused", 0),
            "cancelled": status_counts.get("cancelled", 0),
            "progress_percent": round(
                (status_counts.get("completed", 0) / len(jobs)) * 100, 1
            ),
        }

    def get_interrupted_jobs(self) -> list[MarketplaceJob]:
        """
        Get jobs that were interrupted (RUNNING but not completed).

        These are jobs that need user confirmation to resume.

        Returns:
            List of interrupted MarketplaceJob
        """
        return (
            self.db.query(MarketplaceJob)
            .filter(
                MarketplaceJob.status.in_([JobStatus.RUNNING, JobStatus.PAUSED]),
                MarketplaceJob.expires_at > datetime.now(timezone.utc),
            )
            .order_by(MarketplaceJob.priority, MarketplaceJob.created_at)
            .all()
        )

    # =========================================================================
    # EXPIRATION
    # =========================================================================

    def expire_old_jobs(self) -> int:
        """
        Mark expired pending jobs as EXPIRED.

        Returns:
            Number of jobs expired
        """
        now = datetime.now(timezone.utc)

        expired_jobs = (
            self.db.query(MarketplaceJob)
            .filter(
                MarketplaceJob.status.in_([JobStatus.PENDING, JobStatus.PAUSED]),
                MarketplaceJob.expires_at < now,
            )
            .all()
        )

        for job in expired_jobs:
            job.status = JobStatus.EXPIRED
            job.completed_at = now
            job.error_message = "Job expired (pending > 1h)"

        if expired_jobs:
            self.db.commit()
            logger.info(f"[VintedJobService] Expired {len(expired_jobs)} jobs")

        return len(expired_jobs)

    # =========================================================================
    # STATISTICS
    # =========================================================================

    def _update_job_stats(self, job: MarketplaceJob, success: bool) -> None:
        """
        Update daily statistics for a completed job.

        Args:
            job: Completed MarketplaceJob
            success: Whether job succeeded
        """
        today = datetime.now(timezone.utc).date()

        # Get or create stats record
        stats = (
            self.db.query(MarketplaceJobStats)
            .filter(
                MarketplaceJobStats.action_type_id == job.action_type_id,
                MarketplaceJobStats.marketplace == 'vinted',
                MarketplaceJobStats.date == today,
            )
            .first()
        )

        if not stats:
            stats = MarketplaceJobStats(
                marketplace='vinted',
                action_type_id=job.action_type_id,
                date=today,
                total_jobs=0,
                success_count=0,
                failure_count=0,
            )
            self.db.add(stats)

        stats.total_jobs += 1
        if success:
            stats.success_count += 1
        else:
            stats.failure_count += 1

        # Calculate average duration
        if job.started_at and job.completed_at:
            duration_ms = int((job.completed_at - job.started_at).total_seconds() * 1000)
            if stats.avg_duration_ms is None:
                stats.avg_duration_ms = duration_ms
            else:
                # Rolling average
                stats.avg_duration_ms = int(
                    (stats.avg_duration_ms * (stats.total_jobs - 1) + duration_ms)
                    / stats.total_jobs
                )

        self.db.commit()

    def get_stats(self, days: int = 7) -> list[dict]:
        """
        Get job statistics for the last N days.

        Args:
            days: Number of days to look back

        Returns:
            List of daily stats with action type info
        """
        start_date = datetime.now(timezone.utc).date() - timedelta(days=days)

        stats = (
            self.db.query(MarketplaceJobStats)
            .filter(
                MarketplaceJobStats.marketplace == 'vinted',
                MarketplaceJobStats.date >= start_date
            )
            .order_by(MarketplaceJobStats.date.desc())
            .all()
        )

        result = []
        for stat in stats:
            action_type = self.get_action_type_by_id(stat.action_type_id)
            result.append({
                "date": stat.date.isoformat(),
                "action_code": action_type.code if action_type else "unknown",
                "action_name": action_type.name if action_type else "Unknown",
                "total_jobs": stat.total_jobs,
                "success_count": stat.success_count,
                "failure_count": stat.failure_count,
                "success_rate": stat.success_rate,
                "avg_duration_ms": stat.avg_duration_ms,
            })

        return result

    # =========================================================================
    # TASK MANAGEMENT
    # =========================================================================

    def _cancel_job_tasks(self, job_id: int) -> int:
        """
        DEPRECATED (2026-01-09): WebSocket architecture, no granular tasks in DB.

        Cancel all pending tasks for a job.

        Args:
            job_id: Job ID

        Returns:
            Number of tasks cancelled (always 0 now)
        """
        # WebSocket architecture: no PluginTask in DB, cancellation handled real-time
        return 0

    def get_job_tasks(self, job_id: int) -> list:
        """
        DEPRECATED (2026-01-09): WebSocket architecture, no granular tasks in DB.

        Get all tasks for a job.

        Args:
            job_id: Job ID

        Returns:
            Empty list (no tasks in DB)
        """
        # WebSocket architecture: no PluginTask in DB
        return []

    def get_job_progress(self, job_id: int) -> dict:
        """
        Get progress of a job from result_data.progress (new format).

        Args:
            job_id: Job ID

        Returns:
            dict: Simple format {current, label} or empty dict if no progress
        """
        job = self.db.query(MarketplaceJob).filter(
            MarketplaceJob.id == job_id
        ).first()

        if not job or not job.result_data:
            return {}

        # New simple format: {current, label}
        progress_data = job.result_data.get("progress")
        if progress_data and "current" in progress_data:
            return progress_data

        # No progress data
        return {}
