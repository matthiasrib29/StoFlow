"""
Temporal worker management module.

Provides lifecycle management for Temporal workers.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Type

from temporalio.worker import Worker, UnsandboxedWorkflowRunner

from temporal.client import get_temporal_client
from temporal.config import get_temporal_config

logger = logging.getLogger(__name__)


class TemporalWorkerManager:
    """
    Manages Temporal worker lifecycle.

    Handles starting and stopping workers for workflow execution.
    Designed to run in-process with the FastAPI application.
    """

    def __init__(self):
        self._worker: Optional[Worker] = None
        self._worker_task: Optional[asyncio.Task] = None
        self._executor: Optional[ThreadPoolExecutor] = None
        self._running = False
        self._workflows: List[Type] = []
        self._activities: List = []

    def register_workflow(self, workflow_class: Type) -> None:
        """Register a workflow class to be handled by the worker."""
        self._workflows.append(workflow_class)
        logger.debug(f"Registered workflow: {workflow_class.__name__}")

    def register_activity(self, activity_func) -> None:
        """Register an activity function to be handled by the worker."""
        self._activities.append(activity_func)
        logger.debug(f"Registered activity: {activity_func.__name__}")

    def register_activities(self, activities: List) -> None:
        """Register multiple activity functions."""
        for activity in activities:
            self.register_activity(activity)

    async def start(self) -> None:
        """
        Start the Temporal worker.

        Creates a worker and starts it in the background.
        The worker will process workflows and activities from the configured task queue.
        """
        if self._running:
            logger.warning("Worker is already running")
            return

        config = get_temporal_config()

        if not config.temporal_enabled:
            logger.info("Temporal is disabled, skipping worker start")
            return

        if not self._workflows and not self._activities:
            logger.warning("No workflows or activities registered, skipping worker start")
            return

        try:
            client = await get_temporal_client()

            logger.info(
                "Starting Temporal worker",
                extra={
                    "task_queue": config.temporal_task_queue,
                    "identity": config.worker_identity,
                    "workflows": [w.__name__ for w in self._workflows],
                    "activities": [a.__name__ for a in self._activities],
                    "max_concurrent_activities": config.temporal_max_concurrent_activities,
                }
            )

            # Create ThreadPoolExecutor for sync activities
            # This allows true parallel execution of activities using requests (sync HTTP)
            self._executor = ThreadPoolExecutor(
                max_workers=config.temporal_max_concurrent_activities,
                thread_name_prefix="temporal-activity-",
            )

            self._worker = Worker(
                client,
                task_queue=config.temporal_task_queue,
                workflows=self._workflows,
                activities=self._activities,
                identity=config.worker_identity,
                max_concurrent_workflow_tasks=config.temporal_max_concurrent_workflow_tasks,
                max_concurrent_activities=config.temporal_max_concurrent_activities,
                activity_executor=self._executor,  # Required for sync activities
                workflow_runner=UnsandboxedWorkflowRunner(),  # Disable sandbox for simpler imports
            )

            # Start worker in background task
            self._worker_task = asyncio.create_task(self._run_worker())
            self._running = True

            logger.info("Temporal worker started successfully")

        except Exception as e:
            logger.error(f"Failed to start Temporal worker: {e}")
            raise

    async def _run_worker(self) -> None:
        """Internal method to run the worker."""
        try:
            await self._worker.run()
        except asyncio.CancelledError:
            logger.info("Temporal worker task cancelled")
        except Exception as e:
            logger.error(f"Temporal worker error: {e}")
            self._running = False
            raise

    async def stop(self) -> None:
        """
        Stop the Temporal worker gracefully.

        Allows in-flight workflows and activities to complete.
        """
        if not self._running:
            logger.debug("Worker is not running")
            return

        logger.info("Stopping Temporal worker...")

        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

        # Shutdown executor
        if self._executor:
            self._executor.shutdown(wait=False)
            self._executor = None

        self._running = False
        self._worker = None
        self._worker_task = None

        logger.info("Temporal worker stopped")

    @property
    def is_running(self) -> bool:
        """Check if the worker is currently running."""
        return self._running


# Global worker manager instance
_worker_manager: Optional[TemporalWorkerManager] = None


def get_worker_manager() -> TemporalWorkerManager:
    """Get or create the global worker manager instance."""
    global _worker_manager
    if _worker_manager is None:
        _worker_manager = TemporalWorkerManager()
    return _worker_manager
