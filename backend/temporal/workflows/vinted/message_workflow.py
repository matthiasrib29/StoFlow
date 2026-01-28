"""Vinted Message Workflow — synchronizes messages from Vinted."""

from dataclasses import dataclass
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

from temporal.activities.vinted_action_activities import vinted_send_message


@dataclass
class VintedMessageParams:
    """Parameters for Vinted message workflow."""

    user_id: int
    shop_id: int
    conversation_id: int = 0  # 0 = sync inbox


@workflow.defn
class VintedMessageWorkflow:
    """Synchronize messages from Vinted."""

    def __init__(self):
        self._status = "running"
        self._result = None
        self._error = None

    @workflow.run
    async def run(self, params: VintedMessageParams) -> dict:
        try:
            result = await workflow.execute_activity(
                vinted_send_message,
                args=[params.user_id, params.shop_id, params.conversation_id],
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=2),
                    maximum_interval=timedelta(seconds=60),
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
