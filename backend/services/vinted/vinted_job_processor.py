"""
Vinted Job Processor - Orchestrateur d'exécution des jobs

DEPRECATED: This class is deprecated as of 2026-01-09.
Use MarketplaceJobProcessor instead for unified marketplace support.

Ce service est le coeur du système de jobs. Il:
- Récupère les jobs PENDING par priorité
- Dispatch vers le handler approprié
- Gère le cycle de vie des jobs (start, complete, fail)
- Gère les retries automatiques

Business Rules (2025-12-19):
- Un seul job à la fois par utilisateur
- Priorité: 1=CRITICAL, 2=HIGH, 3=NORMAL, 4=LOW
- Max 3 retries avant FAILED
- Expiration après 1 heure

Architecture:
- Chaque action a son propre handler dans services/vinted/jobs/
- Le processor dispatch vers le bon handler via HANDLERS dict

Author: Claude
Date: 2025-12-19
Updated: 2026-01-08 - Added user_id for WebSocket communication
Updated: 2026-01-09 - DEPRECATED in favor of MarketplaceJobProcessor
"""

import time
import warnings
from typing import Any

from sqlalchemy.orm import Session

from models.user.marketplace_job import JobStatus, MarketplaceJob
from services.vinted.vinted_job_service import VintedJobService
from services.vinted.jobs import HANDLERS
from shared.logging_setup import get_logger

logger = get_logger(__name__)

# Deprecation warning
warnings.warn(
    "VintedJobProcessor is deprecated as of 2026-01-09. "
    "Use MarketplaceJobProcessor from services.marketplace.marketplace_job_processor instead. "
    "This class will be removed in February 2026.",
    DeprecationWarning,
    stacklevel=2
)


class VintedJobProcessor:
    """
    Processeur de jobs Vinted.

    Orchestrates job execution with priority management and retry logic.
    Dispatch vers les handlers spécialisés pour chaque type d'action.

    Usage:
        processor = VintedJobProcessor(db, user_id=1, shop_id=123)
        result = await processor.process_next_job()

        # Or process all pending jobs:
        results = await processor.process_all_pending_jobs()
    """

    def __init__(self, db: Session, user_id: int, shop_id: int | None = None):
        """
        Initialize the job processor.

        Args:
            db: SQLAlchemy session (user schema)
            user_id: User ID (required for WebSocket communication)
            shop_id: Vinted shop ID (required for sync operations)
        """
        self.db = db
        self.user_id = user_id
        self.shop_id = shop_id
        self.job_service = VintedJobService(db)

    # =========================================================================
    # MAIN PROCESSING METHODS
    # =========================================================================

    async def process_next_job(self) -> dict[str, Any] | None:
        """
        Process the next pending job in the queue.

        Gets the highest priority pending job and executes it.

        Returns:
            dict: Result of job execution, or None if no pending jobs
        """
        # First, expire old jobs
        expired_count = self.job_service.expire_old_jobs()
        if expired_count > 0:
            logger.info(f"[JobProcessor] Expired {expired_count} old jobs")

        # Get next pending job
        job = self.job_service.get_next_pending_job()
        if not job:
            logger.debug("[JobProcessor] No pending jobs")
            return None

        return await self._execute_job(job)

    async def process_all_pending_jobs(
        self,
        max_jobs: int = 100,
        stop_on_error: bool = False
    ) -> list[dict[str, Any]]:
        """
        Process all pending jobs in priority order.

        Args:
            max_jobs: Maximum number of jobs to process
            stop_on_error: If True, stop processing on first error

        Returns:
            list: List of job results
        """
        results = []
        processed = 0

        while processed < max_jobs:
            result = await self.process_next_job()
            if result is None:
                break

            results.append(result)
            processed += 1

            if stop_on_error and not result.get("success", False):
                logger.warning("[JobProcessor] Stopping on error")
                break

        logger.info(f"[JobProcessor] Processed {processed} jobs")
        return results

    async def process_batch(self, batch_id: str) -> dict[str, Any]:
        """
        Process all jobs in a specific batch.

        Args:
            batch_id: The batch ID to process

        Returns:
            dict: Batch processing summary
        """
        jobs = self.job_service.get_batch_jobs(batch_id)
        if not jobs:
            return {"batch_id": batch_id, "error": "Batch not found"}

        results = []
        success_count = 0
        failed_count = 0

        for job in jobs:
            if job.status != JobStatus.PENDING:
                continue

            result = await self._execute_job(job)
            results.append(result)

            if result.get("success"):
                success_count += 1
            else:
                failed_count += 1

        return {
            "batch_id": batch_id,
            "total": len(jobs),
            "processed": len(results),
            "success_count": success_count,
            "failed_count": failed_count,
            "results": results,
        }

    # =========================================================================
    # JOB EXECUTION
    # =========================================================================

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

        # Get action type
        action_type = self.job_service.get_action_type_by_id(job.action_type_id)
        action_code = action_type.code if action_type else "unknown"

        logger.info(
            f"[JobProcessor] Starting job #{job_id} "
            f"(action={action_code}, product={job.product_id})"
        )

        # Mark job as running
        self.job_service.start_job(job_id)

        try:
            # Get handler for this action
            # Support eBay handlers (action codes ending with _ebay)
            if action_code.endswith("_ebay"):
                from services.ebay.jobs import EBAY_HANDLERS
                handler_class = EBAY_HANDLERS.get(action_code)
            else:
                handler_class = HANDLERS.get(action_code)

            if not handler_class:
                raise ValueError(f"Unknown action code: {action_code}")

            # Create handler instance
            handler = handler_class(
                db=self.db,
                shop_id=self.shop_id,
                job_id=job_id
            )

            # Set user_id for WebSocket communication
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
                    "action": action_code,
                    "success": True,
                    "result": result,
                    "duration_ms": int(elapsed * 1000),
                }
            else:
                # Operation returned success=False
                error_msg = result.get("error", "Operation failed")
                return await self._handle_job_failure(
                    job, action_code, error_msg, start_time
                )

        except Exception as e:
            return await self._handle_job_failure(
                job, action_code, str(e), start_time
            )

    async def _handle_job_failure(
        self,
        job: MarketplaceJob,
        action_code: str,
        error_msg: str,
        start_time: float
    ) -> dict[str, Any]:
        """
        Handle job failure with retry logic.

        Args:
            job: The failed job
            action_code: The action type code
            error_msg: Error message
            start_time: When job started

        Returns:
            dict: Failure result
        """
        elapsed = time.time() - start_time

        # Check if we can retry
        updated_job, can_retry = self.job_service.increment_retry(job.id)

        if can_retry:
            # Reset to pending for retry
            updated_job.status = JobStatus.PENDING
            self.db.commit()

            logger.warning(
                f"[JobProcessor] Job #{job.id} failed, will retry "
                f"(attempt {updated_job.retry_count}): {error_msg}"
            )

            return {
                "job_id": job.id,
                "action": action_code,
                "success": False,
                "error": error_msg,
                "will_retry": True,
                "retry_count": updated_job.retry_count,
                "duration_ms": int(elapsed * 1000),
            }
        else:
            # Max retries reached, job is now FAILED
            self.job_service.fail_job(job.id, error_msg)

            logger.error(
                f"[JobProcessor] Job #{job.id} failed permanently: {error_msg}"
            )

            return {
                "job_id": job.id,
                "action": action_code,
                "success": False,
                "error": error_msg,
                "will_retry": False,
                "duration_ms": int(elapsed * 1000),
            }

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def get_queue_status(self) -> dict[str, Any]:
        """
        Get current queue status.

        Returns:
            dict: Queue statistics
        """
        pending_jobs = self.job_service.get_pending_jobs(limit=100)
        interrupted_jobs = self.job_service.get_interrupted_jobs()

        # Group by action type
        by_action = {}
        for job in pending_jobs:
            action_type = self.job_service.get_action_type_by_id(job.action_type_id)
            code = action_type.code if action_type else "unknown"
            by_action[code] = by_action.get(code, 0) + 1

        return {
            "pending_count": len(pending_jobs),
            "interrupted_count": len(interrupted_jobs),
            "by_action": by_action,
            "next_job": {
                "id": pending_jobs[0].id,
                "action": self.job_service.get_action_type_by_id(
                    pending_jobs[0].action_type_id
                ).code if pending_jobs else None,
                "priority": pending_jobs[0].priority,
            } if pending_jobs else None,
        }
