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
from services.marketplace.task_orchestrator import TaskOrchestrator


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
