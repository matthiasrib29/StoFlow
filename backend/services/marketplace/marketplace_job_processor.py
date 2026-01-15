"""
Marketplace Job Processor - Unified orchestrator for all marketplaces

Handles job execution for Vinted, eBay, and Etsy with priority management,
retry logic, and marketplace-specific handler dispatch.

Author: Claude
Date: 2026-01-09
"""
import time
from typing import Any, Optional

from sqlalchemy.orm import Session

from models.user.marketplace_job import JobStatus, MarketplaceJob
from services.marketplace.marketplace_job_service import MarketplaceJobService
from services.vinted.jobs import HANDLERS as VINTED_HANDLERS
from services.ebay.jobs import EBAY_HANDLERS
from services.etsy.jobs import ETSY_HANDLERS
from shared.logging_setup import get_logger

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

    async def _execute_job(self, job: MarketplaceJob) -> dict[str, Any]:
        """
        Execute a single job by dispatching to the appropriate handler.

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

        logger.info(
            f"[JobProcessor] Starting job #{job_id} "
            f"(marketplace={marketplace}, action={action_code}, product={job.product_id})"
        )

        # Mark job as running
        self.job_service.start_job(job_id)

        # Check if cancellation was requested before we started
        self.db.refresh(job)
        if job.cancel_requested:
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

        try:
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
                error_msg = result.get("error", "Operation failed")
                return await self._handle_job_failure(
                    job_id, marketplace, full_action_code, error_msg, start_time
                )

        except Exception as e:
            return await self._handle_job_failure(
                job_id, marketplace, full_action_code, str(e), start_time
            )

    async def _handle_job_failure(
        self,
        job_id: int,
        marketplace: str,
        action_code: str,
        error_msg: str,
        start_time: float
    ) -> dict[str, Any]:
        """
        Handle job failure with retry logic.

        Args:
            job_id: The ID of the MarketplaceJob that failed
            marketplace: The marketplace name (vinted, ebay, etsy)
            action_code: Full action code (e.g., "publish_ebay")
            error_msg: Error message
            start_time: Job start timestamp

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

        # Check if we can retry
        updated_job, can_retry = self.job_service.increment_retry(job_id)

        if can_retry:
            # Reset to pending for retry
            updated_job.status = JobStatus.PENDING
            self.db.commit()

            logger.warning(
                f"[JobProcessor] Job #{job_id} failed, will retry "
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
            # Max retries reached, job is now FAILED
            self.job_service.fail_job(job_id, error_msg)

            logger.error(
                f"[JobProcessor] Job #{job_id} failed permanently: {error_msg}"
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
