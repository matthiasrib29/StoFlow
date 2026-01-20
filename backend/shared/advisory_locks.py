"""
PostgreSQL Advisory Locks Helper

Provides non-blocking signaling for job cancellation.
Advisory locks are automatically released when the session ends.

Architecture (2026-01-19):
- WORK_LOCK_NS (1): Worker holds this while processing a job
- CANCEL_LOCK_NS (2): Cancel API acquires this to signal cancellation

Usage:
    # Worker acquires work lock before processing
    if AdvisoryLockHelper.try_acquire_work_lock(db, job_id):
        try:
            # ... process job ...
            # Check for cancel signal periodically:
            if AdvisoryLockHelper.is_cancel_signaled(db, job_id):
                raise CancelledException("Job cancelled")
        finally:
            AdvisoryLockHelper.release_work_lock(db, job_id)

    # Cancel API signals cancellation
    AdvisoryLockHelper.signal_cancel(db, job_id)

Benefits:
- Non-blocking: cancel API returns immediately
- No deadlocks: advisory locks are session-scoped
- Auto-cleanup: locks released on session end/crash
"""
from sqlalchemy import text
from sqlalchemy.orm import Session

from shared.logging import get_logger

logger = get_logger(__name__)

# Namespace constants for advisory locks
# Using different namespaces to avoid conflicts
WORK_LOCK_NS = 1      # Worker holds this while processing
CANCEL_LOCK_NS = 2    # Cancel API acquires this to signal


class AdvisoryLockHelper:
    """Helper for PostgreSQL advisory locks used in job cancellation."""

    @staticmethod
    def try_acquire_work_lock(db: Session, job_id: int) -> bool:
        """
        Try to acquire work lock (non-blocking).

        Called by job processor before starting job execution.
        If another worker is processing the same job, this returns False.

        Args:
            db: SQLAlchemy session
            job_id: Job ID to lock

        Returns:
            True if lock acquired, False if already held by another session
        """
        try:
            result = db.execute(
                text("SELECT pg_try_advisory_lock(:ns, :id)"),
                {"ns": WORK_LOCK_NS, "id": job_id}
            ).scalar()
            return bool(result)
        except Exception as e:
            logger.error(f"Error acquiring work lock for job #{job_id}: {e}")
            return False

    @staticmethod
    def release_work_lock(db: Session, job_id: int) -> bool:
        """
        Release work lock.

        Called by job processor after job completion (success or failure).
        Safe to call even if lock not held (returns False).

        Args:
            db: SQLAlchemy session
            job_id: Job ID to unlock

        Returns:
            True if lock was released, False if not held
        """
        try:
            result = db.execute(
                text("SELECT pg_advisory_unlock(:ns, :id)"),
                {"ns": WORK_LOCK_NS, "id": job_id}
            ).scalar()
            return bool(result)
        except Exception as e:
            logger.error(f"Error releasing work lock for job #{job_id}: {e}")
            return False

    @staticmethod
    def signal_cancel(db: Session, job_id: int, max_retries: int = 3) -> bool:
        """
        Signal cancellation by acquiring cancel lock (non-blocking with retry).

        Called by cancel API to signal that a job should stop.
        Uses pg_try_advisory_lock (non-blocking) to avoid statement timeout issues.

        The worker checks this lock periodically via is_cancel_signaled().
        When worker sees the lock is held, it knows to stop.

        Args:
            db: SQLAlchemy session
            job_id: Job ID to signal cancellation
            max_retries: Number of retry attempts if lock not acquired

        Returns:
            True if lock acquired (cancel signaled), False otherwise
        """
        import time

        for attempt in range(max_retries):
            try:
                # Use pg_try_advisory_lock (non-blocking) to avoid timeout
                result = db.execute(
                    text("SELECT pg_try_advisory_lock(:ns, :id)"),
                    {"ns": CANCEL_LOCK_NS, "id": job_id}
                ).scalar()

                if result:
                    logger.debug(f"Cancel signal sent for job #{job_id} via advisory lock")
                    return True
                else:
                    # Lock not acquired - could mean:
                    # 1. Previous cancel already signaled (lock held by another session)
                    # 2. Worker is checking (very brief window)
                    if attempt < max_retries - 1:
                        time.sleep(0.05)  # 50ms between retries
                    else:
                        # After all retries, assume cancel already signaled
                        logger.debug(f"Cancel lock for job #{job_id} already held (cancel may be in progress)")
                        return True  # Return True since cancel is effectively signaled

            except Exception as e:
                logger.error(f"Error signaling cancel for job #{job_id} (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(0.05)

        return False

    @staticmethod
    def is_cancel_signaled(db: Session, job_id: int) -> bool:
        """
        Check if cancellation was signaled (non-blocking).

        Called by worker periodically during long operations.
        If cancel lock is held by the cancel API, this returns True.

        Implementation: Try to acquire the cancel lock:
        - If we get it: no cancel signal -> release it -> return False
        - If we don't get it: someone else has it (cancel API) -> return True

        Args:
            db: SQLAlchemy session
            job_id: Job ID to check

        Returns:
            True if cancel signal received, False otherwise
        """
        try:
            # Try to acquire cancel lock (non-blocking)
            result = db.execute(
                text("SELECT pg_try_advisory_lock(:ns, :id)"),
                {"ns": CANCEL_LOCK_NS, "id": job_id}
            ).scalar()

            if result:
                # We got the lock -> no cancel signal -> release it
                db.execute(
                    text("SELECT pg_advisory_unlock(:ns, :id)"),
                    {"ns": CANCEL_LOCK_NS, "id": job_id}
                )
                return False
            else:
                # Lock held by cancel API -> cancel signal received
                return True

        except Exception as e:
            logger.error(f"Error checking cancel signal for job #{job_id}: {e}")
            # On error, assume no cancel signal (safer than false positive)
            return False

    @staticmethod
    def release_cancel_signal(db: Session, job_id: int) -> bool:
        """
        Release cancel signal lock.

        Called after job is marked as cancelled to cleanup the advisory lock.
        Safe to call even if lock not held (returns False).

        Note: Advisory locks are also auto-released when session ends,
        but explicit release is cleaner.

        Args:
            db: SQLAlchemy session
            job_id: Job ID to release cancel signal

        Returns:
            True if lock was released, False if not held
        """
        try:
            result = db.execute(
                text("SELECT pg_advisory_unlock(:ns, :id)"),
                {"ns": CANCEL_LOCK_NS, "id": job_id}
            ).scalar()
            return bool(result)
        except Exception as e:
            logger.error(f"Error releasing cancel signal for job #{job_id}: {e}")
            return False

    @staticmethod
    def release_all_job_locks(db: Session, job_id: int) -> None:
        """
        Release all locks for a job (work + cancel).

        Utility method for cleanup in finally blocks.

        Args:
            db: SQLAlchemy session
            job_id: Job ID to release all locks
        """
        AdvisoryLockHelper.release_work_lock(db, job_id)
        AdvisoryLockHelper.release_cancel_signal(db, job_id)
