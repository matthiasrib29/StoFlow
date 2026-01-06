"""
Vinted Job Status Manager

Service for managing Vinted job status transitions.

Business Rules (2025-12-19):
- Status transitions: PENDING -> RUNNING -> COMPLETED/FAILED
- PAUSED jobs can be resumed within expiration window
- CANCELLED jobs terminate all associated tasks
- Expired jobs are marked after 1 hour

Created: 2026-01-06
Author: Claude
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from models.user.plugin_task import PluginTask, TaskStatus
from models.user.vinted_job import JobStatus, VintedJob
from shared.logging_setup import get_logger

logger = get_logger(__name__)

# Job expiration time (1 hour)
JOB_EXPIRATION_HOURS = 1


class VintedJobStatusManager:
    """Service for managing Vinted job status transitions."""

    @staticmethod
    def start_job(db: Session, job: VintedJob) -> VintedJob:
        """
        Mark a job as running.

        Args:
            db: SQLAlchemy Session
            job: VintedJob to start

        Returns:
            Updated VintedJob
        """
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(timezone.utc)
        db.commit()

        logger.debug(f"[VintedJobStatusManager] Started job #{job.id}")
        return job

    @staticmethod
    def complete_job(
        db: Session,
        job: VintedJob,
        on_complete_callback: Optional[callable] = None,
    ) -> VintedJob:
        """
        Mark a job as completed successfully.

        Args:
            db: SQLAlchemy Session
            job: VintedJob to complete
            on_complete_callback: Optional callback for stats update

        Returns:
            Updated VintedJob
        """
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.now(timezone.utc)
        db.commit()

        if on_complete_callback:
            on_complete_callback(job, True)

        logger.info(f"[VintedJobStatusManager] Completed job #{job.id}")
        return job

    @staticmethod
    def fail_job(
        db: Session,
        job: VintedJob,
        error_message: str,
        on_complete_callback: Optional[callable] = None,
    ) -> VintedJob:
        """
        Mark a job as failed.

        Args:
            db: SQLAlchemy Session
            job: VintedJob to fail
            error_message: Error description
            on_complete_callback: Optional callback for stats update

        Returns:
            Updated VintedJob
        """
        job.status = JobStatus.FAILED
        job.error_message = error_message
        job.completed_at = datetime.now(timezone.utc)
        db.commit()

        if on_complete_callback:
            on_complete_callback(job, False)

        logger.warning(f"[VintedJobStatusManager] Failed job #{job.id}: {error_message}")
        return job

    @staticmethod
    def pause_job(db: Session, job: VintedJob) -> Optional[VintedJob]:
        """
        Pause a running or pending job.

        Args:
            db: SQLAlchemy Session
            job: VintedJob to pause

        Returns:
            Updated VintedJob or None if not pausable
        """
        if job.status not in (JobStatus.PENDING, JobStatus.RUNNING):
            return None

        job.status = JobStatus.PAUSED
        db.commit()

        logger.info(f"[VintedJobStatusManager] Paused job #{job.id}")
        return job

    @staticmethod
    def resume_job(db: Session, job: VintedJob) -> Optional[VintedJob]:
        """
        Resume a paused job.

        Args:
            db: SQLAlchemy Session
            job: VintedJob to resume

        Returns:
            Updated VintedJob or None if not resumable
        """
        if job.status != JobStatus.PAUSED:
            return None

        job.status = JobStatus.PENDING
        # Reset expiration
        job.expires_at = datetime.now(timezone.utc) + timedelta(hours=JOB_EXPIRATION_HOURS)
        db.commit()

        logger.info(f"[VintedJobStatusManager] Resumed job #{job.id}")
        return job

    @staticmethod
    def cancel_job(db: Session, job: VintedJob) -> Optional[VintedJob]:
        """
        Cancel a job and its pending tasks.

        Args:
            db: SQLAlchemy Session
            job: VintedJob to cancel

        Returns:
            Updated VintedJob or None if already terminal
        """
        if job.is_terminal:
            return None

        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.now(timezone.utc)
        db.commit()

        # Cancel associated pending tasks
        VintedJobStatusManager._cancel_job_tasks(db, job.id)

        logger.info(f"[VintedJobStatusManager] Cancelled job #{job.id}")
        return job

    @staticmethod
    def increment_retry(
        db: Session,
        job: VintedJob,
        max_retries: int = 3,
        on_max_retries_callback: Optional[callable] = None,
    ) -> tuple[VintedJob, bool]:
        """
        Increment retry count and check if max retries reached.

        Args:
            db: SQLAlchemy Session
            job: VintedJob to retry
            max_retries: Maximum retry attempts
            on_max_retries_callback: Optional callback for stats update

        Returns:
            Tuple of (job, can_retry)
        """
        job.retry_count += 1
        can_retry = job.retry_count < max_retries

        if not can_retry:
            job.status = JobStatus.FAILED
            job.error_message = f"Max retries ({max_retries}) exceeded"
            job.completed_at = datetime.now(timezone.utc)

            if on_max_retries_callback:
                on_max_retries_callback(job, False)

        db.commit()
        return job, can_retry

    @staticmethod
    def expire_old_jobs(db: Session) -> int:
        """
        Mark expired pending/paused jobs as EXPIRED.

        Args:
            db: SQLAlchemy Session

        Returns:
            Number of jobs expired
        """
        now = datetime.now(timezone.utc)

        expired_jobs = (
            db.query(VintedJob)
            .filter(
                VintedJob.status.in_([JobStatus.PENDING, JobStatus.PAUSED]),
                VintedJob.expires_at < now,
            )
            .all()
        )

        for job in expired_jobs:
            job.status = JobStatus.EXPIRED
            job.completed_at = now
            job.error_message = "Job expired (pending > 1h)"

        if expired_jobs:
            db.commit()
            logger.info(f"[VintedJobStatusManager] Expired {len(expired_jobs)} jobs")

        return len(expired_jobs)

    @staticmethod
    def _cancel_job_tasks(db: Session, job_id: int) -> int:
        """
        Cancel all pending tasks for a job.

        Args:
            db: SQLAlchemy Session
            job_id: Job ID

        Returns:
            Number of tasks cancelled
        """
        pending_tasks = (
            db.query(PluginTask)
            .filter(
                PluginTask.job_id == job_id,
                PluginTask.status == TaskStatus.PENDING,
            )
            .all()
        )

        for task in pending_tasks:
            task.status = TaskStatus.CANCELLED
            task.error_message = "Parent job cancelled"
            task.completed_at = datetime.now(timezone.utc)

        if pending_tasks:
            db.commit()

        return len(pending_tasks)


__all__ = ["VintedJobStatusManager", "JOB_EXPIRATION_HOURS"]
