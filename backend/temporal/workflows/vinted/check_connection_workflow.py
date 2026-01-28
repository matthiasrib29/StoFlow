"""Vinted Check Connection Workflow — checks Vinted connection status."""

from dataclasses import dataclass
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

from temporal.activities.vinted_action_activities import vinted_check_connection


@dataclass
class VintedCheckConnectionParams:
    """Parameters for Vinted check connection workflow."""

    user_id: int


@workflow.defn
class VintedCheckConnectionWorkflow:
    """Check Vinted connection status via plugin."""

    def __init__(self):
        self._status = "running"
        self._result = None
        self._error = None

    @workflow.run
    async def run(self, params: VintedCheckConnectionParams) -> dict:
        try:
            result = await workflow.execute_activity(
                vinted_check_connection,
                args=[params.user_id],
                start_to_close_timeout=timedelta(minutes=1),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(seconds=10),
                    maximum_attempts=2,
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
