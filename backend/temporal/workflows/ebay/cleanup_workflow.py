"""
eBay Cleanup Workflow for Temporal.

Triggered when a user confirms a DELETE_EBAY_LISTING pending action.
Deletes the associated eBay listing via the eBay API.

This workflow is fire-and-forget: the user confirms the pending action,
and the eBay deletion happens asynchronously with retries.

Author: Claude
Date: 2026-01-26
"""

from dataclasses import dataclass
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

from temporal.activities.ebay_activities import delete_ebay_listing


@dataclass
class EbayCleanupParams:
    """Parameters for eBay cleanup workflow."""

    user_id: int
    product_id: int
    marketplace_id: str = "EBAY_FR"


@workflow.defn
class EbayCleanupWorkflow:
    """
    Workflow to delete an eBay listing after user confirms the pending action.

    Simple single-activity workflow:
    1. Call delete_ebay_listing (eBay API delete + local DB cleanup)
    2. Return the result (success/failure)

    Retry policy: 3 attempts with 5-60s backoff.
    """

    @workflow.run
    async def run(self, params: EbayCleanupParams) -> dict:
        """
        Execute the eBay cleanup workflow.

        Args:
            params: EbayCleanupParams with user_id, product_id, marketplace_id

        Returns:
            Dict with success status and product_id
        """
        result = await workflow.execute_activity(
            delete_ebay_listing,
            args=[params.user_id, params.product_id, params.marketplace_id],
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=5),
                maximum_interval=timedelta(seconds=60),
                maximum_attempts=3,
            ),
        )
        return result
