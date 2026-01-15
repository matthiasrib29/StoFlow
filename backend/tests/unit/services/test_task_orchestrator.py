"""
Unit Tests for TaskOrchestrator

TDD implementation for retry-intelligent task execution.

Created: 2026-01-15
Phase: 01-02 Task Orchestration
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock

from models.user.marketplace_job import MarketplaceJob, JobStatus
from models.user.marketplace_task import MarketplaceTask, TaskStatus
from services.marketplace.task_orchestrator import TaskOrchestrator, TaskResult


# ===== FIXTURES =====

@pytest.fixture
def db_session():
    """Mock database session for unit tests."""
    session = Mock(spec=["query", "add", "flush", "commit", "rollback", "refresh"])
    return session


@pytest.fixture
def sample_job():
    """Sample MarketplaceJob for testing."""
    return MarketplaceJob(
        id=1,
        marketplace="vinted",
        action_type_id=1,
        product_id=101,
        status=JobStatus.PENDING,
        priority=3,
        retry_count=0,
        max_retries=3,
        created_at=datetime.now(timezone.utc)
    )


# ===== TASK 1: RED PHASE - Tests création tasks =====

class TestTaskCreation:
    """Tests for task creation with ordering."""

    def test_create_tasks_generates_ordered_tasks(self, db_session, sample_job):
        """Should create N tasks with position 1..N and status PENDING."""
        orchestrator = TaskOrchestrator(db_session)

        task_names = [
            "Validate product",
            "Upload image 1/2",
            "Upload image 2/2",
            "Create listing"
        ]

        tasks = orchestrator.create_tasks(sample_job, task_names)

        # Verify we got 4 tasks
        assert len(tasks) == 4

        # Verify each task has correct attributes
        assert tasks[0].description == "Validate product"
        assert tasks[0].position == 1
        assert tasks[0].status == TaskStatus.PENDING

        assert tasks[1].description == "Upload image 1/2"
        assert tasks[1].position == 2
        assert tasks[1].status == TaskStatus.PENDING

        assert tasks[2].description == "Upload image 2/2"
        assert tasks[2].position == 3
        assert tasks[2].status == TaskStatus.PENDING

        assert tasks[3].description == "Create listing"
        assert tasks[3].position == 4
        assert tasks[3].status == TaskStatus.PENDING

    def test_create_tasks_links_to_job(self, db_session, sample_job):
        """Should link all tasks to the parent job via job_id."""
        orchestrator = TaskOrchestrator(db_session)

        task_names = ["Task 1", "Task 2", "Task 3"]
        tasks = orchestrator.create_tasks(sample_job, task_names)

        # All tasks should have job_id set
        for task in tasks:
            assert task.job_id == sample_job.id

    def test_create_tasks_commits_to_db(self, db_session, sample_job):
        """Should add tasks to session and commit."""
        orchestrator = TaskOrchestrator(db_session)

        task_names = ["Task 1", "Task 2"]
        tasks = orchestrator.create_tasks(sample_job, task_names)

        # Verify db_session.add was called for each task
        assert db_session.add.call_count == 2

        # Verify commit was called
        db_session.commit.assert_called_once()


# ===== TASK 3: RED PHASE - Tests exécution tasks =====

class TestTaskExecution:
    """Tests for single task execution with handler."""

    def test_execute_task_marks_running_before_handler(self, db_session):
        """Should mark task RUNNING and set started_at before calling handler."""
        orchestrator = TaskOrchestrator(db_session)

        task = MarketplaceTask(
            id=1,
            job_id=1,
            description="Test task",
            position=1,
            status=TaskStatus.PENDING
        )

        # Simple handler that returns success
        def handler(t):
            # Verify task is RUNNING when handler is called
            assert t.status == TaskStatus.PROCESSING
            assert t.started_at is not None
            return {"result": "success"}

        result = orchestrator.execute_task(task, handler)

        assert result.success is True
        assert result.result == {"result": "success"}

    def test_execute_task_marks_completed_on_success(self, db_session):
        """Should mark task COMPLETED and set completed_at on success."""
        orchestrator = TaskOrchestrator(db_session)

        task = MarketplaceTask(
            id=1,
            job_id=1,
            description="Test task",
            position=1,
            status=TaskStatus.PENDING
        )

        def handler(t):
            return {"status": "ok"}

        result = orchestrator.execute_task(task, handler)

        assert result.success is True
        assert task.status == TaskStatus.SUCCESS
        assert task.completed_at is not None
        assert task.result == {"status": "ok"}

    def test_execute_task_marks_failed_on_exception(self, db_session):
        """Should mark task FAILED and store error message on exception."""
        orchestrator = TaskOrchestrator(db_session)

        task = MarketplaceTask(
            id=1,
            job_id=1,
            description="Test task",
            position=1,
            status=TaskStatus.PENDING
        )

        def failing_handler(t):
            raise ValueError("API connection failed")

        result = orchestrator.execute_task(task, failing_handler)

        assert result.success is False
        assert task.status == TaskStatus.FAILED
        assert task.completed_at is not None
        assert "API connection failed" in task.error_message

    def test_execute_task_commits_after_completion(self, db_session):
        """Should commit to DB after task finishes (success or failure)."""
        orchestrator = TaskOrchestrator(db_session)

        task = MarketplaceTask(
            id=1,
            job_id=1,
            description="Test task",
            position=1,
            status=TaskStatus.PENDING
        )

        def handler(t):
            return {"done": True}

        orchestrator.execute_task(task, handler)

        # Should commit 3 times:
        # 1. Mark RUNNING
        # 2. Mark COMPLETED
        assert db_session.commit.call_count >= 2
