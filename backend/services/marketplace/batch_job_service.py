"""
Batch Job Service

Manages batch operations across marketplaces (Vinted, eBay, Etsy).
Groups multiple MarketplaceJobs into a single BatchJob for simplified UI tracking.

Business Rules (2026-01-07):
- 1 BatchJob = N MarketplaceJobs (1 per product)
- BatchJob provides summary view (completed/total counts)
- Auto-updates progress when child jobs complete
- Supports batch cancellation

Author: Claude
Date: 2026-01-07
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from models.user.batch_job import BatchJob, BatchJobStatus
from models.user.marketplace_job import JobStatus, MarketplaceJob
# MarketplaceTask removed (2026-01-09): WebSocket architecture, no granular tasks in DB
from models.vinted.vinted_action_type import VintedActionType
from shared.logging import get_logger

logger = get_logger(__name__)


class BatchJobService:
    """
    Service for managing batch job operations.

    Orchestrates batch operations by creating a parent BatchJob
    with multiple child MarketplaceJobs.
    """

    def __init__(self, db: Session):
        self.db = db
        self._action_types_cache: dict[tuple[str, str], Any] = {}

    # =========================================================================
    # ACTION TYPES
    # =========================================================================

    def get_action_type(
        self, marketplace: str, action_code: str
    ) -> VintedActionType | None:
        """
        Get action type for a marketplace.

        Args:
            marketplace: Marketplace identifier (vinted, ebay, etsy)
            action_code: Action code (publish, update, delete, link_product, sync)

        Returns:
            Action type object or None

        Note:
            Currently only supports Vinted action types.
            eBay/Etsy action types will be added when those handlers are implemented.
        """
        cache_key = (marketplace, action_code)

        if cache_key not in self._action_types_cache:
            # For now, only Vinted action types exist
            if marketplace == "vinted":
                action_type = (
                    self.db.query(VintedActionType)
                    .filter(VintedActionType.code == action_code)
                    .first()
                )
                if action_type:
                    self._action_types_cache[cache_key] = action_type
            else:
                # eBay and Etsy action types will be added later
                logger.warning(
                    f"Action types not yet implemented for marketplace: {marketplace}"
                )
                return None

        return self._action_types_cache.get(cache_key)

    # =========================================================================
    # BATCH JOB CREATION
    # =========================================================================

    def create_batch_job(
        self,
        marketplace: str,
        action_code: str,
        product_ids: list[int],
        priority: int | None = None,
        created_by_user_id: int | None = None,
    ) -> BatchJob:
        """
        Create a batch job with N child MarketplaceJobs.

        Args:
            marketplace: Target marketplace (vinted, ebay, etsy)
            action_code: Action to perform (publish, update, delete, link_product, sync)
            product_ids: List of product IDs to process
            priority: Job priority (1=CRITICAL, 2=HIGH, 3=NORMAL, 4=LOW)
            created_by_user_id: User ID creating the batch (for audit)

        Returns:
            Created BatchJob instance with child jobs

        Raises:
            ValueError: If action_code is invalid for the marketplace
            ValueError: If product_ids is empty
        """
        if not product_ids:
            raise ValueError("product_ids cannot be empty")

        # Get action type
        action_type = self.get_action_type(marketplace, action_code)
        if not action_type:
            raise ValueError(
                f"Invalid action_code '{action_code}' for marketplace '{marketplace}'"
            )

        # Use action type's default priority if not specified
        effective_priority = priority if priority is not None else action_type.priority

        # Generate unique batch_id
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        batch_id = f"{action_code}_{timestamp}_{uuid.uuid4().hex[:8]}"

        logger.info(
            f"Creating batch job: marketplace={marketplace}, action={action_code}, "
            f"products={len(product_ids)}, priority={effective_priority}"
        )

        # 1. Create BatchJob parent
        batch = BatchJob(
            batch_id=batch_id,
            marketplace=marketplace,
            action_code=action_code,
            total_count=len(product_ids),
            completed_count=0,
            failed_count=0,
            cancelled_count=0,
            status=BatchJobStatus.PENDING,
            priority=effective_priority,
            created_by_user_id=created_by_user_id,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(batch)
        self.db.flush()  # Get batch.id

        # 2. Create child MarketplaceJobs
        for product_id in product_ids:
            job = MarketplaceJob(
                batch_job_id=batch.id,
                marketplace=marketplace,
                action_type_id=action_type.id,
                product_id=product_id,
                status=JobStatus.PENDING,
                priority=effective_priority,
                created_at=datetime.now(timezone.utc),
            )
            self.db.add(job)

        self.db.commit()

        logger.info(
            f"Batch job created: batch_id={batch_id}, id={batch.id}, "
            f"child_jobs={len(product_ids)}"
        )

        return batch

    # =========================================================================
    # BATCH PROGRESS TRACKING
    # =========================================================================

    def update_batch_progress(self, batch_job_id: int) -> BatchJob:
        """
        Recalculate batch progress from child jobs.

        Called after each child MarketplaceJob completes/fails.

        Args:
            batch_job_id: BatchJob primary key

        Returns:
            Updated BatchJob with recalculated counts

        Raises:
            ValueError: If batch_job_id not found
        """
        batch = self.db.query(BatchJob).filter(BatchJob.id == batch_job_id).first()
        if not batch:
            raise ValueError(f"BatchJob with id={batch_job_id} not found")

        # Count job statuses
        jobs = (
            self.db.query(MarketplaceJob)
            .filter(MarketplaceJob.batch_job_id == batch_job_id)
            .all()
        )

        completed_count = sum(1 for j in jobs if j.status == JobStatus.COMPLETED)
        failed_count = sum(1 for j in jobs if j.status == JobStatus.FAILED)
        cancelled_count = sum(1 for j in jobs if j.status == JobStatus.CANCELLED)

        # Update counts
        batch.completed_count = completed_count
        batch.failed_count = failed_count
        batch.cancelled_count = cancelled_count

        # Update global status (but preserve CANCELLED status if already set)
        total = batch.total_count

        # Don't override CANCELLED status
        if batch.status == BatchJobStatus.CANCELLED:
            # Keep cancelled status, just update completed_at if not set
            if not batch.completed_at:
                batch.completed_at = datetime.now(timezone.utc)
        elif completed_count == total:
            batch.status = BatchJobStatus.COMPLETED
            batch.completed_at = datetime.now(timezone.utc)
        elif failed_count == total:
            batch.status = BatchJobStatus.FAILED
            batch.completed_at = datetime.now(timezone.utc)
        elif completed_count + failed_count + cancelled_count == total:
            # All jobs finished (mixed results)
            if failed_count > 0:
                batch.status = BatchJobStatus.PARTIALLY_FAILED
            else:
                batch.status = BatchJobStatus.COMPLETED
            batch.completed_at = datetime.now(timezone.utc)
        elif completed_count > 0 or failed_count > 0:
            # At least one job finished, batch is running
            if batch.status == BatchJobStatus.PENDING:
                batch.status = BatchJobStatus.RUNNING
                batch.started_at = datetime.now(timezone.utc)

        self.db.commit()

        logger.debug(
            f"Batch progress updated: batch_id={batch.batch_id}, "
            f"status={batch.status.value}, progress={batch.progress_percent:.1f}%"
        )

        return batch

    def get_batch_summary(self, batch_id: str) -> dict[str, Any] | None:
        """
        Get batch summary by batch_id string.

        Args:
            batch_id: Batch identifier (UUID-like string)

        Returns:
            Dictionary with batch summary or None if not found
        """
        batch = (
            self.db.query(BatchJob)
            .options(selectinload(BatchJob.jobs))
            .filter(BatchJob.batch_id == batch_id)
            .first()
        )

        if not batch:
            return None

        return {
            "id": batch.id,
            "batch_id": batch.batch_id,
            "marketplace": batch.marketplace,
            "action_code": batch.action_code,
            "status": batch.status.value,
            "priority": batch.priority,
            "total_count": batch.total_count,
            "completed_count": batch.completed_count,
            "failed_count": batch.failed_count,
            "cancelled_count": batch.cancelled_count,
            "pending_count": batch.pending_count,
            "progress_percent": batch.progress_percent,
            "created_at": batch.created_at.isoformat() if batch.created_at else None,
            "started_at": batch.started_at.isoformat() if batch.started_at else None,
            "completed_at": (
                batch.completed_at.isoformat() if batch.completed_at else None
            ),
        }

    def get_batch_by_id(self, batch_job_id: int) -> BatchJob | None:
        """
        Get BatchJob by primary key.

        Args:
            batch_job_id: BatchJob primary key

        Returns:
            BatchJob or None
        """
        return self.db.query(BatchJob).filter(BatchJob.id == batch_job_id).first()

    def list_active_batches(
        self, marketplace: str | None = None, limit: int = 50
    ) -> list[BatchJob]:
        """
        List active batch jobs (pending or running).

        Args:
            marketplace: Filter by marketplace (optional)
            limit: Maximum number of results

        Returns:
            List of active BatchJob instances
        """
        query = self.db.query(BatchJob).filter(
            BatchJob.status.in_([BatchJobStatus.PENDING, BatchJobStatus.RUNNING])
        )

        if marketplace:
            query = query.filter(BatchJob.marketplace == marketplace)

        query = query.order_by(BatchJob.priority.asc(), BatchJob.created_at.desc())

        return query.limit(limit).all()

    # =========================================================================
    # BATCH CANCELLATION
    # =========================================================================

    def cancel_batch(self, batch_job_id: int) -> int:
        """
        Cancel all pending/running jobs in a batch.

        Args:
            batch_job_id: BatchJob primary key

        Returns:
            Number of jobs cancelled

        Raises:
            ValueError: If batch_job_id not found
        """
        batch = self.db.query(BatchJob).filter(BatchJob.id == batch_job_id).first()
        if not batch:
            raise ValueError(f"BatchJob with id={batch_job_id} not found")

        logger.info(f"Cancelling batch: batch_id={batch.batch_id}, id={batch.id}")

        cancelled_count = 0

        # Cancel all pending/running child jobs
        jobs = (
            self.db.query(MarketplaceJob)
            # .options(selectinload(MarketplaceJob.tasks))  # Removed: no tasks relationship (WebSocket architecture)
            .filter(MarketplaceJob.batch_job_id == batch_job_id)
            .filter(
                MarketplaceJob.status.in_([JobStatus.PENDING, JobStatus.RUNNING])
            )
            .all()
        )

        for job in jobs:
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.now(timezone.utc)
            # Tasks cancellation removed: WebSocket handles real-time cancellation
            # No granular tasks in DB (Option A: simple architecture)

            cancelled_count += 1

        # Update batch status
        batch.status = BatchJobStatus.CANCELLED
        batch.completed_at = datetime.now(timezone.utc)

        # Recalculate counts
        self.update_batch_progress(batch_job_id)

        self.db.commit()

        logger.info(
            f"Batch cancelled: batch_id={batch.batch_id}, jobs_cancelled={cancelled_count}"
        )

        return cancelled_count
