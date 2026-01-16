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

        This method implements a priority queue pattern where jobs are selected
        based on priority (1=highest) and age (oldest first). It handles:
        1. Expiration of old jobs (pending > 1 hour)
        2. Job selection from queue
        3. Dispatching to appropriate handler

        Returns:
            dict: Result of job execution with success status, or None if queue is empty
                Example: {"success": True, "job_id": 123, "duration_ms": 5000}
        """
        # Clean up expired jobs before processing
        # This prevents stale jobs from clogging the queue
        # Expiration time: 1 hour from creation (configurable in job_service)
        expired_count = self.job_service.expire_old_jobs(marketplace=self.marketplace)
        if expired_count > 0:
            logger.info(f"[JobProcessor] Expired {expired_count} old jobs")

        # Get highest priority pending job
        # Priority order: 1 (CRITICAL) > 2 (HIGH) > 3 (NORMAL) > 4 (LOW)
        # Within same priority: FIFO (oldest first)
        job = self.job_service.get_next_pending_job(marketplace=self.marketplace)
        if not job:
            logger.debug("[JobProcessor] No pending jobs")
            return None

        return await self._execute_job(job)

    async def _execute_job(self, job: MarketplaceJob) -> dict[str, Any]:
        """
        Execute a single job by dispatching to the appropriate handler.

        This is the main orchestration logic that:
        1. Determines which handler to use (factory pattern)
        2. Instantiates the handler with correct parameters
        3. Executes the handler (which creates and executes tasks)
        4. Handles success/failure with retry logic

        Handler Selection:
        - Uses global registry ALL_HANDLERS
        - Key format: "{action_code}_{marketplace}" (e.g., "publish_vinted")
        - Raises ValueError if handler not found

        Args:
            job: The MarketplaceJob to execute

        Returns:
            dict: Execution result with keys:
                - success (bool): Whether job succeeded
                - job_id (int): Job ID
                - marketplace (str): Marketplace name
                - action (str): Action code
                - result (dict): Handler-specific result data
                - duration_ms (int): Execution duration in milliseconds
                - will_retry (bool): Only present on failure if retry available
                - retry_count (int): Only present on failure with retry
        """
        start_time = time.time()
        job_id = job.id
        marketplace = job.marketplace

        # Load action type from public.marketplace_action_types table
        # This is cached in MarketplaceJobService for performance
        action_type = self.job_service.get_action_type_by_id(job.action_type_id)
        action_code = action_type.code if action_type else "unknown"

        # Build full action code for handler lookup
        # Format: "{action_code}_{marketplace}"
        # Examples: "publish_vinted", "update_ebay", "sync_etsy"
        full_action_code = f"{action_code}_{marketplace}"

        logger.info(
            f"[JobProcessor] Starting job #{job_id} "
            f"(marketplace={marketplace}, action={action_code}, product={job.product_id})"
        )

        # Mark job as running (updates status and started_at timestamp)
        # Uses flush() instead of commit() to preserve schema context
        self.job_service.start_job(job_id)

        try:
            # Handler factory pattern: Look up handler class by action code
            # ALL_HANDLERS is a global registry combining:
            # - VINTED_HANDLERS (WebSocket-based)
            # - EBAY_HANDLERS (Direct HTTP OAuth 2.0)
            # - ETSY_HANDLERS (Direct HTTP OAuth 2.0)
            handler_class = ALL_HANDLERS.get(full_action_code)

            if not handler_class:
                raise ValueError(f"Unknown action: {full_action_code}")

            # Instantiate handler with dependencies
            # All handlers inherit from BaseMarketplaceHandler
            handler = handler_class(
                db=self.db,
                shop_id=self.shop_id,  # Vinted shop ID (optional, can be None)
                job_id=job_id
            )

            # Set user_id for WebSocket communication (Vinted only)
            # Required for PluginWebSocketHelper to identify WebSocket connection
            # Not needed for eBay/Etsy (direct HTTP with OAuth tokens)
            if marketplace == "vinted":
                handler.user_id = self.user_id

            # Execute the handler
            # Handler is responsible for:
            # 1. Creating MarketplaceTasks
            # 2. Executing tasks (via plugin or direct HTTP)
            # 3. Handling idempotence checks
            # 4. Returning result dict
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

        This method implements intelligent retry behavior:
        1. Rollback failed transaction (database cleanup)
        2. Increment retry counter
        3. Check if max retries reached
        4. If retry available: Reset to PENDING, return to queue
        5. If max retries exceeded: Mark as FAILED, update parent batch

        Retry Count:
        - Default max_retries: 3 (configurable per action type)
        - retry_count starts at 0
        - After 3 failures: retry_count=3, status=FAILED

        Schema Context Preservation:
        - SQLAlchemy schema_translate_map survives rollback
        - No need to reset search_path after rollback
        - Schema context remains user_X

        Args:
            job_id: The ID of the MarketplaceJob that failed
            marketplace: The marketplace name (vinted, ebay, etsy)
            action_code: Full action code (e.g., "publish_ebay")
            error_msg: Error message from handler or exception
            start_time: Job start timestamp (for duration calculation)

        Returns:
            dict: Failure result with keys:
                - success: Always False
                - job_id: Job ID
                - marketplace: Marketplace name
                - action: Action code
                - error: Error message
                - will_retry: True if retry available, False if max retries reached
                - retry_count: Current retry count (only if will_retry=True)
                - duration_ms: Execution duration in milliseconds
        """
        elapsed = time.time() - start_time

        # Rollback any failed transaction
        # This is critical to prevent "current transaction is aborted" errors
        # schema_translate_map survives rollback - no need to restore search_path
        try:
            self.db.rollback()
        except Exception:
            pass  # Ignore if no transaction active

        # Increment retry count and check if we can retry
        # Returns: (updated_job, can_retry)
        # can_retry = True if retry_count < max_retries
        updated_job, can_retry = self.job_service.increment_retry(job_id)

        if can_retry:
            # Reset to pending for retry
            # Job will be picked up again by process_next_job()
            # Tasks with status='success' will be skipped (idempotence)
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
            # Max retries reached, mark job as permanently FAILED
            # This also updates parent BatchJob progress if applicable
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
