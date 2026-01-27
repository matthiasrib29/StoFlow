"""
eBay Apply Policy Workflow for Temporal.

This workflow applies a business policy (payment, fulfillment, or return)
to all existing eBay offers for a marketplace.

Offers are dispatched in batches of 500 to Temporal. The worker's
ThreadPoolExecutor (30 threads) processes them as a sliding window:
as soon as one thread finishes, it picks up the next activity.
Progress is updated in the DB after each dispatch batch.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Optional

from temporalio import workflow
from temporalio.common import RetryPolicy

from temporal.activities.ebay_activities import (
    apply_policy_to_single_offer,
    update_job_progress,
    mark_job_completed,
    mark_job_failed,
)


@dataclass
class ApplyPolicyParams:
    """Parameters for the apply policy workflow."""

    user_id: int
    job_id: int
    marketplace_id: str
    policy_type: str  # "payment" | "fulfillment" | "return"
    policy_id: str
    policy_field: str  # "paymentPolicyId" | "fulfillmentPolicyId" | "returnPolicyId"
    offer_ids: list[str] = field(default_factory=list)


@dataclass
class ApplyPolicyProgress:
    """Progress tracking for the apply policy workflow."""

    status: str = "initializing"
    current: int = 0
    total: int = 0
    updated: int = 0
    skipped: int = 0
    errors: int = 0
    label: str = "initialisation..."


@workflow.defn
class EbayApplyPolicyWorkflow:
    """
    Temporal workflow to apply a business policy to all eBay offers.

    Features:
    - Dispatch batches of 500 activities to Temporal
    - Sliding window: 30 concurrent threads, each picks up next on completion
    - Progress tracking via queries
    - Cancellation support via signal
    - DB progress updates after each dispatch batch
    """

    def __init__(self):
        self._progress = ApplyPolicyProgress()
        self._cancelled = False

    @workflow.run
    async def run(self, params: ApplyPolicyParams) -> dict:
        """
        Execute the apply policy workflow.

        Args:
            params: Workflow parameters (user_id, job_id, offer_ids, etc.)

        Returns:
            Dict with results (updated, skipped, errors)
        """
        self._progress = ApplyPolicyProgress(
            status="running",
            total=len(params.offer_ids),
            label=f"0/{len(params.offer_ids)} offres traitées",
        )

        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=2),
            maximum_interval=timedelta(seconds=30),
            backoff_coefficient=2.0,
            maximum_attempts=3,
        )

        activity_options = {
            "start_to_close_timeout": timedelta(seconds=30),
            "retry_policy": retry_policy,
        }

        progress_activity_options = {
            "start_to_close_timeout": timedelta(seconds=10),
            "retry_policy": RetryPolicy(maximum_attempts=2),
        }

        # Dispatch batch size: send 500 activities at once to Temporal.
        # The worker's ThreadPoolExecutor (30 threads) processes them with
        # a sliding window: as soon as one finishes, the next starts.
        dispatch_batch = 500

        try:
            # Initial progress update
            await workflow.execute_activity(
                update_job_progress,
                args=[params.user_id, params.job_id, 0, "application en cours..."],
                **progress_activity_options,
            )

            # Process offers in dispatch batches (500 at a time)
            for i in range(0, len(params.offer_ids), dispatch_batch):
                if self._cancelled:
                    break

                batch = params.offer_ids[i:i + dispatch_batch]

                # Launch all activities in this batch concurrently.
                # Temporal's worker (30 threads) picks them up as a sliding
                # window: as soon as one thread finishes, it grabs the next.
                tasks = []
                for offer_id in batch:
                    task = workflow.execute_activity(
                        apply_policy_to_single_offer,
                        args=[
                            params.user_id,
                            offer_id,
                            params.marketplace_id,
                            params.policy_field,
                            params.policy_id,
                        ],
                        **activity_options,
                    )
                    tasks.append(task)

                # Wait for all in dispatch batch to complete
                results = await asyncio.gather(*tasks)

                # Aggregate results
                for result in results:
                    if result.get("success"):
                        if result.get("skipped"):
                            self._progress.skipped += 1
                        else:
                            self._progress.updated += 1
                    else:
                        self._progress.errors += 1

                self._progress.current = min(i + len(batch), len(params.offer_ids))
                self._progress.label = (
                    f"{self._progress.current}/{self._progress.total} offres traitées"
                )

                # Update DB progress after each dispatch batch
                await workflow.execute_activity(
                    update_job_progress,
                    args=[
                        params.user_id,
                        params.job_id,
                        self._progress.current,
                        self._progress.label,
                    ],
                    **progress_activity_options,
                )

            # Handle cancellation
            if self._cancelled:
                self._progress.status = "cancelled"
                await workflow.execute_activity(
                    mark_job_failed,
                    args=[params.user_id, params.job_id, "Annulé par l'utilisateur"],
                    **progress_activity_options,
                )
                return {
                    "status": "cancelled",
                    "updated": self._progress.updated,
                    "skipped": self._progress.skipped,
                    "errors": self._progress.errors,
                }

            # Mark completed
            await workflow.execute_activity(
                mark_job_completed,
                args=[params.user_id, params.job_id, self._progress.updated],
                **progress_activity_options,
            )

            self._progress.status = "completed"
            self._progress.label = (
                f"{self._progress.updated} mises à jour, "
                f"{self._progress.skipped} ignorées, "
                f"{self._progress.errors} erreurs"
            )

            return {
                "status": "completed",
                "updated": self._progress.updated,
                "skipped": self._progress.skipped,
                "errors": self._progress.errors,
                "total": self._progress.total,
            }

        except Exception as e:
            self._progress.status = "failed"

            try:
                await workflow.execute_activity(
                    mark_job_failed,
                    args=[params.user_id, params.job_id, str(e)],
                    start_to_close_timeout=timedelta(seconds=10),
                )
            except Exception:
                pass  # Best effort

            raise

    @workflow.signal
    def cancel(self) -> None:
        """Signal to cancel the workflow."""
        self._cancelled = True
        self._progress.status = "cancelling"

    @workflow.query
    def get_progress(self) -> dict:
        """Query current progress."""
        return {
            "status": self._progress.status,
            "current": self._progress.current,
            "total": self._progress.total,
            "updated": self._progress.updated,
            "skipped": self._progress.skipped,
            "errors": self._progress.errors,
            "label": self._progress.label,
        }
