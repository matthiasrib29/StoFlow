"""
eBay Sync Workflow for Temporal.

This workflow orchestrates the synchronization of products from eBay Inventory API.
It provides:
- Durable execution (survives crashes)
- Progress tracking via queries
- Cancellation support via signals
- Automatic retries with backoff

Architecture (optimized for large inventories):
1. SYNC: Fetch inventory pages (30 parallel) and upsert directly to DB
2. ENRICH: Fetch offer data (500 batch, 30 concurrent) for price, listing_id, etc.
   - Skip products enriched less than 12 hours ago
3. CLEANUP: Delete products without listing_id (500 batch, 30 concurrent)

Direct DB writes keep history small.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

from temporalio import workflow
from temporalio.common import RetryPolicy

# Import activities (sandbox disabled, direct imports work)
from temporal.activities.ebay_activities import (
    fetch_and_sync_page,
    get_skus_to_delete,
    delete_single_product,
    sync_sold_status,
    get_skus_sold_elsewhere,
    update_job_progress,
    mark_job_completed,
    mark_job_failed,
    enrich_single_product,
    get_skus_to_enrich,
)


@dataclass
class EbaySyncParams:
    """Parameters for eBay sync workflow."""

    user_id: int
    job_id: int
    marketplace_id: str = "EBAY_FR"
    batch_size: int = 100  # Items per page

    # Continue-As-New support (for resuming after history limit)
    start_offset: int = 0  # Resume from this offset
    sync_start_time: Optional[str] = None  # ISO format, set on first run
    accumulated_synced: int = 0  # Count from previous runs
    accumulated_errors: int = 0  # Errors from previous runs


@dataclass
class SyncProgress:
    """Progress tracking for the sync workflow."""

    status: str = "initializing"
    phase: str = "fetch"
    current_count: int = 0
    total_count: int = 0
    label: str = "initialisation..."
    error: Optional[str] = None


@workflow.defn
class EbaySyncWorkflow:
    """
    Temporal workflow for synchronizing eBay products.

    Architecture (optimized for large inventories 10K+ items):
    - Phase 1 (SYNC): Fetch inventory pages (30 parallel) and upsert to DB
    - Phase 2 (ENRICH): Fetch offer data (500 batch, 30 concurrent) per batch
    - Phase 3 (CLEANUP): Delete products without listing_id (500 batch, 30 concurrent)

    Features:
    - Survives crashes and restarts
    - Queryable progress
    - Cancellable via signal
    - Automatic retries with backoff
    - 30 concurrent activities via ThreadPoolExecutor
    """

    def __init__(self):
        self._progress = SyncProgress()
        self._cancelled = False

    @workflow.run
    async def run(self, params: EbaySyncParams) -> dict:
        """
        Execute the eBay sync workflow.

        Args:
            params: Sync parameters (user_id, job_id, marketplace_id, etc.)

        Returns:
            Dict with sync results (count, status, etc.)
        """
        self._progress = SyncProgress(status="running", phase="sync")

        # Initialize sync_start_time on first run
        # IMPORTANT: Use workflow.now() for determinism (datetime.now() breaks replay)
        if params.sync_start_time is None:
            sync_start_time = workflow.now().isoformat()
        else:
            sync_start_time = params.sync_start_time

        # Configure retry policy for activities
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=60),
            backoff_coefficient=2.0,
            maximum_attempts=3,
        )

        # Activity options
        activity_options = {
            "start_to_close_timeout": timedelta(seconds=60),
            "retry_policy": retry_policy,
        }

        try:
            # ═══════════════════════════════════════════════════════════
            # PHASE 1: Fetch pages and sync directly to DB
            # ═══════════════════════════════════════════════════════════
            self._progress.phase = "sync"
            self._progress.label = "synchronisation en cours..."

            offset = params.start_offset
            total_synced = params.accumulated_synced
            total_errors = params.accumulated_errors
            total_items = 0
            pages_processed = 0

            # Initial progress update
            await workflow.execute_activity(
                update_job_progress,
                args=[params.user_id, params.job_id, total_synced, "synchronisation en cours..."],
                **activity_options,
            )

            # Step 1: First call to get total count
            first_result = await workflow.execute_activity(
                fetch_and_sync_page,
                args=[
                    params.user_id,
                    params.marketplace_id,
                    params.batch_size,
                    offset,
                    sync_start_time,
                ],
                **activity_options,
            )

            total_synced += first_result.get("synced", 0)
            total_errors += first_result.get("errors", 0)
            total_items = first_result.get("total", 0)
            pages_processed += 1

            # Update progress after first page
            self._progress.current_count = total_synced
            self._progress.total_count = total_items
            label = f"{total_synced}/{total_items} produits synchronisés"
            self._progress.label = label

            # Step 2: Calculate remaining offsets
            remaining_offsets = []
            next_offset = params.batch_size
            while next_offset < total_items:
                remaining_offsets.append(next_offset)
                next_offset += params.batch_size

            # Step 3: Fetch remaining pages in parallel (30 at a time, uses ThreadPoolExecutor)
            sync_parallel_batch = 30

            for i in range(0, len(remaining_offsets), sync_parallel_batch):
                if self._cancelled:
                    break

                batch_offsets = remaining_offsets[i:i + sync_parallel_batch]

                # Launch parallel activities
                tasks = []
                for page_offset in batch_offsets:
                    task = workflow.execute_activity(
                        fetch_and_sync_page,
                        args=[
                            params.user_id,
                            params.marketplace_id,
                            params.batch_size,
                            page_offset,
                            sync_start_time,
                        ],
                        **activity_options,
                    )
                    tasks.append(task)

                # Wait for all in batch
                results = await asyncio.gather(*tasks)

                # Aggregate results
                for page_result in results:
                    total_synced += page_result.get("synced", 0)
                    total_errors += page_result.get("errors", 0)
                    pages_processed += 1

                # Update progress after each batch
                self._progress.current_count = total_synced
                label = f"{total_synced}/{total_items} produits synchronisés"
                self._progress.label = label

                await workflow.execute_activity(
                    update_job_progress,
                    args=[params.user_id, params.job_id, total_synced, label],
                    **activity_options,
                )

            # Handle cancellation
            if self._cancelled:
                return await self._handle_cancellation(params, activity_options, total_synced)

            # ═══════════════════════════════════════════════════════════
            # PHASE 2: Enrich products with offer data (500 batch, 50 concurrent)
            # ═══════════════════════════════════════════════════════════
            self._progress.phase = "enrich"
            self._progress.label = "enrichissement en cours..."
            total_enriched = 0

            await workflow.execute_activity(
                update_job_progress,
                args=[params.user_id, params.job_id, total_synced, "enrichissement en cours..."],
                **activity_options,
            )

            # Enrich products: 500 activities launched at once, worker handles 30 concurrent (sliding window)
            enrich_batch_size = 500

            while not self._cancelled:
                # Get next batch of SKUs to enrich
                # Always offset=0 because enriched products are excluded by last_enriched_at filter
                skus_to_enrich = await workflow.execute_activity(
                    get_skus_to_enrich,
                    args=[params.user_id, sync_start_time, enrich_batch_size, 0],
                    **activity_options,
                )

                if not skus_to_enrich:
                    break  # No more products to enrich

                # Launch enrichments in parallel
                enrich_tasks = []
                for sku in skus_to_enrich:
                    task = workflow.execute_activity(
                        enrich_single_product,
                        args=[params.user_id, params.marketplace_id, sku],
                        **activity_options,
                    )
                    enrich_tasks.append(task)

                # Wait for all to complete (parallel execution)
                results = await asyncio.gather(*enrich_tasks)

                # Count successes
                batch_enriched = sum(1 for r in results if r.get("success"))
                total_enriched += batch_enriched

                # NOTE: Don't increment offset!
                # Enriched products are automatically excluded by the last_enriched_at filter
                # so we always query from offset=0 to get the next batch of unenriched products

                # Update progress
                label = f"{total_synced} synchronisés, {total_enriched} enrichis..."
                self._progress.label = label

                # Update job progress every batch
                await workflow.execute_activity(
                    update_job_progress,
                    args=[params.user_id, params.job_id, total_synced, label],
                    **activity_options,
                )

            # Handle cancellation after enrich phase
            if self._cancelled:
                return await self._handle_cancellation(params, activity_options, total_synced)

            # ═══════════════════════════════════════════════════════════
            # PHASE 3: Cleanup orphan products (parallel deletion)
            # ═══════════════════════════════════════════════════════════
            self._progress.phase = "cleanup"
            self._progress.label = "nettoyage en cours..."
            total_deleted = 0

            await workflow.execute_activity(
                update_job_progress,
                args=[params.user_id, params.job_id, total_synced, "nettoyage en cours..."],
                **activity_options,
            )

            # Delete products without listing: 500 activities at once, worker handles 30 concurrent
            delete_batch_size = 500

            while not self._cancelled:
                # Get next batch of SKUs to delete
                skus_to_delete = await workflow.execute_activity(
                    get_skus_to_delete,
                    args=[params.user_id, delete_batch_size, 0],
                    **activity_options,
                )

                if not skus_to_delete:
                    break  # No more products to delete

                # Launch deletions in parallel
                delete_tasks = []
                for sku in skus_to_delete:
                    task = workflow.execute_activity(
                        delete_single_product,
                        args=[params.user_id, params.marketplace_id, sku],
                        **activity_options,
                    )
                    delete_tasks.append(task)

                # Wait for all to complete (parallel execution)
                results = await asyncio.gather(*delete_tasks)

                # Count successes
                batch_deleted = sum(1 for r in results if r.get("success"))
                total_deleted += batch_deleted

                # Update progress
                label = f"{total_synced} synchronisés, {total_enriched} enrichis, {total_deleted} supprimés..."
                self._progress.label = label

                await workflow.execute_activity(
                    update_job_progress,
                    args=[params.user_id, params.job_id, total_synced, label],
                    **activity_options,
                )

            deleted_count = total_deleted

            # ═══════════════════════════════════════════════════════════
            # PHASE 4: Sync sold status to Stoflow products
            # ═══════════════════════════════════════════════════════════
            sold_result = await workflow.execute_activity(
                sync_sold_status,
                args=[params.user_id],
                **activity_options,
            )
            sold_updated = sold_result.get("updated_count", 0)

            if sold_updated > 0:
                label = f"{total_synced} synchronisés, {total_enriched} enrichis, {deleted_count} supprimés, {sold_updated} vendus..."
                self._progress.label = label

                await workflow.execute_activity(
                    update_job_progress,
                    args=[params.user_id, params.job_id, total_synced, label],
                    **activity_options,
                )

            # ═══════════════════════════════════════════════════════════
            # PHASE 5: Delete eBay products sold elsewhere (not on eBay)
            # Uses individual activities like Phase 3 for proper retry
            # ═══════════════════════════════════════════════════════════
            self._progress.phase = "sold_elsewhere"
            self._progress.label = "suppression produits vendus ailleurs..."
            total_sold_elsewhere_deleted = 0

            await workflow.execute_activity(
                update_job_progress,
                args=[params.user_id, params.job_id, total_synced, "suppression produits vendus ailleurs..."],
                **activity_options,
            )

            # Delete in batches of 500, same pattern as cleanup phase
            sold_elsewhere_batch_size = 500

            while not self._cancelled:
                # Get next batch of SKUs to delete
                skus_sold_elsewhere = await workflow.execute_activity(
                    get_skus_sold_elsewhere,
                    args=[params.user_id, sold_elsewhere_batch_size],
                    **activity_options,
                )

                if not skus_sold_elsewhere:
                    break  # No more products to delete

                # Launch deletions in parallel (individual activities)
                delete_tasks = []
                for sku in skus_sold_elsewhere:
                    task = workflow.execute_activity(
                        delete_single_product,
                        args=[params.user_id, params.marketplace_id, sku],
                        **activity_options,
                    )
                    delete_tasks.append(task)

                # Wait for all to complete
                results = await asyncio.gather(*delete_tasks)

                # Count successes
                batch_deleted = sum(1 for r in results if r.get("success"))
                total_sold_elsewhere_deleted += batch_deleted

                # Update progress
                label = f"{total_synced} sync, {sold_updated} vendus, {total_sold_elsewhere_deleted} supprimés (vendus ailleurs)..."
                self._progress.label = label

                await workflow.execute_activity(
                    update_job_progress,
                    args=[params.user_id, params.job_id, total_synced, label],
                    **activity_options,
                )

            oos_deleted = total_sold_elsewhere_deleted

            # ═══════════════════════════════════════════════════════════
            # DONE
            # ═══════════════════════════════════════════════════════════
            final_count = total_synced

            # Mark job as completed
            await workflow.execute_activity(
                mark_job_completed,
                args=[params.user_id, params.job_id, final_count],
                **activity_options,
            )

            self._progress.status = "completed"
            self._progress.phase = "done"
            self._progress.current_count = final_count
            final_label = f"{final_count} sync, {total_enriched} enrichis, {sold_updated} vendus, {deleted_count} orphelins supprimés, {oos_deleted} vendus ailleurs supprimés"
            self._progress.label = final_label

            return {
                "status": "completed",
                "final_count": final_count,
                "enriched": total_enriched,
                "sold_updated": sold_updated,
                "sold_elsewhere_deleted": oos_deleted,
                "orphans_deleted": deleted_count,
                "errors": total_errors,
                "total_fetched": total_items,
            }

        except Exception as e:
            self._progress.status = "failed"
            self._progress.error = str(e)

            # Mark job as failed
            try:
                await workflow.execute_activity(
                    mark_job_failed,
                    args=[params.user_id, params.job_id, str(e)],
                    start_to_close_timeout=timedelta(minutes=1),
                )
            except Exception:
                pass  # Best effort

            raise

    async def _handle_cancellation(
        self, params: EbaySyncParams, activity_options: dict, synced_count: int
    ) -> dict:
        """Handle workflow cancellation."""
        self._progress.status = "cancelled"
        await workflow.execute_activity(
            mark_job_failed,
            args=[params.user_id, params.job_id, "Sync cancelled by user"],
            **activity_options,
        )
        return {
            "status": "cancelled",
            "synced_count": synced_count,
            "message": "Sync cancelled by user",
        }

    @workflow.signal
    def cancel_sync(self) -> None:
        """Signal to cancel the sync workflow."""
        self._cancelled = True
        self._progress.status = "cancelling"

    @workflow.query
    def get_progress(self) -> dict:
        """Query current sync progress."""
        return {
            "status": self._progress.status,
            "phase": self._progress.phase,
            "current": self._progress.current_count,
            "total": self._progress.total_count,
            "label": self._progress.label,
            "error": self._progress.error,
        }
