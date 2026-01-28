"""Vinted Delete Workflow — deletes a product listing from Vinted via plugin."""

from dataclasses import dataclass
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

from temporal.activities.vinted_action_activities import vinted_delete_product


@dataclass
class VintedDeleteParams:
    """Parameters for Vinted delete workflow."""

    user_id: int
    product_id: int
    shop_id: int
    check_conditions: bool = True


@workflow.defn
class VintedDeleteWorkflow:
    """Delete a single product listing from Vinted."""

    def __init__(self):
        self._status = "running"
        self._result = None
        self._error = None

    @workflow.run
    async def run(self, params: VintedDeleteParams) -> dict:
        try:
            result = await workflow.execute_activity(
                vinted_delete_product,
                args=[
                    params.user_id,
                    params.product_id,
                    params.shop_id,
                    params.check_conditions,
                ],
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=2),
                    maximum_interval=timedelta(seconds=30),
                    maximum_attempts=3,
                    non_retryable_error_types=["RuntimeError"],
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
