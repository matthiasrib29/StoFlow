"""
Vinted Sync Workflow for Temporal.

This workflow orchestrates the synchronization of products from Vinted.
It provides:
- Durable execution (survives crashes)
- Progress tracking via queries
- Cancellation support via signals
- Automatic retries with backoff

Architecture (optimized for DataDome protection):
1. SYNC: Fetch wardrobe pages SEQUENTIALLY and upsert to DB
2. ENRICH: Fetch item_upload data in small batches (15) with pauses (20-30s)

Key differences from eBay:
- Sequential page fetching (not parallel) due to DataDome
- Mark as "sold" instead of delete for missing products
- Smaller enrichment batches with longer pauses
- Only 2 phases (sync, enrich) vs 3 for eBay

Author: Claude
Date: 2026-01-22
"""

import asyncio
import random
from dataclasses import dataclass
from datetime import timedelta
from typing import Optional

from temporalio import workflow
from temporalio.common import RetryPolicy

# Import activities (sandbox disabled, direct imports work)
from temporal.activities.vinted_activities import (
    fetch_and_sync_page,
    get_vinted_ids_to_enrich,
    enrich_single_product,
    update_job_progress,
    mark_job_completed,
    mark_job_failed,
)


@dataclass
class VintedSyncParams:
    """Parameters for Vinted sync workflow."""

    user_id: int
    job_id: int
    shop_id: int  # Vinted shop ID (vinted_user_id)

    # Continue-As-New support (for resuming after history limit)
    start_offset: int = 0  # Resume from this page
    sync_start_time: Optional[str] = None  # ISO format, set on first run
    accumulated_synced: int = 0  # Count from previous runs
    accumulated_errors: int = 0  # Errors from previous runs


@dataclass
class VintedSyncProgress:
    """Progress tracking for the sync workflow."""

    status: str = "initializing"  # initializing, running, completed, failed, cancelled
    phase: str = "sync"  # sync, enrich
    current_count: int = 0
    total_count: int = 0
    label: str = "initialisation..."
    error: Optional[str] = None


@workflow.defn
class VintedSyncWorkflow:
    """
    Temporal workflow for synchronizing Vinted products.

    Architecture (optimized for DataDome protection):
    - Phase 1 (SYNC): Fetch wardrobe pages SEQUENTIALLY and upsert to DB
    - Phase 2 (ENRICH): Fetch item_upload data in small batches with pauses

    Features:
    - Survives crashes and restarts
    - Queryable progress
    - Cancellable via signal
    - Automatic retries with backoff
    - Sequential fetching to avoid DataDome blocks
    """

    def __init__(self):
        self._progress = VintedSyncProgress()
        self._cancelled = False

    @workflow.run
    async def run(self, params: VintedSyncParams) -> dict:
        """
        Execute the Vinted sync workflow.

        Args:
            params: Sync parameters (user_id, job_id, shop_id, etc.)

        Returns:
            Dict with sync results (count, status, etc.)
        """
        self._progress = VintedSyncProgress(status="running", phase="sync")

        # Initialize sync_start_time on first run
        # IMPORTANT: Use workflow.now() for determinism (datetime.now() breaks replay)
        if params.sync_start_time is None:
            sync_start_time = workflow.now().isoformat()
        else:
            sync_start_time = params.sync_start_time

        # Configure retry policy for activities
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=2),
            maximum_interval=timedelta(seconds=120),
            backoff_coefficient=2.0,
            maximum_attempts=3,
        )

        # Activity options
        activity_options = {
            "start_to_close_timeout": timedelta(minutes=10),
            "retry_policy": retry_policy,
        }

        try:
            # ═══════════════════════════════════════════════════════════
            # PHASE 1: Fetch pages SEQUENTIALLY and sync to DB
            # ═══════════════════════════════════════════════════════════
            self._progress.phase = "sync"
            self._progress.label = "synchronisation en cours..."

            page = params.start_offset + 1  # Pages are 1-indexed
            total_synced = params.accumulated_synced
            total_errors = params.accumulated_errors

            # Initial progress update
            await workflow.execute_activity(
                update_job_progress,
                args=[params.user_id, params.job_id, total_synced, "synchronisation en cours..."],
                **activity_options,
            )

            # Fetch pages sequentially (DataDome protection)
            while not self._cancelled:
                result = await workflow.execute_activity(
                    fetch_and_sync_page,
                    args=[
                        params.user_id,
                        params.shop_id,
                        page,
                        sync_start_time,
                    ],
                    **activity_options,
                )

                total_synced += result.get("synced", 0)
                total_errors += result.get("errors", 0)
                total_pages = result.get("total_pages", 1)

                # Update progress
                self._progress.current_count = total_synced
                self._progress.total_count = total_synced  # We don't know total in advance
                label = f"{total_synced} produits synchronisés (page {page}/{total_pages})"
                self._progress.label = label

                await workflow.execute_activity(
                    update_job_progress,
                    args=[params.user_id, params.job_id, total_synced, label],
                    **activity_options,
                )

                # Check if more pages
                if page >= total_pages:
                    break

                page += 1

            # Handle cancellation
            if self._cancelled:
                return await self._handle_cancellation(params, activity_options, total_synced)

            # NOTE: Phase 1.5 (mark_missing_as_sold) has been removed.
            # Products are only marked as "sold" when Vinted API explicitly
            # returns is_closed=true (handled in fetch_and_sync_page via map_api_status).
            # This avoids false positives from incomplete syncs.

            # ═══════════════════════════════════════════════════════════
            # PHASE 2: Enrich products (sequential, batch 15, pause 20-30s)
            # ═══════════════════════════════════════════════════════════
            self._progress.phase = "enrich"
            self._progress.label = "enrichissement en cours..."
            total_enriched = 0
            total_enrich_errors = 0

            await workflow.execute_activity(
                update_job_progress,
                args=[params.user_id, params.job_id, total_synced, "enrichissement en cours..."],
                **activity_options,
            )

            # Enrich products sequentially in batches
            # IMPORTANT: Always use offset=0 because enriched products exit the filter
            enrich_batch_size = 15
            batch_count = 0

            while not self._cancelled:
                # Get next batch (always offset=0 since enriched products have description now)
                vinted_ids_to_enrich = await workflow.execute_activity(
                    get_vinted_ids_to_enrich,
                    args=[params.user_id, sync_start_time, enrich_batch_size, 0],
                    **activity_options,
                )

                if not vinted_ids_to_enrich:
                    break  # No more products to enrich

                # Enrich products SEQUENTIALLY (no parallel - DataDome protection)
                for vinted_id in vinted_ids_to_enrich:
                    if self._cancelled:
                        break

                    result = await workflow.execute_activity(
                        enrich_single_product,
                        args=[params.user_id, vinted_id],
                        **activity_options,
                    )

                    if result.get("success"):
                        total_enriched += 1
                    else:
                        total_enrich_errors += 1
                        # Stop on critical errors
                        error = result.get("error", "")
                        if error in ("unauthorized", "disconnected"):
                            self._progress.error = f"Enrichissement arrêté: {error}"
                            break

                # Update progress after each batch
                label = f"{total_synced} synchronisés, {total_enriched} enrichis..."
                self._progress.label = label
                self._progress.current_count = total_synced + total_enriched

                await workflow.execute_activity(
                    update_job_progress,
                    args=[params.user_id, params.job_id, total_synced, label],
                    **activity_options,
                )

                batch_count += 1

                # Pause between batches (20-30s) only if more products might exist
                if len(vinted_ids_to_enrich) == enrich_batch_size:
                    pause_seconds = 20 + (workflow.random().random() * 10)
                    await asyncio.sleep(pause_seconds)

            # Handle cancellation after enrich phase
            if self._cancelled:
                return await self._handle_cancellation(params, activity_options, total_synced)

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
            final_label = f"{final_count} synchronisés, {total_enriched} enrichis"
            self._progress.label = final_label

            return {
                "status": "completed",
                "final_count": final_count,
                "enriched": total_enriched,
                "errors": total_errors,
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
        self, params: VintedSyncParams, activity_options: dict, synced_count: int
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
