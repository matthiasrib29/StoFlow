"""
Vinted Sync Workflow for Temporal.

This workflow orchestrates the synchronization of products from Vinted.
It provides:
- Durable execution (survives crashes)
- Progress tracking via queries
- Cancellation support via signals
- Pause/Resume support via signals
- Automatic retries with backoff
- Automatic reconnection waiting on plugin disconnect

Architecture (optimized for DataDome protection):
1. SYNC: Fetch wardrobe pages SEQUENTIALLY and upsert to DB
2. ENRICH: Fetch item_upload data sequentially (rate limiter handles delays)
3. SOLD_SYNC: Mark StoFlow products as SOLD when Vinted product is closed

Key differences from eBay:
- Sequential page fetching (not parallel) due to DataDome
- Mark as "sold" instead of delete for missing products
- Rate limiter with random delays between all requests
- 3 phases (sync, enrich, sold_sync)

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
    check_plugin_connection,
    mark_job_paused,
    sync_sold_status,
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

    status: str = "initializing"  # initializing, running, completed, failed, cancelled, paused, waiting_reconnection
    phase: str = "sync"  # sync, enrich
    current_count: int = 0
    total_count: int = 0
    label: str = "initialisation..."
    error: Optional[str] = None
    # Resilience fields
    paused_at: Optional[str] = None
    pause_reason: Optional[str] = None
    reconnection_attempts: int = 0


@workflow.defn
class VintedSyncWorkflow:
    """
    Temporal workflow for synchronizing Vinted products.

    Architecture (optimized for DataDome protection):
    - Phase 1 (SYNC): Fetch wardrobe pages SEQUENTIALLY and upsert to DB
    - Phase 2 (ENRICH): Fetch item_upload data sequentially
    - Phase 3 (SOLD_SYNC): Mark StoFlow products as SOLD when Vinted closed

    Features:
    - Survives crashes and restarts
    - Queryable progress
    - Cancellable via signal
    - Pause/Resume via signals
    - Automatic retries with backoff
    - Rate limiter with random delays (anti-bot protection)
    """

    def __init__(self):
        self._progress = VintedSyncProgress()
        self._cancelled = False
        # Resilience flags
        self._paused = False
        self._resume_requested = False
        self._waiting_for_reconnection = False

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
                # Check for pause signal
                if self._paused:
                    if not await self._wait_while_paused(params, activity_options):
                        return await self._handle_cancellation(params, activity_options, total_synced)
                    # Restore running status after resume
                    await workflow.execute_activity(
                        update_job_progress,
                        args=[params.user_id, params.job_id, total_synced, "synchronisation en cours..."],
                        **activity_options,
                    )
                    continue

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

                # Check for errors that require waiting/retry
                error_type = result.get("error")
                if error_type:
                    # Errors that indicate plugin/connection issue - wait for reconnection
                    if error_type in ("disconnected", "timeout"):
                        workflow.logger.warning(f"Plugin connection issue during sync ({error_type}), waiting for reconnection")
                        if await self._wait_for_reconnection(params, activity_options):
                            await workflow.execute_activity(
                                update_job_progress,
                                args=[params.user_id, params.job_id, total_synced, "reprise de la synchronisation..."],
                                **activity_options,
                            )
                            continue
                        else:
                            return {
                                "status": "failed",
                                "error": "disconnected_timeout",
                                "synced_count": total_synced,
                                "message": "Plugin disconnected and reconnection timeout reached",
                            }

                    # 401 Unauthorized / 403 Forbidden - STOP immediately (no retry)
                    if error_type in ("unauthorized", "forbidden"):
                        workflow.logger.error(f"{error_type.upper()} - stopping workflow immediately")
                        error_messages = {
                            "unauthorized": "Session Vinted expirée. Veuillez vous reconnecter au plugin.",
                            "forbidden": "Accès bloqué par Vinted (403). Réessayez plus tard.",
                        }
                        return {
                            "status": "failed",
                            "error": error_type,
                            "synced_count": total_synced,
                            "message": error_messages.get(error_type, f"Erreur {error_type}"),
                        }

                    # 429 Rate Limited - wait longer then retry
                    if error_type == "rate_limited":
                        workflow.logger.warning("Rate limited during sync, pausing 60s before retry")
                        self._progress.label = "pause anti-blocage (rate_limited)..."
                        await asyncio.sleep(60)
                        continue

                    # 5xx Server Error - wait and retry
                    if error_type == "server_error":
                        workflow.logger.warning("Vinted server error, pausing 30s before retry")
                        self._progress.label = "erreur serveur Vinted, pause..."
                        await asyncio.sleep(30)
                        continue

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
            # PHASE 2: Enrich products (sequential, rate limiter handles delays)
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
                # Check for pause signal
                if self._paused:
                    if not await self._wait_while_paused(params, activity_options):
                        return await self._handle_cancellation(params, activity_options, total_synced)
                    # Restore running status after resume
                    await workflow.execute_activity(
                        update_job_progress,
                        args=[params.user_id, params.job_id, total_synced, "enrichissement en cours..."],
                        **activity_options,
                    )
                    continue

                # Get next batch (always offset=0 since enriched products have description now)
                vinted_ids_to_enrich = await workflow.execute_activity(
                    get_vinted_ids_to_enrich,
                    args=[params.user_id, sync_start_time, enrich_batch_size, 0],
                    **activity_options,
                )

                if not vinted_ids_to_enrich:
                    break  # No more products to enrich

                # Enrich products SEQUENTIALLY (no parallel - DataDome protection)
                should_retry_batch = False
                for vinted_id in vinted_ids_to_enrich:
                    if self._cancelled:
                        break

                    # Check for pause within batch
                    if self._paused:
                        if not await self._wait_while_paused(params, activity_options):
                            return await self._handle_cancellation(params, activity_options, total_synced)

                    result = await workflow.execute_activity(
                        enrich_single_product,
                        args=[params.user_id, vinted_id],
                        **activity_options,
                    )

                    if result.get("success"):
                        total_enriched += 1
                    else:
                        total_enrich_errors += 1
                        error = result.get("error", "")

                        # Handle disconnection or timeout with reconnection wait
                        if error in ("disconnected", "timeout"):
                            workflow.logger.warning(f"Plugin connection issue during enrich ({error}), waiting for reconnection")
                            if await self._wait_for_reconnection(params, activity_options):
                                await workflow.execute_activity(
                                    update_job_progress,
                                    args=[params.user_id, params.job_id, total_synced, "reprise de l'enrichissement..."],
                                    **activity_options,
                                )
                                should_retry_batch = True
                                break
                            else:
                                return {
                                    "status": "failed",
                                    "error": "disconnected_timeout",
                                    "synced_count": total_synced,
                                    "enriched": total_enriched,
                                    "message": "Plugin disconnected and reconnection timeout reached",
                                }

                        # 401 Unauthorized / 403 Forbidden - STOP immediately (no retry)
                        if error in ("unauthorized", "forbidden"):
                            workflow.logger.error(f"{error.upper()} during enrich - stopping workflow")
                            error_messages = {
                                "unauthorized": "Session Vinted expirée. Veuillez vous reconnecter au plugin.",
                                "forbidden": "Accès bloqué par Vinted (403). Réessayez plus tard.",
                            }
                            return {
                                "status": "failed",
                                "error": error,
                                "synced_count": total_synced,
                                "enriched": total_enriched,
                                "message": error_messages.get(error, f"Erreur {error}"),
                            }

                        # 429 Rate Limited - pause and retry batch
                        if error == "rate_limited":
                            workflow.logger.warning("Rate limited during enrich, pausing 60s")
                            self._progress.label = "pause anti-blocage (rate_limited)..."
                            await asyncio.sleep(60)
                            should_retry_batch = True
                            break

                        # 5xx Server Error - pause and retry
                        if error == "server_error":
                            workflow.logger.warning("Vinted server error during enrich, pausing 30s")
                            self._progress.label = "erreur serveur Vinted, pause..."
                            await asyncio.sleep(30)
                            should_retry_batch = True
                            break

                        # 404 not found - product sold/deleted, just skip it (not an error)
                        if error in ("not_found_vinted", "not_found_db"):
                            continue

                # If we should retry due to reconnection, continue the while loop
                if should_retry_batch:
                    continue

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

                # NOTE: No pause between batches - rate limiter handles delays

            # Handle cancellation after enrich phase
            if self._cancelled:
                return await self._handle_cancellation(params, activity_options, total_synced)

            # ═══════════════════════════════════════════════════════════
            # PHASE 3: Sync sold status (Vinted closed → StoFlow SOLD)
            # ═══════════════════════════════════════════════════════════
            self._progress.phase = "sold_sync"
            self._progress.label = "synchronisation des ventes..."

            await workflow.execute_activity(
                update_job_progress,
                args=[params.user_id, params.job_id, total_synced, "synchronisation des ventes..."],
                **activity_options,
            )

            sold_result = await workflow.execute_activity(
                sync_sold_status,
                args=[params.user_id],
                **activity_options,
            )

            sold_count = sold_result.get("updated_count", 0)
            if sold_count > 0:
                workflow.logger.info(f"Marked {sold_count} StoFlow products as SOLD")

            # Handle cancellation after sold sync phase
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
            final_label = f"{final_count} sync, {total_enriched} enrichis, {sold_count} vendus"
            self._progress.label = final_label

            return {
                "status": "completed",
                "final_count": final_count,
                "enriched": total_enriched,
                "sold_updated": sold_count,
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

    async def _wait_for_reconnection(
        self,
        params: VintedSyncParams,
        activity_options: dict,
        max_wait_seconds: int = 300,
    ) -> bool:
        """
        Wait for plugin reconnection with exponential backoff.

        Args:
            params: Workflow parameters
            activity_options: Activity execution options
            max_wait_seconds: Maximum time to wait (default 5 minutes)

        Returns:
            True if reconnected, False if timeout or cancelled
        """
        self._waiting_for_reconnection = True
        self._progress.status = "waiting_reconnection"
        self._progress.paused_at = workflow.now().isoformat()
        self._progress.pause_reason = "plugin_disconnected"
        self._progress.reconnection_attempts = 0

        # Mark job as paused in DB
        await workflow.execute_activity(
            mark_job_paused,
            args=[params.user_id, params.job_id, "waiting_reconnection"],
            **activity_options,
        )

        backoff = 5  # Start with 5 seconds
        total_waited = 0

        workflow.logger.info(
            f"Waiting for plugin reconnection (max {max_wait_seconds}s)"
        )

        while total_waited < max_wait_seconds:
            # Check for cancellation or resume signal
            if self._cancelled:
                workflow.logger.info("Reconnection wait cancelled")
                self._waiting_for_reconnection = False
                return False

            if self._resume_requested:
                workflow.logger.info("Reconnection wait resumed by user signal")
                self._resume_requested = False

            # Check plugin connection
            self._progress.reconnection_attempts += 1
            is_connected = await workflow.execute_activity(
                check_plugin_connection,
                args=[params.user_id],
                start_to_close_timeout=timedelta(seconds=30),
            )

            if is_connected:
                workflow.logger.info(
                    f"Plugin reconnected after {total_waited}s "
                    f"({self._progress.reconnection_attempts} attempts)"
                )
                self._waiting_for_reconnection = False
                self._progress.status = "running"
                self._progress.paused_at = None
                self._progress.pause_reason = None
                return True

            # Wait with exponential backoff
            workflow.logger.debug(
                f"Plugin not connected, waiting {backoff}s (total: {total_waited}s)"
            )
            await asyncio.sleep(backoff)
            total_waited += backoff
            backoff = min(backoff * 2, 60)  # Cap at 60 seconds

        # Timeout reached
        workflow.logger.warning(
            f"Plugin reconnection timeout after {max_wait_seconds}s"
        )
        self._waiting_for_reconnection = False
        return False

    async def _wait_while_paused(
        self,
        params: VintedSyncParams,
        activity_options: dict,
    ) -> bool:
        """
        Wait while the workflow is paused by user.

        Uses workflow.wait_condition for efficient waiting (no polling).

        Args:
            params: Workflow parameters
            activity_options: Activity execution options

        Returns:
            True if resumed, False if cancelled
        """
        # Mark job as paused in DB
        await workflow.execute_activity(
            mark_job_paused,
            args=[params.user_id, params.job_id, "user_pause"],
            **activity_options,
        )

        workflow.logger.info("Workflow paused, waiting for resume signal")

        # Wait for resume or cancel signal
        # workflow.wait_condition is efficient - no polling
        await workflow.wait_condition(
            lambda: self._resume_requested or self._cancelled
        )

        if self._cancelled:
            workflow.logger.info("Paused workflow cancelled")
            return False

        workflow.logger.info("Workflow resumed by user")
        self._paused = False
        self._resume_requested = False
        return True

    @workflow.signal
    def cancel_sync(self) -> None:
        """Signal to cancel the sync workflow."""
        self._cancelled = True
        self._progress.status = "cancelling"

    @workflow.signal
    def pause_sync(self) -> None:
        """Signal to pause the sync workflow."""
        if self._progress.status == "running":
            self._paused = True
            self._progress.status = "paused"
            self._progress.paused_at = workflow.now().isoformat()
            self._progress.pause_reason = "user_pause"
            workflow.logger.info("Sync paused by user signal")

    @workflow.signal
    def resume_sync(self) -> None:
        """Signal to resume a paused sync workflow."""
        if self._paused or self._waiting_for_reconnection:
            self._paused = False
            self._resume_requested = True
            self._progress.status = "running"
            self._progress.paused_at = None
            self._progress.pause_reason = None
            workflow.logger.info("Sync resumed by user signal")

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
            # Resilience fields
            "paused_at": self._progress.paused_at,
            "pause_reason": self._progress.pause_reason,
            "reconnection_attempts": self._progress.reconnection_attempts,
            # Control hints for UI
            "can_pause": self._progress.status == "running",
            "can_resume": self._progress.status in ("paused", "waiting_reconnection"),
        }
