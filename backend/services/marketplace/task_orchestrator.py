"""
Task Orchestrator Service

Manages creation and execution of MarketplaceTask objects for retry-intelligent job processing.

Business Rules:
- Tasks are created with sequential positions (1, 2, 3...)
- Each task linked to parent MarketplaceJob via job_id
- Status starts as PENDING
- Tasks are committed in batch for performance
- Each task execution commits independently (1 commit per task)

Created: 2026-01-15
Phase: 01-02 Task Orchestration Foundation
Author: Claude
"""

import logging
from typing import List, Callable, Any
from dataclasses import dataclass
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from models.user.marketplace_job import MarketplaceJob
from models.user.marketplace_task import MarketplaceTask, TaskStatus

logger = logging.getLogger("stoflow.services.task_orchestrator")


@dataclass
class TaskResult:
    """
    Result wrapper for task execution.

    Encapsulates success/failure status and result data or error message.
    """
    success: bool
    result: dict | None = None
    error: str | None = None


class TaskOrchestrator:
    """
    Orchestrates creation and execution of tasks within a MarketplaceJob.

    Enables retry intelligence: skip COMPLETED tasks, retry only FAILED/PENDING.
    """

    def __init__(self, db: Session):
        """
        Initialize TaskOrchestrator.

        Args:
            db: SQLAlchemy session for database operations
        """
        self.db = db

    def create_tasks(
        self,
        job: MarketplaceJob,
        task_names: List[str]
    ) -> List[MarketplaceTask]:
        """
        Create ordered tasks for a job.

        Each task gets:
        - Sequential position (1, 2, 3...)
        - Link to parent job (job_id)
        - Initial status PENDING
        - Description from task_names

        Args:
            job: Parent MarketplaceJob
            task_names: List of human-readable task descriptions
                       (e.g., ["Upload image 1/3", "Upload image 2/3", "Create listing"])

        Returns:
            List of created MarketplaceTask objects (committed to DB)

        Example:
            >>> orchestrator = TaskOrchestrator(db)
            >>> tasks = orchestrator.create_tasks(
            ...     job,
            ...     ["Validate product", "Upload images", "Publish"]
            ... )
            >>> print(tasks[0].position)  # 1
            >>> print(tasks[0].status)     # TaskStatus.PENDING
        """
        tasks = []

        for position, task_name in enumerate(task_names, start=1):
            task = MarketplaceTask(
                job_id=job.id,
                description=task_name,
                position=position,
                status=TaskStatus.PENDING
            )
            self.db.add(task)
            tasks.append(task)

        # Batch commit for performance
        self.db.commit()

        return tasks

    def execute_task(
        self,
        task: MarketplaceTask,
        handler: Callable[[MarketplaceTask], Any]
    ) -> TaskResult:
        """
        Execute a single task with the provided handler.

        Workflow:
        1. Mark task PROCESSING, set started_at → commit
        2. Call handler function with task as argument
        3. On success: mark SUCCESS, store result, set completed_at → commit
        4. On failure: mark FAILED, store error, set completed_at → commit

        Each task execution commits independently for visibility (1 commit per task).

        Args:
            task: MarketplaceTask to execute
            handler: Callable that takes task and returns result dict
                    Should raise exception on failure

        Returns:
            TaskResult with success status and result/error

        Example:
            >>> def upload_image(task: MarketplaceTask) -> dict:
            ...     # Upload logic
            ...     return {"image_url": "https://..."}
            >>>
            >>> result = orchestrator.execute_task(task, upload_image)
            >>> if result.success:
            ...     print(result.result["image_url"])
        """
        try:
            # 1. Mark PROCESSING (RUNNING)
            task.status = TaskStatus.PROCESSING
            task.started_at = datetime.now(timezone.utc)
            self.db.commit()

            logger.info(f"Task #{task.id} ({task.description}) started")

            # 2. Execute handler
            result_data = handler(task)

            # 3. Mark SUCCESS
            task.status = TaskStatus.SUCCESS
            task.completed_at = datetime.now(timezone.utc)
            task.result = result_data
            self.db.commit()

            logger.info(f"Task #{task.id} completed successfully")

            return TaskResult(success=True, result=result_data)

        except Exception as e:
            # Mark FAILED
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.now(timezone.utc)
            self.db.commit()

            logger.error(f"Task #{task.id} failed: {e}")

            return TaskResult(success=False, error=str(e))

    def should_skip_task(self, task: MarketplaceTask) -> bool:
        """
        Check if a task should be skipped during job execution.

        Retry intelligence: Skip only COMPLETED (SUCCESS) tasks.
        Execute PENDING and FAILED tasks (retry).

        Args:
            task: MarketplaceTask to check

        Returns:
            True if task should be skipped (already SUCCESS)
            False if task should be executed (PENDING, FAILED, etc.)

        Example:
            >>> if orchestrator.should_skip_task(task):
            ...     logger.info(f"Task {task.id} already completed, skipping")
            ... else:
            ...     orchestrator.execute_task(task, handler)
        """
        return task.status == TaskStatus.SUCCESS

    def execute_job_with_tasks(
        self,
        job: MarketplaceJob,
        tasks: List[MarketplaceTask],
        handlers: dict[str, Callable]
    ) -> bool:
        """
        Execute all tasks for a job with retry intelligence.

        Workflow:
        1. Sort tasks by position (1, 2, 3...)
        2. For each task:
           - Skip if status=SUCCESS (already completed)
           - Execute with handler if PENDING/FAILED
           - Stop on first failure (return False)
        3. Return True if all tasks succeed

        This enables intelligent retry:
        - First run: executes all tasks
        - Retry after failure: skips completed tasks, retries failed

        Args:
            job: Parent MarketplaceJob
            tasks: List of MarketplaceTask to execute
            handlers: Dict mapping task.description -> handler function

        Returns:
            True if all tasks succeed
            False if any task fails (stops execution)

        Example:
            >>> handlers = {
            ...     "Upload image 1/3": upload_image_handler,
            ...     "Upload image 2/3": upload_image_handler,
            ...     "Create listing": create_listing_handler,
            ... }
            >>> success = orchestrator.execute_job_with_tasks(job, tasks, handlers)
            >>> if success:
            ...     print("All tasks completed")
            ... else:
            ...     print("Job failed, can retry to skip completed tasks")
        """
        # Sort by position for ordered execution
        sorted_tasks = sorted(tasks, key=lambda t: t.position)

        for task in sorted_tasks:
            # Skip if already completed (retry intelligence)
            if self.should_skip_task(task):
                logger.info(f"Task #{task.id} ({task.description}) already completed, skipping")
                continue

            # Get handler for this task
            handler = handlers.get(task.description)
            if not handler:
                logger.error(f"No handler found for task '{task.description}'")
                return False

            # Execute task
            result = self.execute_task(task, handler)

            # Stop on failure
            if not result.success:
                logger.error(f"Job #{job.id} failed at task #{task.id}")
                return False

        logger.info(f"Job #{job.id} completed successfully")
        return True
