"""eBay Orders Sync Workflow — synchronizes orders from eBay."""

from dataclasses import dataclass
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

from temporal.activities.ebay_action_activities import ebay_sync_orders


@dataclass
class EbayOrdersSyncParams:
    """Parameters for eBay orders sync workflow."""

    user_id: int
    marketplace_id: str = "EBAY_FR"


@workflow.defn
class EbayOrdersSyncWorkflow:
    """Synchronize orders from eBay."""

    def __init__(self):
        self._status = "running"
        self._result = None
        self._error = None

    @workflow.run
    async def run(self, params: EbayOrdersSyncParams) -> dict:
        try:
            result = await workflow.execute_activity(
                ebay_sync_orders,
                args=[params.user_id, params.marketplace_id],
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(seconds=60),
                    maximum_attempts=3,
                ),
            )

            self._result = result
            self._status = "completed" if result.get("success") else "failed"
            self._error = result.get("error")
            return result

        except Exception as e:
            self._status = "failed"
            self._error = str(e)
            raise

    @workflow.query
    def get_progress(self) -> dict:
        return {
            "status": self._status,
            "result": self._result,
            "error": self._error,
        }

    @workflow.signal
    def cancel(self) -> None:
        pass
