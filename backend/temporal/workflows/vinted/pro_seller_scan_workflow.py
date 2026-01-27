"""
Vinted Pro Seller Scan Workflow for Temporal.

This workflow scans Vinted for professional (business) sellers by iterating
through a list of search keywords (business terms, legal forms, niches),
fetching user search results via the plugin, filtering for business accounts,
and storing them in the database.

Features:
- Durable execution (survives crashes)
- Progress tracking via queries
- Cancel/Pause/Resume via signals
- Automatic reconnection on plugin disconnect
- Rate limit handling (60s pause on 429)
- Continue-as-new support for long-running scans

Author: Claude
Date: 2026-01-27
"""

import asyncio
from dataclasses import dataclass, field
from datetime import timedelta
from typing import List, Optional

from temporalio import workflow
from temporalio.common import RetryPolicy

from temporal.activities.vinted_activities import (
    scan_pro_sellers_page,
    save_pro_sellers_batch,
    check_plugin_connection,
    get_keyword_scan_logs,
    update_keyword_scan_log,
)


@dataclass
class VintedProSellerScanParams:
    """Parameters for pro seller scan workflow."""

    user_id: int
    job_id: int  # Optional job tracking ID (0 if not used)

    # Search configuration
    keywords: List[str] = field(default_factory=list)
    marketplace: str = "vinted_fr"
    per_page: int = 90

    # Continue-as-new support
    start_keyword_index: int = 0
    accumulated_saved: int = 0
    accumulated_updated: int = 0
    accumulated_errors: int = 0


@dataclass
class VintedProSellerScanProgress:
    """Progress tracking for the scan workflow."""

    status: str = "initializing"
    current_keyword: Optional[str] = None
    current_page: int = 0
    total_saved: int = 0
    total_updated: int = 0
    total_errors: int = 0
    keywords_completed: int = 0
    total_keywords: int = 0
    # Resilience
    paused_at: Optional[str] = None
    pause_reason: Optional[str] = None
    reconnection_attempts: int = 0


@workflow.defn
class VintedProSellerScanWorkflow:
    """
    Temporal workflow that scans Vinted for professional sellers.

    Iterates through a list of search keywords (business terms, legal forms,
    niches), fetches pages of user results via the browser plugin, filters
    business=true users, and stores them with extracted contact information.

    Signals: cancel_scan, pause_scan, resume_scan
    Query: get_progress
    """

    def __init__(self):
        self._progress = VintedProSellerScanProgress()
        self._cancelled = False
        self._paused = False
        self._resume_requested = False
        self._waiting_for_reconnection = False

    @workflow.run
    async def run(self, params: VintedProSellerScanParams) -> dict:
        """Execute the pro seller scan workflow."""
        self._progress = VintedProSellerScanProgress(
            status="running",
            total_keywords=len(params.keywords),
            keywords_completed=params.start_keyword_index,
            total_saved=params.accumulated_saved,
            total_updated=params.accumulated_updated,
            total_errors=params.accumulated_errors,
        )

        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=2),
            maximum_interval=timedelta(seconds=120),
            backoff_coefficient=2.0,
            maximum_attempts=3,
        )

        activity_options = {
            "start_to_close_timeout": timedelta(minutes=5),
            "retry_policy": retry_policy,
        }

        total_saved = params.accumulated_saved
        total_updated = params.accumulated_updated
        total_errors = params.accumulated_errors

        try:
            # Load scan history to know where to resume each keyword
            scan_logs: dict = await workflow.execute_activity(
                get_keyword_scan_logs,
                args=[params.marketplace],
                start_to_close_timeout=timedelta(seconds=30),
            )

            for kw_idx in range(params.start_keyword_index, len(params.keywords)):
                if self._cancelled:
                    break

                keyword = params.keywords[kw_idx]
                self._progress.current_keyword = keyword
                self._progress.keywords_completed = kw_idx

                # Check scan history for this keyword
                kw_log = scan_logs.get(keyword)
                if kw_log and kw_log.get("exhausted"):
                    workflow.logger.info(
                        f"Skipping '{keyword}' — already exhausted "
                        f"({kw_log['total_found']} found previously)"
                    )
                    self._progress.keywords_completed = kw_idx + 1
                    continue

                # Resume from last scanned page + 1
                start_page = (kw_log["last_page"] + 1) if kw_log else 1

                workflow.logger.info(
                    f"Scanning keyword '{keyword}' ({kw_idx + 1}/{len(params.keywords)}) "
                    f"from page {start_page}"
                )

                page = start_page
                keyword_saved = 0
                keyword_exhausted = False

                while not self._cancelled:
                    # Check for pause
                    if self._paused:
                        if not await self._wait_while_paused(params, activity_options):
                            return self._build_result("cancelled", total_saved, total_updated, total_errors)

                    self._progress.current_page = page

                    # Fetch page
                    result = await workflow.execute_activity(
                        scan_pro_sellers_page,
                        args=[params.user_id, keyword, page, params.per_page],
                        **activity_options,
                    )

                    error = result.get("error")
                    if error:
                        # Plugin disconnected or timeout -> wait for reconnection
                        if error in ("disconnected", "timeout"):
                            workflow.logger.warning(
                                f"Plugin issue ({error}) at '{keyword}' page {page}, waiting..."
                            )
                            if await self._wait_for_reconnection(params, activity_options):
                                continue  # Retry same page
                            else:
                                return self._build_result(
                                    "failed", total_saved, total_updated, total_errors,
                                    error="disconnected_timeout",
                                )

                        # Auth errors -> stop immediately
                        if error in ("unauthorized", "forbidden"):
                            workflow.logger.error(f"{error.upper()} - stopping scan")
                            return self._build_result(
                                "failed", total_saved, total_updated, total_errors,
                                error=error,
                            )

                        # Rate limited -> pause 60s then retry
                        if error == "rate_limited":
                            workflow.logger.warning("Rate limited, pausing 60s")
                            self._progress.status = "rate_limited"
                            await asyncio.sleep(60)
                            self._progress.status = "running"
                            continue

                        # Server error -> pause 30s then retry
                        if error == "server_error":
                            workflow.logger.warning("Server error, pausing 30s")
                            await asyncio.sleep(30)
                            continue

                    pro_sellers = result.get("pro_sellers", [])
                    total_pages = result.get("total_pages", page)

                    # Save batch if we have results
                    if pro_sellers:
                        save_result = await workflow.execute_activity(
                            save_pro_sellers_batch,
                            args=[pro_sellers, params.marketplace, params.user_id],
                            **activity_options,
                        )
                        batch_saved = save_result.get("saved", 0)
                        total_saved += batch_saved
                        total_updated += save_result.get("updated", 0)
                        total_errors += save_result.get("errors", 0)
                        keyword_saved += batch_saved

                    # Update progress
                    self._progress.total_saved = total_saved
                    self._progress.total_updated = total_updated
                    self._progress.total_errors = total_errors

                    # Check if more pages
                    if page >= total_pages or not pro_sellers:
                        keyword_exhausted = True
                        break

                    page += 1

                    # Small delay between pages to avoid rate limiting
                    await asyncio.sleep(2)

                # Record scan progress for this keyword
                if not self._cancelled:
                    await workflow.execute_activity(
                        update_keyword_scan_log,
                        args=[keyword, params.marketplace, page, keyword_saved, keyword_exhausted],
                        start_to_close_timeout=timedelta(seconds=30),
                    )

                # Update keywords completed
                self._progress.keywords_completed = kw_idx + 1

                # Small delay between keywords
                if not self._cancelled and kw_idx < len(params.keywords) - 1:
                    await asyncio.sleep(3)

            # Done
            if self._cancelled:
                return self._build_result("cancelled", total_saved, total_updated, total_errors)

            self._progress.status = "completed"
            return self._build_result("completed", total_saved, total_updated, total_errors)

        except Exception as e:
            self._progress.status = "failed"
            workflow.logger.error(f"Scan workflow failed: {e}")
            raise

    def _build_result(
        self,
        status: str,
        saved: int,
        updated: int,
        errors: int,
        error: Optional[str] = None,
    ) -> dict:
        """Build workflow result dict."""
        result = {
            "status": status,
            "total_saved": saved,
            "total_updated": updated,
            "total_errors": errors,
            "keywords_completed": self._progress.keywords_completed,
            "total_keywords": self._progress.total_keywords,
        }
        if error:
            result["error"] = error
        return result

    async def _wait_for_reconnection(
        self,
        params: VintedProSellerScanParams,
        activity_options: dict,
        max_wait_seconds: int = 300,
    ) -> bool:
        """Wait for plugin reconnection with exponential backoff."""
        self._waiting_for_reconnection = True
        self._progress.status = "waiting_reconnection"
        self._progress.paused_at = workflow.now().isoformat()
        self._progress.pause_reason = "plugin_disconnected"
        self._progress.reconnection_attempts = 0

        backoff = 5
        total_waited = 0

        workflow.logger.info(f"Waiting for plugin reconnection (max {max_wait_seconds}s)")

        while total_waited < max_wait_seconds:
            if self._cancelled:
                self._waiting_for_reconnection = False
                return False

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

            await asyncio.sleep(backoff)
            total_waited += backoff
            backoff = min(backoff * 2, 60)

        workflow.logger.warning(f"Plugin reconnection timeout after {max_wait_seconds}s")
        self._waiting_for_reconnection = False
        return False

    async def _wait_while_paused(
        self,
        params: VintedProSellerScanParams,
        activity_options: dict,
    ) -> bool:
        """Wait while paused by user. Returns True if resumed, False if cancelled."""
        self._progress.paused_at = workflow.now().isoformat()
        self._progress.pause_reason = "user_pause"

        workflow.logger.info("Scan paused, waiting for resume signal")

        await workflow.wait_condition(
            lambda: self._resume_requested or self._cancelled
        )

        if self._cancelled:
            return False

        self._paused = False
        self._resume_requested = False
        self._progress.status = "running"
        self._progress.paused_at = None
        self._progress.pause_reason = None
        workflow.logger.info("Scan resumed by user")
        return True

    @workflow.signal
    def cancel_scan(self) -> None:
        """Signal to cancel the scan."""
        self._cancelled = True
        self._progress.status = "cancelling"

    @workflow.signal
    def pause_scan(self) -> None:
        """Signal to pause the scan."""
        if self._progress.status == "running":
            self._paused = True
            self._progress.status = "paused"
            workflow.logger.info("Scan paused by user signal")

    @workflow.signal
    def resume_scan(self) -> None:
        """Signal to resume a paused scan."""
        if self._paused or self._waiting_for_reconnection:
            self._paused = False
            self._resume_requested = True
            self._progress.status = "running"
            self._progress.paused_at = None
            self._progress.pause_reason = None
            workflow.logger.info("Scan resumed by user signal")

    @workflow.query
    def get_progress(self) -> dict:
        """Query current scan progress."""
        return {
            "status": self._progress.status,
            "current_keyword": self._progress.current_keyword,
            "current_page": self._progress.current_page,
            "total_saved": self._progress.total_saved,
            "total_updated": self._progress.total_updated,
            "total_errors": self._progress.total_errors,
            "keywords_completed": self._progress.keywords_completed,
            "total_keywords": self._progress.total_keywords,
            # Resilience
            "paused_at": self._progress.paused_at,
            "pause_reason": self._progress.pause_reason,
            "reconnection_attempts": self._progress.reconnection_attempts,
            # Control hints
            "can_pause": self._progress.status == "running",
            "can_resume": self._progress.status in ("paused", "waiting_reconnection"),
        }
