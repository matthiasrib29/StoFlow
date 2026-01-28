"""
Vinted Fetch Users Workflow — fetches Vinted users for prospection.

Complex workflow with:
- A-Z alphabet iteration
- Pagination per character
- Cooperative cancellation
- Progress tracking
- Rate limiting (2.5s between API calls)

Pattern modeled after VintedProSellerScanWorkflow.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import timedelta
from typing import List, Optional

from temporalio import workflow
from temporalio.common import RetryPolicy

from temporal.activities.vinted_action_activities import (
    vinted_fetch_users_page,
    vinted_save_prospects_batch,
)

SEARCH_CHARS = list("abcdefghijklmnopqrstuvwxyz")


@dataclass
class VintedFetchUsersParams:
    """Parameters for Vinted fetch users workflow."""

    user_id: int
    country_code: str = "FR"
    min_items: int = 200
    max_pages_per_search: int = 50
    per_page: int = 100

    # Continue-as-new support
    start_char_index: int = 0
    accumulated_saved: int = 0
    accumulated_duplicates: int = 0
    accumulated_errors: int = 0


@dataclass
class FetchUsersProgress:
    """Progress tracking for fetch users workflow."""

    status: str = "initializing"
    current_char: Optional[str] = None
    current_page: int = 0
    total_saved: int = 0
    total_duplicates: int = 0
    total_errors: int = 0
    chars_completed: int = 0
    total_chars: int = 26
    error: Optional[str] = None


@workflow.defn
class VintedFetchUsersWorkflow:
    """
    Fetch Vinted users by iterating A-Z and paginating results.

    Uses two activities:
    - vinted_fetch_users_page: Fetches and filters one page of users
    - vinted_save_prospects_batch: Saves filtered users to database
    """

    def __init__(self):
        self._progress = FetchUsersProgress()
        self._cancelled = False

    @workflow.run
    async def run(self, params: VintedFetchUsersParams) -> dict:
        self._progress = FetchUsersProgress(
            status="running",
            total_saved=params.accumulated_saved,
            total_duplicates=params.accumulated_duplicates,
            total_errors=params.accumulated_errors,
            chars_completed=params.start_char_index,
        )

        activity_options = {
            "start_to_close_timeout": timedelta(minutes=2),
            "retry_policy": RetryPolicy(
                initial_interval=timedelta(seconds=5),
                maximum_interval=timedelta(seconds=60),
                maximum_attempts=3,
            ),
        }

        save_options = {
            "start_to_close_timeout": timedelta(minutes=1),
            "retry_policy": RetryPolicy(
                initial_interval=timedelta(seconds=1),
                maximum_interval=timedelta(seconds=10),
                maximum_attempts=3,
            ),
        }

        try:
            chars_to_process = SEARCH_CHARS[params.start_char_index:]

            for char_idx, char in enumerate(chars_to_process, start=params.start_char_index):
                if self._cancelled:
                    self._progress.status = "cancelled"
                    break

                self._progress.current_char = char
                self._progress.chars_completed = char_idx

                workflow.logger.info(f"Searching users with '{char}'...")

                for page in range(1, params.max_pages_per_search + 1):
                    if self._cancelled:
                        self._progress.status = "cancelled"
                        break

                    self._progress.current_page = page
                    self._progress.label = f"Recherche '{char.upper()}' page {page}..."

                    # Fetch one page of users
                    fetch_result = await workflow.execute_activity(
                        vinted_fetch_users_page,
                        args=[
                            params.user_id,
                            char,
                            page,
                            params.per_page,
                            params.country_code,
                            params.min_items,
                        ],
                        **activity_options,
                    )

                    # Handle API errors
                    if fetch_result.get("error"):
                        error = fetch_result["error"]
                        if error == "disconnected":
                            self._progress.status = "failed"
                            self._progress.error = "Plugin disconnected"
                            return self._build_result("failed", "disconnected")

                        if error in ("rate_limited", "timeout"):
                            self._progress.total_errors += 1
                            # Wait longer and retry on next iteration
                            await asyncio.sleep(10)
                            continue

                        # Other errors: log and continue
                        self._progress.total_errors += 1
                        continue

                    # Save filtered users
                    users = fetch_result.get("users", [])
                    if users:
                        save_result = await workflow.execute_activity(
                            vinted_save_prospects_batch,
                            args=[users, params.user_id],
                            **save_options,
                        )
                        self._progress.total_saved += save_result.get("saved", 0)
                        self._progress.total_duplicates += save_result.get("duplicates", 0)
                        self._progress.total_errors += save_result.get("errors", 0)

                    # Check if last page
                    if not fetch_result.get("has_more", False):
                        break

                    # Rate limiting (2.5s between Vinted API calls)
                    await asyncio.sleep(2.5)

                # Update progress after completing a character
                self._progress.chars_completed = char_idx + 1

            # All done
            if not self._cancelled:
                self._progress.status = "completed"

            return self._build_result(self._progress.status)

        except Exception as e:
            self._progress.status = "failed"
            self._progress.error = str(e)
            raise

    def _build_result(self, status: str, error: str = None) -> dict:
        return {
            "status": status,
            "total_saved": self._progress.total_saved,
            "total_duplicates": self._progress.total_duplicates,
            "total_errors": self._progress.total_errors,
            "chars_completed": self._progress.chars_completed,
            "error": error or self._progress.error,
        }

    # ═══════════════════════════════════════════════════════════════
    # SIGNALS
    # ═══════════════════════════════════════════════════════════════

    @workflow.signal
    def cancel(self) -> None:
        self._cancelled = True
        self._progress.status = "cancelling"
        workflow.logger.info("Fetch users cancelled by signal")

    # ═══════════════════════════════════════════════════════════════
    # QUERIES
    # ═══════════════════════════════════════════════════════════════

    @workflow.query
    def get_progress(self) -> dict:
        return {
            "status": self._progress.status,
            "current_char": self._progress.current_char,
            "current_page": self._progress.current_page,
            "total_saved": self._progress.total_saved,
            "total_duplicates": self._progress.total_duplicates,
            "total_errors": self._progress.total_errors,
            "chars_completed": self._progress.chars_completed,
            "total_chars": self._progress.total_chars,
            "error": self._progress.error,
        }
