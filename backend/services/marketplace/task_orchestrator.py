"""
Task Orchestrator Service

Manages creation and execution of MarketplaceTask objects for retry-intelligent job processing.

Business Rules:
- Tasks are created with sequential positions (1, 2, 3...)
- Each task linked to parent MarketplaceJob via job_id
- Status starts as PENDING
- Tasks are committed in batch for performance

Created: 2026-01-15
Phase: 01-02 Task Orchestration Foundation
Author: Claude
"""

from typing import List
from sqlalchemy.orm import Session

from models.user.marketplace_job import MarketplaceJob
from models.user.marketplace_task import MarketplaceTask, TaskStatus


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
