"""
Unit Tests for BaseJobHandler TaskOrchestrator Integration

Tests the TaskOrchestrator integration added in Phase 2.

Created: 2026-01-15
Phase: 02-01 Base Handler Unification
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from models.user.marketplace_job import MarketplaceJob, JobStatus
from models.user.marketplace_task import MarketplaceTask, TaskStatus
from services.vinted.jobs.base_job_handler import BaseJobHandler
from services.marketplace.task_orchestrator import TaskOrchestrator


# ===== TEST HANDLER IMPLEMENTATION =====

class ConcreteTestHandler(BaseJobHandler):
    """
    Concrete implementation of BaseJobHandler for testing.

    Implements the required abstract methods create_tasks() and execute().
    """

    ACTION_CODE = "test"

    def create_tasks(self, job: MarketplaceJob) -> list[str]:
        """Return a fixed list of 3 tasks for testing."""
        return [
            "Validate product data",
            "Upload image 1/2",
            "Upload image 2/2"
        ]

    async def execute(self, job: MarketplaceJob) -> dict:
        """Not used in these tests."""
        return {"success": True}


# ===== FIXTURES =====

@pytest.fixture
def db_session():
    """Mock database session for unit tests."""
    session = Mock(spec=["query", "add", "flush", "commit", "rollback", "refresh"])

    # Mock query().filter().all() for MarketplaceTask
    query_mock = Mock()
    filter_mock = Mock()
    filter_mock.all.return_value = []
    query_mock.filter.return_value = filter_mock
    session.query.return_value = query_mock

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


@pytest.fixture
def handler(db_session):
    """Instantiate test handler."""
    return ConcreteTestHandler(db=db_session, shop_id=123, job_id=1)


# ===== TESTS =====

class TestBaseJobHandlerOrchestration:
    """Tests for BaseJobHandler TaskOrchestrator integration."""

    def test_orchestrator_initialized_in_constructor(self, handler, db_session):
        """Should create TaskOrchestrator instance in __init__."""
        assert hasattr(handler, 'orchestrator')
        assert isinstance(handler.orchestrator, TaskOrchestrator)
        assert handler.orchestrator.db == db_session

    @patch.object(TaskOrchestrator, 'create_tasks')
    @patch.object(TaskOrchestrator, 'execute_job_with_tasks')
    def test_execute_with_tasks_creates_tasks_on_first_run(
        self,
        mock_execute,
        mock_create,
        handler,
        sample_job,
        db_session
    ):
        """Should create tasks using handler's create_tasks() method on first run."""
        # Setup: No existing tasks (first run)
        query_mock = db_session.query.return_value
        query_mock.filter.return_value.all.return_value = []

        # Mock task creation
        created_tasks = [
            MarketplaceTask(
                id=i,
                job_id=sample_job.id,
                description=name,
                position=i,
                status=TaskStatus.SUCCESS
            )
            for i, name in enumerate(handler.create_tasks(sample_job), start=1)
        ]
        mock_create.return_value = created_tasks
        mock_execute.return_value = True

        # Execute
        result = handler.execute_with_tasks(sample_job, {})

        # Verify create_tasks was called with correct args
        mock_create.assert_called_once()
        call_args = mock_create.call_args
        assert call_args[0][0] == sample_job
        assert call_args[0][1] == [
            "Validate product data",
            "Upload image 1/2",
            "Upload image 2/2"
        ]

    @patch.object(TaskOrchestrator, 'execute_job_with_tasks')
    def test_execute_with_tasks_reuses_existing_tasks_on_retry(
        self,
        mock_execute,
        handler,
        sample_job,
        db_session
    ):
        """Should not recreate tasks if they already exist (retry scenario)."""
        # Setup: Existing tasks (retry)
        existing_tasks = [
            MarketplaceTask(
                id=1,
                job_id=sample_job.id,
                description="Validate product data",
                position=1,
                status=TaskStatus.SUCCESS
            ),
            MarketplaceTask(
                id=2,
                job_id=sample_job.id,
                description="Upload image 1/2",
                position=2,
                status=TaskStatus.FAILED
            ),
            MarketplaceTask(
                id=3,
                job_id=sample_job.id,
                description="Upload image 2/2",
                position=3,
                status=TaskStatus.PENDING
            )
        ]

        query_mock = db_session.query.return_value
        query_mock.filter.return_value.all.return_value = existing_tasks
        mock_execute.return_value = True

        # Execute
        with patch.object(TaskOrchestrator, 'create_tasks') as mock_create:
            result = handler.execute_with_tasks(sample_job, {})

            # Verify create_tasks was NOT called (tasks already exist)
            mock_create.assert_not_called()

    @patch.object(TaskOrchestrator, 'create_tasks')
    @patch.object(TaskOrchestrator, 'execute_job_with_tasks')
    def test_execute_with_tasks_returns_success_when_all_tasks_succeed(
        self,
        mock_execute,
        mock_create,
        handler,
        sample_job,
        db_session
    ):
        """Should return success=True when all tasks complete."""
        # Setup: All tasks succeed
        successful_tasks = [
            MarketplaceTask(
                id=i,
                job_id=sample_job.id,
                description=name,
                position=i,
                status=TaskStatus.SUCCESS
            )
            for i, name in enumerate(handler.create_tasks(sample_job), start=1)
        ]

        query_mock = db_session.query.return_value
        query_mock.filter.return_value.all.return_value = []

        mock_create.return_value = successful_tasks
        mock_execute.return_value = True  # All tasks succeeded

        # Execute
        result = handler.execute_with_tasks(sample_job, {})

        # Verify result
        assert result["success"] is True
        assert result["tasks_completed"] == 3
        assert result["tasks_total"] == 3
        assert "error" not in result

    @patch.object(TaskOrchestrator, 'create_tasks')
    @patch.object(TaskOrchestrator, 'execute_job_with_tasks')
    def test_execute_with_tasks_returns_failure_with_error_message(
        self,
        mock_execute,
        mock_create,
        handler,
        sample_job,
        db_session
    ):
        """Should return success=False with error when task fails."""
        # Setup: Task 2 fails
        failed_tasks = [
            MarketplaceTask(
                id=1,
                job_id=sample_job.id,
                description="Validate product data",
                position=1,
                status=TaskStatus.SUCCESS
            ),
            MarketplaceTask(
                id=2,
                job_id=sample_job.id,
                description="Upload image 1/2",
                position=2,
                status=TaskStatus.FAILED,
                error_message="Connection timeout"
            ),
            MarketplaceTask(
                id=3,
                job_id=sample_job.id,
                description="Upload image 2/2",
                position=3,
                status=TaskStatus.PENDING
            )
        ]

        query_mock = db_session.query.return_value
        query_mock.filter.return_value.all.return_value = []

        mock_create.return_value = failed_tasks
        mock_execute.return_value = False  # Task failed

        # Execute
        result = handler.execute_with_tasks(sample_job, {})

        # Verify result
        assert result["success"] is False
        assert result["tasks_completed"] == 1  # Only task 1 succeeded
        assert result["tasks_total"] == 3
        assert result["error"] == "Connection timeout"

    @patch.object(TaskOrchestrator, 'create_tasks')
    @patch.object(TaskOrchestrator, 'execute_job_with_tasks')
    def test_execute_with_tasks_counts_completed_tasks_correctly(
        self,
        mock_execute,
        mock_create,
        handler,
        sample_job,
        db_session
    ):
        """Should count tasks_completed and tasks_total accurately."""
        # Setup: 2 out of 3 tasks completed
        partial_tasks = [
            MarketplaceTask(
                id=1,
                job_id=sample_job.id,
                description="Validate product data",
                position=1,
                status=TaskStatus.SUCCESS
            ),
            MarketplaceTask(
                id=2,
                job_id=sample_job.id,
                description="Upload image 1/2",
                position=2,
                status=TaskStatus.SUCCESS
            ),
            MarketplaceTask(
                id=3,
                job_id=sample_job.id,
                description="Upload image 2/2",
                position=3,
                status=TaskStatus.FAILED,
                error_message="API error"
            )
        ]

        query_mock = db_session.query.return_value
        query_mock.filter.return_value.all.return_value = []

        mock_create.return_value = partial_tasks
        mock_execute.return_value = False

        # Execute
        result = handler.execute_with_tasks(sample_job, {})

        # Verify counts
        assert result["tasks_completed"] == 2
        assert result["tasks_total"] == 3
        assert result["success"] is False
