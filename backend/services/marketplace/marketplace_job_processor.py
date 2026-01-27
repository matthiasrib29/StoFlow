"""
Marketplace Job Processor - Unified orchestrator for all marketplaces

Handles job execution for Vinted, eBay, and Etsy with priority management,
retry logic, and marketplace-specific handler dispatch.

Features (updated 2026-01-27 - Audit):
- Circuit breaker per marketplace (#20)
- Error classification for smart retries (#21)
- Exponential backoff with jitter (#22)

Author: Claude
Date: 2026-01-09
"""
import random
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from models.user.marketplace_job import JobStatus, MarketplaceJob
from services.marketplace.marketplace_job_service import MarketplaceJobService
from services.vinted.jobs import HANDLERS as VINTED_HANDLERS
from services.ebay.jobs import EBAY_HANDLERS
from services.etsy.jobs import ETSY_HANDLERS
from shared.advisory_locks import AdvisoryLockHelper
from shared.circuit_breaker import get_circuit_breaker
from shared.error_classification import is_retryable
from shared.logging import get_logger

logger = get_logger(__name__)

# Global registry (all marketplaces)
ALL_HANDLERS = {
    **VINTED_HANDLERS,
    **EBAY_HANDLERS,
    **ETSY_HANDLERS,
}


class MarketplaceJobProcessor:
    """
    Unified job processor for all marketplaces.

    Replaces VintedJobProcessor with support for Vinted, eBay, and Etsy.

    Usage:
        processor = MarketplaceJobProcessor(db, user_id=1, shop_id=123)
        result = await processor.process_next_job()
    """

    def __init__(
        self,
        db: Session,
        user_id: int,
        shop_id: Optional[int] = None,
        marketplace: Optional[str] = None
    ):
        """
        Initialize the job processor.

        Args:
            db: SQLAlchemy session (user schema)
            user_id: User ID (required for WebSocket communication)
            shop_id: Shop ID (Vinted specific, optional)
            marketplace: Filter jobs by marketplace (optional)
        """
        self.db = db
        self.user_id = user_id
        self.shop_id = shop_id
        self.marketplace = marketplace
        self.job_service = MarketplaceJobService(db)

    async def process_next_job(self) -> Optional[dict[str, Any]]:
        """
        Process the next pending job in the queue.

        Returns:
            dict: Result of job execution, or None if no pending jobs
        """
        # Timeout fallback: force-cancel stale jobs (cooperative pattern - 2026-01-15)
        self._force_cancel_stale_jobs()

        # Expire old jobs
        expired_count = self.job_service.expire_old_jobs(marketplace=self.marketplace)
        if expired_count > 0:
            logger.info(f"[JobProcessor] Expired {expired_count} old jobs")

        # Get next pending job
        job = self.job_service.get_next_pending_job(marketplace=self.marketplace)
        if not job:
            logger.debug("[JobProcessor] No pending jobs")
            return None

        return await self._execute_job(job)

    def _force_cancel_stale_jobs(self) -> int:
        """
        Force-cancel jobs that didn't respond to cancellation within 60s.

        This is a safety net for handlers that don't check cancel_requested
        frequently enough. Jobs with cancel_requested=True and still RUNNING
        after 60s are force-cancelled.

        Returns:
            int: Number of jobs force-cancelled
        """
        try:
            # Find stale jobs: cancel_requested + RUNNING + updated_at > 60s ago
            cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=60)

            stale_jobs = self.db.query(MarketplaceJob).filter(
                MarketplaceJob.cancel_requested == True,
                MarketplaceJob.status == JobStatus.RUNNING,
                MarketplaceJob.updated_at < cutoff_time
            ).all()

            if stale_jobs:
                logger.warning(
                    f"[JobProcessor] Found {len(stale_jobs)} stale jobs "
                    "with unresponsive cancellation - forcing CANCELLED"
                )

                for job in stale_jobs:
                    logger.warning(
                        f"[JobProcessor] Job #{job.id} didn't respond to cancellation "
                        "within 60s - forcing CANCELLED"
                    )
                    self.job_service.mark_job_cancelled(job.id)

                return len(stale_jobs)

            return 0

        except Exception as e:
            logger.exception(f"[JobProcessor] Error in timeout watcher: {e}")
            return 0

    async def _execute_job(self, job: MarketplaceJob) -> dict[str, Any]:
        """
        Execute a single job by dispatching to the appropriate handler.

        Uses advisory locks for work coordination (2026-01-19):
        - Acquires work lock before processing (non-blocking)
        - Releases work lock after completion (success or failure)

        Circuit breaker (Issue #20 - Audit):
        - Checks marketplace circuit breaker before executing
        - Records success/failure for circuit state transitions

        Args:
            job: The MarketplaceJob to execute

        Returns:
            dict: Execution result
        """
        start_time = time.time()
        job_id = job.id
        marketplace = job.marketplace

        # Get action type
        action_type = self.job_service.get_action_type_by_id(job.action_type_id)
        action_code = action_type.code if action_type else "unknown"

        # Build full action code (e.g., "publish_vinted", "publish_ebay")
        full_action_code = f"{action_code}_{marketplace}"

        # Circuit breaker check (Issue #20)
        cb = get_circuit_breaker(marketplace)
        if not cb.can_execute():
            logger.warning(
                f"[JobProcessor] Circuit breaker OPEN for {marketplace}, "
                f"skipping job #{job_id}"
            )
            return {
                "job_id": job_id,
                "marketplace": marketplace,
                "action": action_code,
                "success": False,
                "status": "circuit_breaker_open",
                "reason": f"Circuit breaker open for {marketplace}",
            }

        logger.info(
            f"[JobProcessor] Starting job #{job_id} "
            f"(marketplace={marketplace}, action={action_code}, product={job.product_id})"
        )

        # Acquire work lock (advisory) - should always succeed since we used SKIP LOCKED
        if not AdvisoryLockHelper.try_acquire_work_lock(self.db, job_id):
            logger.warning(f"[JobProcessor] Could not acquire work lock for job #{job_id}")
            return {
                "job_id": job_id,
                "marketplace": marketplace,
                "action": action_code,
                "success": False,
                "status": "skipped",
                "reason": "could_not_acquire_work_lock"
            }

        try:
            # Mark job as running
            self.job_service.start_job(job_id)

            # Check if cancellation was signaled before we started (via advisory lock)
            if AdvisoryLockHelper.is_cancel_signaled(self.db, job_id):
                logger.info(f"[JobProcessor] Job #{job_id} cancelled before execution started")
                self.job_service.mark_job_cancelled(job_id)
                return {
                    "job_id": job_id,
                    "marketplace": marketplace,
                    "action": action_code,
                    "success": False,
                    "status": "cancelled",
                    "reason": "cancelled_before_start"
                }

            # Get handler for this action
            handler_class = ALL_HANDLERS.get(full_action_code)

            if not handler_class:
                raise ValueError(f"Unknown action: {full_action_code}")

            # Create handler instance
            handler = handler_class(
                db=self.db,
                shop_id=self.shop_id,
                job_id=job_id
            )

            # Set user_id for WebSocket communication (Vinted only)
            if marketplace == "vinted":
                handler.user_id = self.user_id

            # Execute the handler
            result = await handler.execute(job)

            # Check if operation succeeded
            if result.get("success", False):
                cb.record_success()
                self.job_service.complete_job(job_id)
                elapsed = time.time() - start_time
                logger.info(
                    f"[JobProcessor] Job #{job_id} completed successfully "
                    f"({elapsed:.1f}s)"
                )
                return {
                    "job_id": job_id,
                    "marketplace": marketplace,
                    "action": action_code,
                    "success": True,
                    "result": result,
                    "duration_ms": int(elapsed * 1000),
                }
            else:
                # Operation returned success=False
                cb.record_failure()
                error_msg = result.get("error", "Operation failed")
                failed_step = result.get("failed_step")
                return await self._handle_job_failure(
                    job_id, marketplace, full_action_code, error_msg, start_time,
                    failed_step=failed_step
                )

        except Exception as e:
            cb.record_failure()
            return await self._handle_job_failure(
                job_id, marketplace, full_action_code, str(e), start_time,
                original_error=e,
            )
        finally:
            # Always release work lock
            AdvisoryLockHelper.release_work_lock(self.db, job_id)

    # Exponential backoff constants (Issue #22)
    BACKOFF_BASE = 1.0       # Base delay in seconds
    BACKOFF_MAX = 300.0      # Max delay: 5 minutes

    async def _handle_job_failure(
        self,
        job_id: int,
        marketplace: str,
        action_code: str,
        error_msg: str,
        start_time: float,
        failed_step: str | None = None,
        original_error: Exception | None = None,
    ) -> dict[str, Any]:
        """
        Handle job failure with smart retry logic.

        Features (Issues #21, #22 - Audit):
        - Skips retry for non-retryable errors (auth, validation)
        - Exponential backoff with jitter between retries

        Args:
            job_id: The ID of the MarketplaceJob that failed
            marketplace: The marketplace name (vinted, ebay, etsy)
            action_code: Full action code (e.g., "publish_ebay")
            error_msg: Error message
            start_time: Job start timestamp
            failed_step: Step where the failure occurred (e.g., 'upload_images')
            original_error: The original exception (for classification)

        Returns:
            dict: Failure result with retry information
        """
        elapsed = time.time() - start_time

        # schema_translate_map survives rollback - no need to restore search_path
        # Just rollback any failed transaction before checking retry
        try:
            self.db.rollback()
        except Exception:
            pass  # Ignore if no transaction active

        # Error classification: skip retry for non-retryable errors (Issue #21)
        if original_error and not is_retryable(original_error):
            self.job_service.fail_job(
                job_id, error_msg, failed_step=failed_step
            )
            step_info = f" at step '{failed_step}'" if failed_step else ""
            logger.error(
                f"[JobProcessor] Job #{job_id} failed permanently "
                f"(non-retryable){step_info}: {error_msg}"
            )
            return {
                "job_id": job_id,
                "marketplace": marketplace,
                "action": action_code,
                "success": False,
                "error": error_msg,
                "will_retry": False,
                "non_retryable": True,
                "duration_ms": int(elapsed * 1000),
            }

        # Check if we can retry
        updated_job, can_retry = self.job_service.increment_retry(job_id)

        if can_retry:
            # Exponential backoff with jitter (Issue #22)
            # delay = min(base * 2^retry_count + jitter, max_delay)
            retry_count = updated_job.retry_count
            delay = min(
                self.BACKOFF_BASE * (2 ** retry_count) + random.uniform(0, self.BACKOFF_BASE),
                self.BACKOFF_MAX,
            )
            next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=delay)
            updated_job.updated_at = next_retry_at

            # Reset to pending for retry
            updated_job.status = JobStatus.PENDING
            self.db.commit()

            logger.warning(
                f"[JobProcessor] Job #{job_id} failed, will retry "
                f"(attempt {retry_count}, backoff {delay:.1f}s): {error_msg}"
            )

            return {
                "job_id": job_id,
                "marketplace": marketplace,
                "action": action_code,
                "success": False,
                "error": error_msg,
                "will_retry": True,
                "retry_count": retry_count,
                "backoff_seconds": round(delay, 1),
                "duration_ms": int(elapsed * 1000),
            }
        else:
            # Max retries reached, job is now FAILED
            self.job_service.fail_job(job_id, error_msg, failed_step=failed_step)

            step_info = f" at step '{failed_step}'" if failed_step else ""
            logger.error(
                f"[JobProcessor] Job #{job_id} failed permanently{step_info}: {error_msg}"
            )

            return {
                "job_id": job_id,
                "marketplace": marketplace,
                "action": action_code,
                "success": False,
                "error": error_msg,
                "will_retry": False,
                "duration_ms": int(elapsed * 1000),
            }
