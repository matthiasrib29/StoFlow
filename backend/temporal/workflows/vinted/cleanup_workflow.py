"""
Vinted Cleanup Workflows for Temporal.

Triggered when a user confirms pending actions (product sold on StoFlow,
delete the Vinted listing).

Two workflows:
- VintedCleanupWorkflow: Single product deletion (fire-and-forget)
- VintedBatchCleanupWorkflow: Sequential deletion of multiple products

Author: Claude
Date: 2026-01-26
"""

from dataclasses import dataclass, field
from datetime import timedelta
from typing import List

from temporalio import workflow
from temporalio.common import RetryPolicy

from temporal.activities.vinted_activities import delete_vinted_listing


# Shared retry policy for all cleanup activities
_CLEANUP_RETRY = RetryPolicy(
    initial_interval=timedelta(seconds=5),
    maximum_interval=timedelta(seconds=60),
    maximum_attempts=3,
)


@dataclass
class VintedCleanupParams:
    """Parameters for single Vinted cleanup workflow."""

    user_id: int
    product_id: int


@dataclass
class VintedBatchCleanupParams:
    """Parameters for batch Vinted cleanup workflow."""

    user_id: int
    product_ids: List[int] = field(default_factory=list)


@workflow.defn
class VintedCleanupWorkflow:
    """
    Workflow to delete a single Vinted listing.

    Used for individual confirm actions.
    Retry policy: 3 attempts with 5-60s backoff.
    """

    @workflow.run
    async def run(self, params: VintedCleanupParams) -> dict:
        result = await workflow.execute_activity(
            delete_vinted_listing,
            args=[params.user_id, params.product_id],
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=_CLEANUP_RETRY,
        )
        return result


@workflow.defn
class VintedBatchCleanupWorkflow:
    """
    Workflow to delete multiple Vinted listings sequentially.

    Used for bulk confirm / confirm-all actions.
    Products are processed one by one to avoid parallel plugin calls.
    """

    @workflow.run
    async def run(self, params: VintedBatchCleanupParams) -> dict:
        succeeded = 0
        failed = 0
        results = []

        for product_id in params.product_ids:
            result = await workflow.execute_activity(
                delete_vinted_listing,
                args=[params.user_id, product_id],
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=_CLEANUP_RETRY,
            )

            results.append(result)
            if result.get("success"):
                succeeded += 1
            else:
                failed += 1

        return {
            "total": len(params.product_ids),
            "succeeded": succeeded,
            "failed": failed,
            "results": results,
        }
