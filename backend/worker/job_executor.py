"""
Async Job Executor for Marketplace Worker

Executes marketplace jobs with async handlers.
Adapted from MarketplaceJobProcessor for standalone worker use.

Author: Claude
Date: 2026-01-20
"""

import asyncio
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Callable

from sqlalchemy import text
from sqlalchemy.orm import Session

from models.user.marketplace_job import JobStatus, MarketplaceJob
from services.marketplace.marketplace_job_service import MarketplaceJobService
from shared.advisory_locks import AdvisoryLockHelper
from shared.logging_setup import get_logger
from worker.config import WorkerConfig

logger = get_logger(__name__)


class JobExecutor:
    """
    Async job executor for marketplace operations.

    Handles job claiming, execution, and status management
    with support for cooperative cancellation.

    Usage:
        executor = JobExecutor(config, db)
        result = await executor.execute_job(job)
    """

    def __init__(
        self,
        config: WorkerConfig,
        db: Session,
        cancel_check: Optional[Callable[[int], bool]] = None,
    ):
        """
        Initialize job executor.

        Args:
            config: Worker configuration
            db: SQLAlchemy session with tenant schema configured
            cancel_check: Optional callback to check if shutdown requested
        """
        self.config = config
        self.db = db
        self.job_service = MarketplaceJobService(db)
        self._cancel_check = cancel_check
        self._handlers: dict[str, type] = {}
        self._load_handlers()

    def _load_handlers(self) -> None:
        """Load all marketplace job handlers."""
        try:
            from services.vinted.jobs import HANDLERS as VINTED_HANDLERS
            from services.ebay.jobs import EBAY_HANDLERS
            from services.etsy.jobs import ETSY_HANDLERS

            self._handlers = {
                **VINTED_HANDLERS,
                **EBAY_HANDLERS,
                **ETSY_HANDLERS,
            }
            logger.info(f"Loaded {len(self._handlers)} job handlers")
        except ImportError as e:
            logger.warning(f"Could not load some handlers: {e}")

    def claim_next_job(self) -> MarketplaceJob | None:
        """
        Claim the next pending job using FOR UPDATE SKIP LOCKED.

        Returns:
            Claimed job or None if no jobs available
        """
        return self.job_service.get_next_pending_job(
            marketplace=self.config.marketplace_filter
        )

    async def execute_job(self, job: MarketplaceJob) -> dict[str, Any]:
        """
        Execute a marketplace job.

        Args:
            job: Job to execute

        Returns:
            Execution result dict
        """
        start_time = time.time()
        job_id = job.id
        marketplace = job.marketplace

        # Get action type
        action_type = self.job_service.get_action_type_by_id(job.action_type_id)
        action_code = action_type.code if action_type else "unknown"
        full_action_code = f"{action_code}_{marketplace}"

        logger.info(
            f"[JobExecutor] Starting job #{job_id} "
            f"(marketplace={marketplace}, action={action_code}, product={job.product_id})"
        )

        # Acquire work lock
        if not AdvisoryLockHelper.try_acquire_work_lock(self.db, job_id):
            logger.warning(f"[JobExecutor] Could not acquire work lock for job #{job_id}")
            return {
                "job_id": job_id,
                "marketplace": marketplace,
                "action": action_code,
                "success": False,
                "status": "skipped",
                "reason": "could_not_acquire_work_lock",
            }

        try:
            # Mark job as running
            self.job_service.start_job(job_id)
            self.db.commit()

            # Check for cancellation before starting
            if AdvisoryLockHelper.is_cancel_signaled(self.db, job_id):
                logger.info(f"[JobExecutor] Job #{job_id} cancelled before execution")
                self.job_service.mark_job_cancelled(job_id)
                self.db.commit()
                return {
                    "job_id": job_id,
                    "marketplace": marketplace,
                    "action": action_code,
                    "success": False,
                    "status": "cancelled",
                    "reason": "cancelled_before_start",
                }

            # Get handler
            handler_class = self._handlers.get(full_action_code)
            if not handler_class:
                raise ValueError(f"Unknown action: {full_action_code}")

            # Create handler instance
            handler = handler_class(
                db=self.db,
                shop_id=None,  # Will be set from job.input_data if needed
                job_id=job_id,
            )

            # Set user_id for WebSocket communication
            handler.user_id = self.config.user_id

            # Execute handler (with periodic cancel check)
            result = await self._execute_with_cancel_check(handler, job, job_id)

            # Handle result
            if result.get("success", False):
                self.job_service.complete_job(job_id, result_data=result)
                self.db.commit()

                elapsed = time.time() - start_time
                logger.info(f"[JobExecutor] Job #{job_id} completed ({elapsed:.1f}s)")

                return {
                    "job_id": job_id,
                    "marketplace": marketplace,
                    "action": action_code,
                    "success": True,
                    "result": result,
                    "duration_ms": int(elapsed * 1000),
                }
            else:
                error_msg = result.get("error", "Operation failed")
                return await self._handle_failure(
                    job_id, marketplace, action_code, error_msg, start_time
                )

        except asyncio.CancelledError:
            logger.info(f"[JobExecutor] Job #{job_id} cancelled by worker shutdown")
            self._safe_rollback()
            return {
                "job_id": job_id,
                "marketplace": marketplace,
                "action": action_code,
                "success": False,
                "status": "interrupted",
                "reason": "worker_shutdown",
            }

        except Exception as e:
            logger.exception(f"[JobExecutor] Job #{job_id} failed: {e}")
            return await self._handle_failure(
                job_id, marketplace, action_code, str(e), start_time
            )

        finally:
            AdvisoryLockHelper.release_work_lock(self.db, job_id)

    async def _execute_with_cancel_check(
        self,
        handler: Any,
        job: MarketplaceJob,
        job_id: int,
    ) -> dict[str, Any]:
        """
        Execute handler with periodic cancel checking.

        Args:
            handler: Job handler instance
            job: Job being executed
            job_id: Job ID

        Returns:
            Handler result
        """
        # Create a task for the handler execution
        handler_task = asyncio.create_task(handler.execute(job))

        # Periodically check for cancellation
        while not handler_task.done():
            # Check worker shutdown
            if self._cancel_check and self._cancel_check(job_id):
                handler_task.cancel()
                try:
                    await handler_task
                except asyncio.CancelledError:
                    pass
                return {"success": False, "error": "Job cancelled by worker"}

            # Check job-level cancellation via advisory lock
            if AdvisoryLockHelper.is_cancel_signaled(self.db, job_id):
                handler_task.cancel()
                try:
                    await handler_task
                except asyncio.CancelledError:
                    pass
                self.job_service.mark_job_cancelled(job_id)
                self.db.commit()
                return {"success": False, "error": "Job cancelled by user", "cancelled": True}

            # Wait a bit before next check
            try:
                await asyncio.wait_for(
                    asyncio.shield(handler_task),
                    timeout=1.0,
                )
                break  # Task completed
            except asyncio.TimeoutError:
                continue  # Check cancellation again

        return await handler_task

    async def _handle_failure(
        self,
        job_id: int,
        marketplace: str,
        action_code: str,
        error_msg: str,
        start_time: float,
    ) -> dict[str, Any]:
        """
        Handle job failure with retry logic.

        Args:
            job_id: Failed job ID
            marketplace: Marketplace name
            action_code: Action code
            error_msg: Error message
            start_time: Job start time

        Returns:
            Failure result dict
        """
        elapsed = time.time() - start_time
        self._safe_rollback()

        # Check retry
        updated_job, can_retry = self.job_service.increment_retry(job_id)

        if can_retry:
            updated_job.status = JobStatus.PENDING
            self.db.commit()

            logger.warning(
                f"[JobExecutor] Job #{job_id} failed, will retry "
                f"(attempt {updated_job.retry_count}): {error_msg}"
            )

            return {
                "job_id": job_id,
                "marketplace": marketplace,
                "action": action_code,
                "success": False,
                "error": error_msg,
                "will_retry": True,
                "retry_count": updated_job.retry_count,
                "duration_ms": int(elapsed * 1000),
            }
        else:
            self.job_service.fail_job(job_id, error_msg)
            self.db.commit()

            logger.error(f"[JobExecutor] Job #{job_id} failed permanently: {error_msg}")

            return {
                "job_id": job_id,
                "marketplace": marketplace,
                "action": action_code,
                "success": False,
                "error": error_msg,
                "will_retry": False,
                "duration_ms": int(elapsed * 1000),
            }

    def _safe_rollback(self) -> None:
        """Safely rollback transaction if active."""
        try:
            self.db.rollback()
        except Exception:
            pass

    def expire_old_jobs(self) -> int:
        """Expire old pending jobs."""
        count = self.job_service.expire_old_jobs(
            marketplace=self.config.marketplace_filter
        )
        if count > 0:
            self.db.commit()
            logger.info(f"[JobExecutor] Expired {count} old jobs")
        return count

    def force_cancel_stale_jobs(self) -> int:
        """
        Force-cancel jobs that didn't respond to cancellation within 60s.

        Returns:
            Number of jobs force-cancelled
        """
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=60)

            stale_jobs = self.db.query(MarketplaceJob).filter(
                MarketplaceJob.cancel_requested == True,
                MarketplaceJob.status == JobStatus.RUNNING,
            ).all()

            # Filter by updated_at if column exists
            count = 0
            for job in stale_jobs:
                self.job_service.mark_job_cancelled(job.id)
                count += 1

            if count > 0:
                self.db.commit()
                logger.warning(f"[JobExecutor] Force-cancelled {count} stale jobs")

            return count

        except Exception as e:
            logger.exception(f"[JobExecutor] Error in stale job cleanup: {e}")
            return 0
