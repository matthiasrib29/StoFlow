"""
Marketplace Job Service

Orchestrates marketplace jobs with priority management, status tracking,
and integration with the plugin task system.

Extends VintedJobService to support multiple marketplaces (Vinted, eBay, Etsy).

Business Rules (2026-01-07):
- 1 Job = 1 product operation
- Jobs grouped by batch_job_id (FK) or batch_id (string, deprecated)
- Supports marketplace field (vinted, ebay, etsy)
- Priority: 1=CRITICAL, 2=HIGH, 3=NORMAL, 4=LOW
- Expiration: 1 hour for pending jobs
- Retry: 3 attempts max, then FAILED
- Auto-updates parent BatchJob progress

Author: Claude
Date: 2026-01-07
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import and_, func, text
from sqlalchemy.orm import Session

from models.public.marketplace_action_type import MarketplaceActionType
from shared.advisory_locks import AdvisoryLockHelper
from models.user.marketplace_task import MarketplaceTask, TaskStatus
from models.user.marketplace_job import JobStatus, MarketplaceJob
from models.user.batch_job import BatchJob
from models.user.marketplace_job_stats import MarketplaceJobStats
from shared.logging_setup import get_logger

logger = get_logger(__name__)


# Job expiration time (1 hour)
JOB_EXPIRATION_HOURS = 1


class MarketplaceJobService:
    """
    Service for managing marketplace jobs.

    Handles job creation, status updates, priority management,
    statistics tracking, and batch progress updates.
    """

    def __init__(self, db: Session):
        self.db = db
        self._action_types_cache: dict[tuple[str, str], Any] = {}

    # =========================================================================
    # ACTION TYPES
    # =========================================================================

    def get_action_type(
        self, marketplace: str, action_code: str
    ) -> MarketplaceActionType | None:
        """
        Get action type by marketplace and code (with caching).

        Args:
            marketplace: Marketplace identifier (vinted, ebay, etsy)
            action_code: Action type code (publish, sync, orders, etc.)

        Returns:
            Action type or None
        """
        cache_key = (marketplace, action_code)

        if cache_key not in self._action_types_cache:
            # Query action type from public.marketplace_action_types table
            action_type = (
                self.db.query(MarketplaceActionType)
                .filter(
                    MarketplaceActionType.marketplace == marketplace,
                    MarketplaceActionType.code == action_code
                )
                .first()
            )
            if action_type:
                self._action_types_cache[cache_key] = action_type
            else:
                logger.warning(
                    f"Action type not found: marketplace={marketplace}, code={action_code}"
                )
                return None

        return self._action_types_cache.get(cache_key)

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
        marketplace: str,
        action_code: str,
        product_id: int | None = None,
        batch_id: str | None = None,
        batch_job_id: int | None = None,
        priority: int | None = None,
        input_data: dict | None = None,
    ) -> MarketplaceJob:
        """
        Create a new marketplace job.

        Args:
            marketplace: Target marketplace (vinted, ebay, etsy)
            action_code: Action type code (publish, sync, etc.)
            product_id: Product ID (optional)
            batch_id: DEPRECATED - Batch ID string for grouping (optional)
            batch_job_id: BatchJob FK (preferred over batch_id)
            priority: Override priority (optional, uses action_type default)
            input_data: Initial data/parameters for the job (optional)

        Returns:
            Created MarketplaceJob

        Raises:
            ValueError: If action_code is invalid for the marketplace
        """
        action_type = self.get_action_type(marketplace, action_code)
        if not action_type:
            raise ValueError(
                f"Invalid action code '{action_code}' for marketplace '{marketplace}'"
            )

        # Calculate expiration time
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=JOB_EXPIRATION_HOURS)

        job = MarketplaceJob(
            marketplace=marketplace,
            action_type_id=action_type.id,
            product_id=product_id,
            # batch_id removed - column no longer exists in model
            batch_job_id=batch_job_id,
            status=JobStatus.PENDING,
            priority=priority if priority is not None else action_type.priority,
            expires_at=expires_at,
            created_at=now,
            input_data=input_data,
        )

        self.db.add(job)
        self.db.flush()  # Get ID without committing

        logger.debug(
            f"[MarketplaceJobService] Created job #{job.id} "
            f"(marketplace={marketplace}, action={action_code}, product={product_id}, "
            f"batch_job_id={batch_job_id})"
        )

        return job

    def create_batch_jobs(
        self,
        marketplace: str,
        action_code: str,
        product_ids: list[int],
        priority: int | None = None,
    ) -> tuple[str, list[MarketplaceJob]]:
        """
        Create multiple jobs for a batch operation (DEPRECATED).

        This method is kept for backward compatibility.
        New code should use BatchJobService.create_batch_job() instead.

        Args:
            marketplace: Target marketplace (vinted, ebay, etsy)
            action_code: Action type code
            product_ids: List of product IDs
            priority: Override priority (optional)

        Returns:
            Tuple of (batch_id string, list of created jobs)
        """
        logger.warning(
            "create_batch_jobs() is deprecated. Use BatchJobService.create_batch_job() instead."
        )

        batch_id = f"{action_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

        jobs = []
        for product_id in product_ids:
            job = self.create_job(
                marketplace=marketplace,
                action_code=action_code,
                product_id=product_id,
                batch_id=batch_id,
                priority=priority,
            )
            jobs.append(job)

        self.db.commit()

        logger.info(
            f"[MarketplaceJobService] Created batch {batch_id} with {len(jobs)} jobs"
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
        job = (
            self.db.query(MarketplaceJob).filter(MarketplaceJob.id == job_id).first()
        )
        if not job:
            return None

        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(timezone.utc)
        self.db.flush()  # Use flush, not commit (preserve search_path)

        logger.debug(f"[MarketplaceJobService] Started job #{job_id}")
        return job

    def complete_job(
        self, job_id: int, result_data: dict | None = None
    ) -> MarketplaceJob | None:
        """
        Mark a job as completed successfully.

        Also updates parent BatchJob progress if applicable.

        Args:
            job_id: Job ID
            result_data: Optional result data from execution (stored in output_data)

        Returns:
            Updated MarketplaceJob or None if not found
        """
        job = (
            self.db.query(MarketplaceJob).filter(MarketplaceJob.id == job_id).first()
        )
        if not job:
            return None

        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.now(timezone.utc)

        # Store result data if provided
        if result_data:
            job.result_data = result_data

        self.db.flush()  # Use flush, not commit (preserve search_path)

        # Update stats
        self._update_job_stats(job, success=True)

        # Update parent batch progress if applicable
        if job.batch_job_id:
            from services.marketplace.batch_job_service import BatchJobService

            batch_service = BatchJobService(self.db)
            batch_service.update_batch_progress(job.batch_job_id)

        logger.info(f"[MarketplaceJobService] Completed job #{job_id}")
        return job

    def fail_job(self, job_id: int, error_message: str) -> MarketplaceJob | None:
        """
        Mark a job as failed.

        Also updates parent BatchJob progress if applicable.

        Args:
            job_id: Job ID
            error_message: Error description

        Returns:
            Updated MarketplaceJob or None if not found
        """
        job = (
            self.db.query(MarketplaceJob).filter(MarketplaceJob.id == job_id).first()
        )
        if not job:
            return None

        job.status = JobStatus.FAILED
        job.error_message = error_message
        job.completed_at = datetime.now(timezone.utc)
        self.db.flush()  # Use flush, not commit (preserve search_path)

        # Update stats
        self._update_job_stats(job, success=False)

        # Update parent batch progress if applicable
        if job.batch_job_id:
            from services.marketplace.batch_job_service import BatchJobService

            batch_service = BatchJobService(self.db)
            batch_service.update_batch_progress(job.batch_job_id)

        logger.warning(
            f"[MarketplaceJobService] Failed job #{job_id}: {error_message}"
        )
        return job

    def pause_job(self, job_id: int) -> MarketplaceJob | None:
        """
        Pause a running job.

        Args:
            job_id: Job ID

        Returns:
            Updated MarketplaceJob or None if not found
        """
        job = (
            self.db.query(MarketplaceJob).filter(MarketplaceJob.id == job_id).first()
        )
        if not job or job.status not in (JobStatus.PENDING, JobStatus.RUNNING):
            return None

        job.status = JobStatus.PAUSED
        self.db.flush()  # Use flush, not commit (preserve search_path)

        logger.info(f"[MarketplaceJobService] Paused job #{job_id}")
        return job

    def resume_job(self, job_id: int) -> MarketplaceJob | None:
        """
        Resume a paused job.

        Args:
            job_id: Job ID

        Returns:
            Updated MarketplaceJob or None if not found
        """
        job = (
            self.db.query(MarketplaceJob).filter(MarketplaceJob.id == job_id).first()
        )
        if not job or job.status != JobStatus.PAUSED:
            return None

        job.status = JobStatus.PENDING
        # Reset expiration
        job.expires_at = datetime.now(timezone.utc) + timedelta(
            hours=JOB_EXPIRATION_HOURS
        )
        self.db.flush()  # Use flush, not commit (preserve search_path)

        logger.info(f"[MarketplaceJobService] Resumed job #{job_id}")
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
        job = (
            self.db.query(MarketplaceJob).filter(MarketplaceJob.id == job_id).first()
        )

        if not job:
            return None

        # Terminal jobs can't be cancelled
        if job.is_terminal:
            logger.warning(f"[MarketplaceJobService] Cannot cancel job #{job_id} - already terminal ({job.status})")
            return None

        # If job is PENDING, cancel immediately (not started yet)
        if job.status == JobStatus.PENDING:
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.now(timezone.utc)
            self.db.flush()  # Use flush, not commit (preserve search_path)

            # Cancel associated pending tasks
            self._cancel_job_tasks(job_id)

            logger.info(f"[MarketplaceJobService] Job #{job_id} cancelled immediately (was pending)")
            return job

        # If job is RUNNING, signal via advisory lock AND mark as cancelled
        if job.status == JobStatus.RUNNING:
            # Signal cancellation via advisory lock (for active workers)
            AdvisoryLockHelper.signal_cancel(self.db, job_id)

            # Mark job as CANCELLED immediately
            # This ensures the UI reflects the change even if no worker is active
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.now(timezone.utc)
            job.cancel_requested = False  # Reset flag since we're cancelling now
            self.db.flush()  # Use flush, not commit (preserve search_path)

            # Cancel associated pending tasks
            self._cancel_job_tasks(job_id)

            # Release advisory lock (cleanup)
            AdvisoryLockHelper.release_cancel_signal(self.db, job_id)

            logger.info(f"[MarketplaceJobService] Job #{job_id} cancelled (was running)")
            return job

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
        self.db.flush()  # Use flush, not commit (preserve search_path)

        # Release cancel signal lock if held (cleanup)
        AdvisoryLockHelper.release_cancel_signal(self.db, job_id)

        logger.info(f"[MarketplaceJobService] Job #{job_id} marked as CANCELLED")

    def increment_retry(self, job_id: int) -> tuple[MarketplaceJob | None, bool]:
        """
        Increment retry count and check if max retries reached.

        This is a critical method in the retry logic flow:
        1. Load the job from database
        2. Increment retry_count (starts at 0)
        3. Compare with max_retries (default: 3, configurable per action type)
        4. If max retries exceeded: Mark job as FAILED, update stats, update parent batch
        5. Return (job, can_retry) tuple

        Retry Logic Example:
        - Attempt 1 fails: retry_count=0 → 1, can_retry=True (1 < 3)
        - Attempt 2 fails: retry_count=1 → 2, can_retry=True (2 < 3)
        - Attempt 3 fails: retry_count=2 → 3, can_retry=False (3 >= 3)
        - Status changed to FAILED, error_message set

        Why flush() instead of commit():
        - Preserves search_path context (multi-tenant isolation)
        - Caller (MarketplaceJobProcessor) will commit after setting status to PENDING
        - Avoids nested commits which can cause transaction issues

        Args:
            job_id: Job ID to increment retry count

        Returns:
            Tuple of (job, can_retry):
                - job: Updated MarketplaceJob instance (or None if not found)
                - can_retry: True if retry_count < max_retries, False otherwise
        """
        job = (
            self.db.query(MarketplaceJob).filter(MarketplaceJob.id == job_id).first()
        )
        if not job:
            return None, False

        # Get max_retries from job or use default (3)
        # Can be overridden per job or inherited from action_type
        action_type = self.get_action_type_by_id(job.action_type_id)
        max_retries = job.max_retries if job.max_retries else 3

        # Increment retry counter
        # retry_count starts at 0, increments after each failure
        job.retry_count += 1

        # Check if we can retry
        # can_retry = True means job will be reset to PENDING by caller
        can_retry = job.retry_count < max_retries

        if not can_retry:
            # Max retries exceeded - mark as permanently FAILED
            job.status = JobStatus.FAILED
            job.error_message = f"Max retries ({max_retries}) exceeded"
            job.completed_at = datetime.now(timezone.utc)

            # Update daily statistics (failure count)
            self._update_job_stats(job, success=False)

            # Update parent batch progress if job belongs to a batch
            # This ensures batch status reflects failed jobs
            if job.batch_job_id:
                from services.marketplace.batch_job_service import BatchJobService

                batch_service = BatchJobService(self.db)
                batch_service.update_batch_progress(job.batch_job_id)

        # Use flush() instead of commit()
        # Preserves schema_translate_map (multi-tenant context)
        # Caller will commit after setting appropriate status
        self.db.flush()

        return job, can_retry

    # =========================================================================
    # JOB QUERIES
    # =========================================================================

    def get_job(self, job_id: int) -> MarketplaceJob | None:
        """Get job by ID."""
        return (
            self.db.query(MarketplaceJob).filter(MarketplaceJob.id == job_id).first()
        )

    def get_next_pending_job(
        self, marketplace: str | None = None
    ) -> MarketplaceJob | None:
        """
        Get the next job to process using FOR UPDATE SKIP LOCKED.

        This prevents race conditions when multiple workers claim jobs.
        SKIP LOCKED ensures no deadlock - locked rows are simply skipped.

        Args:
            marketplace: Filter by marketplace (optional)

        Returns:
            Next pending MarketplaceJob or None
        """
        query = self.db.query(MarketplaceJob).filter(
            MarketplaceJob.status == JobStatus.PENDING
        )

        if marketplace:
            query = query.filter(MarketplaceJob.marketplace == marketplace)

        # ORDER BY priority (1=CRITICAL first), then oldest first
        # FOR UPDATE SKIP LOCKED: atomic claim, no deadlock
        return query.order_by(
            MarketplaceJob.priority, MarketplaceJob.created_at
        ).with_for_update(skip_locked=True).first()

    def get_pending_jobs(
        self, limit: int = 10, marketplace: str | None = None
    ) -> list[MarketplaceJob]:
        """
        Get pending jobs ordered by priority.

        Args:
            limit: Maximum number of jobs
            marketplace: Filter by marketplace (optional)

        Returns:
            List of pending MarketplaceJob
        """
        query = self.db.query(MarketplaceJob).filter(
            MarketplaceJob.status == JobStatus.PENDING
        )

        if marketplace:
            query = query.filter(MarketplaceJob.marketplace == marketplace)

        return (
            query.order_by(MarketplaceJob.priority, MarketplaceJob.created_at)
            .limit(limit)
            .all()
        )

    def get_batch_jobs(self, batch_id: str) -> list[MarketplaceJob]:
        """
        Get all jobs in a batch (by batch_id string).

        DEPRECATED: Use BatchJobService.get_batch_by_id() instead.

        Args:
            batch_id: Batch ID string

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
        Get summary of a batch (by batch_id string).

        DEPRECATED: Use BatchJobService.get_batch_summary() instead.

        Args:
            batch_id: Batch ID string

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

    def get_interrupted_jobs(
        self, marketplace: str | None = None
    ) -> list[MarketplaceJob]:
        """
        Get jobs that were interrupted (RUNNING but not completed).

        These are jobs that need user confirmation to resume.

        Args:
            marketplace: Filter by marketplace (optional)

        Returns:
            List of interrupted MarketplaceJob
        """
        query = self.db.query(MarketplaceJob).filter(
            MarketplaceJob.status.in_([JobStatus.RUNNING, JobStatus.PAUSED]),
            MarketplaceJob.expires_at > datetime.now(timezone.utc),
        )

        if marketplace:
            query = query.filter(MarketplaceJob.marketplace == marketplace)

        return query.order_by(
            MarketplaceJob.priority, MarketplaceJob.created_at
        ).all()

    # =========================================================================
    # EXPIRATION
    # =========================================================================

    def expire_old_jobs(self, marketplace: str | None = None) -> int:
        """
        Mark expired pending jobs as EXPIRED.

        Args:
            marketplace: Filter by marketplace (optional)

        Returns:
            Number of jobs expired
        """
        now = datetime.now(timezone.utc)

        query = self.db.query(MarketplaceJob).filter(
            MarketplaceJob.status.in_([JobStatus.PENDING, JobStatus.PAUSED]),
            MarketplaceJob.expires_at < now,
        )

        if marketplace:
            query = query.filter(MarketplaceJob.marketplace == marketplace)

        expired_jobs = query.all()

        for job in expired_jobs:
            job.status = JobStatus.EXPIRED
            job.completed_at = now
            job.error_message = "Job expired (pending > 1h)"

        if expired_jobs:
            self.db.flush()  # Use flush, not commit (preserve search_path)
            logger.info(
                f"[MarketplaceJobService] Expired {len(expired_jobs)} jobs"
            )

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

        # Get or create stats record (filtered by marketplace)
        stats = (
            self.db.query(MarketplaceJobStats)
            .filter(
                MarketplaceJobStats.action_type_id == job.action_type_id,
                MarketplaceJobStats.marketplace == job.marketplace,
                MarketplaceJobStats.date == today,
            )
            .first()
        )

        if not stats:
            stats = MarketplaceJobStats(
                marketplace=job.marketplace,
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
            duration_ms = int(
                (job.completed_at - job.started_at).total_seconds() * 1000
            )
            if stats.avg_duration_ms is None:
                stats.avg_duration_ms = duration_ms
            else:
                # Rolling average
                stats.avg_duration_ms = int(
                    (stats.avg_duration_ms * (stats.total_jobs - 1) + duration_ms)
                    / stats.total_jobs
                )

        self.db.flush()  # Use flush, not commit (preserve search_path)

    def get_stats(self, days: int = 7, marketplace: str | None = None) -> list[dict]:
        """
        Get job statistics for the last N days.

        Args:
            days: Number of days to look back
            marketplace: Optional marketplace filter (vinted, ebay, etsy). If None, returns all marketplaces.

        Returns:
            List of daily stats with action type info
        """
        start_date = datetime.now(timezone.utc).date() - timedelta(days=days)

        query = self.db.query(MarketplaceJobStats).filter(
            MarketplaceJobStats.date >= start_date
        )

        if marketplace:
            query = query.filter(MarketplaceJobStats.marketplace == marketplace)

        stats = query.order_by(MarketplaceJobStats.date.desc()).all()

        result = []
        for stat in stats:
            action_type = self.get_action_type_by_id(stat.action_type_id)
            result.append(
                {
                    "date": stat.date.isoformat(),
                    "marketplace": stat.marketplace,
                    "action_code": action_type.code if action_type else "unknown",
                    "action_name": action_type.name if action_type else "Unknown",
                    "total_jobs": stat.total_jobs,
                    "success_count": stat.success_count,
                    "failure_count": stat.failure_count,
                    "success_rate": stat.success_rate,
                    "avg_duration_ms": stat.avg_duration_ms,
                }
            )

        return result

    # =========================================================================
    # TASK MANAGEMENT
    # =========================================================================

    def _cancel_job_tasks(self, job_id: int) -> int:
        """
        Cancel all pending tasks for a job.

        Args:
            job_id: Job ID

        Returns:
            Number of tasks cancelled
        """
        pending_tasks = (
            self.db.query(MarketplaceTask)
            .filter(
                MarketplaceTask.job_id == job_id,
                MarketplaceTask.status == TaskStatus.PENDING,
            )
            .all()
        )

        for task in pending_tasks:
            task.status = TaskStatus.CANCELLED
            task.error_message = "Parent job cancelled"
            task.completed_at = datetime.now(timezone.utc)

        if pending_tasks:
            self.db.flush()  # Use flush, not commit (preserve search_path)

        return len(pending_tasks)

    def get_job_tasks(self, job_id: int) -> list[MarketplaceTask]:
        """
        Get all tasks for a job.

        Args:
            job_id: Job ID

        Returns:
            List of MarketplaceTask
        """
        return (
            self.db.query(MarketplaceTask)
            .filter(MarketplaceTask.job_id == job_id)
            .order_by(MarketplaceTask.created_at)
            .all()
        )

    def get_job_progress(self, job_id: int) -> dict:
        """
        Get progress of a job based on its tasks.

        Args:
            job_id: Job ID

        Returns:
            Dict with task counts and progress
        """
        tasks = self.get_job_tasks(job_id)
        if not tasks:
            return {
                "total": 0,
                "completed": 0,
                "failed": 0,
                "pending": 0,
                "progress_percent": 0,
            }

        completed = sum(1 for t in tasks if t.status == TaskStatus.SUCCESS)
        failed = sum(1 for t in tasks if t.status == TaskStatus.FAILED)
        pending = sum(
            1
            for t in tasks
            if t.status in (TaskStatus.PENDING, TaskStatus.PROCESSING)
        )

        return {
            "total": len(tasks),
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "progress_percent": round((completed / len(tasks)) * 100, 1)
            if tasks
            else 0,
        }
