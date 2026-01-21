"""
Unit Tests for JobExecutor

Tests for job execution, retry logic, cancellation, and advisory locks.

Created: 2026-01-20
"""

import asyncio
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from models.user.marketplace_job import MarketplaceJob, JobStatus
from worker.job_executor import JobExecutor
from worker.config import WorkerConfig


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_db():
    """Mock SQLAlchemy session."""
    db = MagicMock()
    db.commit = MagicMock()
    db.rollback = MagicMock()
    db.flush = MagicMock()
    return db


@pytest.fixture
def config():
    """Create test worker config."""
    return WorkerConfig(
        user_id=1,
        max_concurrent_jobs=4,
        marketplace_filter=None,
    )


@pytest.fixture
def mock_job():
    """Create a mock MarketplaceJob."""
    return MarketplaceJob(
        id=1,
        marketplace="vinted",
        action_type_id=1,
        product_id=123,
        status=JobStatus.PENDING,
        priority=3,
        retry_count=0,
        max_retries=3,
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_action_type():
    """Create a mock action type."""
    action_type = MagicMock()
    action_type.id = 1
    action_type.code = "publish"
    action_type.name = "Publish Product"
    return action_type


# =============================================================================
# Test: JobExecutor Initialization
# =============================================================================


class TestJobExecutorInit:
    """Test JobExecutor initialization."""

    @patch('worker.job_executor.MarketplaceJobService')
    def test_init_creates_job_service(self, mock_service_class, config, mock_db):
        """Should create MarketplaceJobService on init."""
        executor = JobExecutor(config, mock_db)
        mock_service_class.assert_called_once_with(mock_db)

    @patch('worker.job_executor.MarketplaceJobService')
    def test_init_stores_config(self, mock_service_class, config, mock_db):
        """Should store config reference."""
        executor = JobExecutor(config, mock_db)
        assert executor.config == config

    @patch('worker.job_executor.MarketplaceJobService')
    def test_init_stores_db(self, mock_service_class, config, mock_db):
        """Should store db reference."""
        executor = JobExecutor(config, mock_db)
        assert executor.db == mock_db

    @patch('worker.job_executor.MarketplaceJobService')
    def test_init_loads_handlers(self, mock_service_class, config, mock_db):
        """Should attempt to load handlers on init."""
        with patch.object(JobExecutor, '_load_handlers') as mock_load:
            executor = JobExecutor(config, mock_db)
            mock_load.assert_called_once()


# =============================================================================
# Test: Job Claiming
# =============================================================================


class TestJobExecutorClaimJob:
    """Test claim_next_job method."""

    @patch('worker.job_executor.MarketplaceJobService')
    def test_claim_next_job_calls_service(self, mock_service_class, config, mock_db, mock_job):
        """Should call service.get_next_pending_job."""
        mock_service = MagicMock()
        mock_service.get_next_pending_job.return_value = mock_job
        mock_service_class.return_value = mock_service

        executor = JobExecutor(config, mock_db)
        job = executor.claim_next_job()

        mock_service.get_next_pending_job.assert_called_once_with(
            marketplace=config.marketplace_filter
        )
        assert job == mock_job

    @patch('worker.job_executor.MarketplaceJobService')
    def test_claim_next_job_returns_none_when_empty(self, mock_service_class, config, mock_db):
        """Should return None when no jobs available."""
        mock_service = MagicMock()
        mock_service.get_next_pending_job.return_value = None
        mock_service_class.return_value = mock_service

        executor = JobExecutor(config, mock_db)
        job = executor.claim_next_job()

        assert job is None

    @patch('worker.job_executor.MarketplaceJobService')
    def test_claim_job_with_marketplace_filter(self, mock_service_class, mock_db, mock_job):
        """Should pass marketplace filter to service."""
        config = WorkerConfig(user_id=1, marketplace_filter="ebay")
        mock_service = MagicMock()
        mock_service.get_next_pending_job.return_value = mock_job
        mock_service_class.return_value = mock_service

        executor = JobExecutor(config, mock_db)
        executor.claim_next_job()

        mock_service.get_next_pending_job.assert_called_once_with(marketplace="ebay")


# =============================================================================
# Test: Job Execution
# =============================================================================


class TestJobExecutorExecuteJob:
    """Test execute_job method."""

    @pytest.mark.asyncio
    @patch('worker.job_executor.MarketplaceJobService')
    @patch('worker.job_executor.AdvisoryLockHelper')
    async def test_execute_job_acquires_work_lock(
        self, mock_lock_helper, mock_service_class, config, mock_db, mock_job, mock_action_type
    ):
        """Should try to acquire work lock before execution."""
        mock_service = MagicMock()
        mock_service.get_action_type_by_id.return_value = mock_action_type
        mock_service.start_job.return_value = mock_job
        mock_service_class.return_value = mock_service

        mock_lock_helper.try_acquire_work_lock.return_value = False  # Lock failed

        executor = JobExecutor(config, mock_db)
        result = await executor.execute_job(mock_job)

        mock_lock_helper.try_acquire_work_lock.assert_called_once_with(mock_db, mock_job.id)
        assert result["success"] is False
        assert result["status"] == "skipped"
        assert result["reason"] == "could_not_acquire_work_lock"

    @pytest.mark.asyncio
    @patch('worker.job_executor.MarketplaceJobService')
    @patch('worker.job_executor.AdvisoryLockHelper')
    async def test_execute_job_checks_cancel_before_start(
        self, mock_lock_helper, mock_service_class, config, mock_db, mock_job, mock_action_type
    ):
        """Should check for cancellation before starting handler."""
        mock_service = MagicMock()
        mock_service.get_action_type_by_id.return_value = mock_action_type
        mock_service.start_job.return_value = mock_job
        mock_service_class.return_value = mock_service

        mock_lock_helper.try_acquire_work_lock.return_value = True
        mock_lock_helper.is_cancel_signaled.return_value = True  # Cancelled

        executor = JobExecutor(config, mock_db)
        result = await executor.execute_job(mock_job)

        assert result["success"] is False
        assert result["status"] == "cancelled"
        assert result["reason"] == "cancelled_before_start"
        mock_service.mark_job_cancelled.assert_called_once_with(mock_job.id)

    @pytest.mark.asyncio
    @patch('worker.job_executor.MarketplaceJobService')
    @patch('worker.job_executor.AdvisoryLockHelper')
    async def test_execute_job_releases_lock_on_success(
        self, mock_lock_helper, mock_service_class, config, mock_db, mock_job, mock_action_type
    ):
        """Should release work lock after successful execution."""
        mock_service = MagicMock()
        mock_service.get_action_type_by_id.return_value = mock_action_type
        mock_service.start_job.return_value = mock_job
        mock_service_class.return_value = mock_service

        mock_lock_helper.try_acquire_work_lock.return_value = True
        mock_lock_helper.is_cancel_signaled.return_value = False

        # Mock handler
        mock_handler = AsyncMock()
        mock_handler.execute.return_value = {"success": True, "vinted_id": "abc123"}

        executor = JobExecutor(config, mock_db)
        executor._handlers = {"publish_vinted": lambda **kwargs: mock_handler}

        result = await executor.execute_job(mock_job)

        mock_lock_helper.release_work_lock.assert_called_once_with(mock_db, mock_job.id)
        assert result["success"] is True

    @pytest.mark.asyncio
    @patch('worker.job_executor.MarketplaceJobService')
    @patch('worker.job_executor.AdvisoryLockHelper')
    async def test_execute_job_releases_lock_on_failure(
        self, mock_lock_helper, mock_service_class, config, mock_db, mock_job, mock_action_type
    ):
        """Should release work lock after failed execution."""
        mock_service = MagicMock()
        mock_service.get_action_type_by_id.return_value = mock_action_type
        mock_service.start_job.return_value = mock_job
        mock_service.increment_retry.return_value = (mock_job, False)  # No more retries
        mock_service_class.return_value = mock_service

        mock_lock_helper.try_acquire_work_lock.return_value = True
        mock_lock_helper.is_cancel_signaled.return_value = False

        # Mock handler that fails
        mock_handler = AsyncMock()
        mock_handler.execute.return_value = {"success": False, "error": "API error"}

        executor = JobExecutor(config, mock_db)
        executor._handlers = {"publish_vinted": lambda **kwargs: mock_handler}

        result = await executor.execute_job(mock_job)

        mock_lock_helper.release_work_lock.assert_called_once_with(mock_db, mock_job.id)
        assert result["success"] is False


# =============================================================================
# Test: Retry Logic
# =============================================================================


class TestJobExecutorRetryLogic:
    """Test retry logic in failure handling."""

    @pytest.mark.asyncio
    @patch('worker.job_executor.MarketplaceJobService')
    @patch('worker.job_executor.AdvisoryLockHelper')
    async def test_handle_failure_with_retry(
        self, mock_lock_helper, mock_service_class, config, mock_db, mock_job, mock_action_type
    ):
        """Should reset job to PENDING if retries available."""
        mock_job.retry_count = 1  # After increment
        mock_service = MagicMock()
        mock_service.get_action_type_by_id.return_value = mock_action_type
        mock_service.start_job.return_value = mock_job
        mock_service.increment_retry.return_value = (mock_job, True)  # Can retry
        mock_service_class.return_value = mock_service

        mock_lock_helper.try_acquire_work_lock.return_value = True
        mock_lock_helper.is_cancel_signaled.return_value = False

        # Mock handler that fails
        mock_handler = AsyncMock()
        mock_handler.execute.return_value = {"success": False, "error": "Timeout"}

        executor = JobExecutor(config, mock_db)
        executor._handlers = {"publish_vinted": lambda **kwargs: mock_handler}

        result = await executor.execute_job(mock_job)

        assert result["success"] is False
        assert result["will_retry"] is True
        assert mock_job.status == JobStatus.PENDING

    @pytest.mark.asyncio
    @patch('worker.job_executor.MarketplaceJobService')
    @patch('worker.job_executor.AdvisoryLockHelper')
    async def test_handle_failure_no_retry(
        self, mock_lock_helper, mock_service_class, config, mock_db, mock_job, mock_action_type
    ):
        """Should mark job as FAILED if no retries left."""
        mock_service = MagicMock()
        mock_service.get_action_type_by_id.return_value = mock_action_type
        mock_service.start_job.return_value = mock_job
        mock_service.increment_retry.return_value = (mock_job, False)  # No more retries
        mock_service_class.return_value = mock_service

        mock_lock_helper.try_acquire_work_lock.return_value = True
        mock_lock_helper.is_cancel_signaled.return_value = False

        # Mock handler that fails
        mock_handler = AsyncMock()
        mock_handler.execute.return_value = {"success": False, "error": "Fatal error"}

        executor = JobExecutor(config, mock_db)
        executor._handlers = {"publish_vinted": lambda **kwargs: mock_handler}

        result = await executor.execute_job(mock_job)

        assert result["success"] is False
        assert result["will_retry"] is False
        mock_service.fail_job.assert_called_once()


# =============================================================================
# Test: Unknown Handler
# =============================================================================


class TestJobExecutorUnknownHandler:
    """Test handling of unknown action codes."""

    @pytest.mark.asyncio
    @patch('worker.job_executor.MarketplaceJobService')
    @patch('worker.job_executor.AdvisoryLockHelper')
    async def test_unknown_handler_fails_job(
        self, mock_lock_helper, mock_service_class, config, mock_db, mock_job, mock_action_type
    ):
        """Should fail job if handler not found."""
        mock_action_type.code = "unknown_action"
        mock_service = MagicMock()
        mock_service.get_action_type_by_id.return_value = mock_action_type
        mock_service.start_job.return_value = mock_job
        mock_service.increment_retry.return_value = (mock_job, False)
        mock_service_class.return_value = mock_service

        mock_lock_helper.try_acquire_work_lock.return_value = True
        mock_lock_helper.is_cancel_signaled.return_value = False

        executor = JobExecutor(config, mock_db)
        executor._handlers = {}  # No handlers

        result = await executor.execute_job(mock_job)

        assert result["success"] is False
        assert "unknown_action_vinted" in result.get("error", "")


# =============================================================================
# Test: Expire Old Jobs
# =============================================================================


class TestJobExecutorExpireOldJobs:
    """Test expire_old_jobs method."""

    @patch('worker.job_executor.MarketplaceJobService')
    def test_expire_old_jobs_calls_service(self, mock_service_class, config, mock_db):
        """Should call service.expire_old_jobs."""
        mock_service = MagicMock()
        mock_service.expire_old_jobs.return_value = 5
        mock_service_class.return_value = mock_service

        executor = JobExecutor(config, mock_db)
        count = executor.expire_old_jobs()

        mock_service.expire_old_jobs.assert_called_once_with(
            marketplace=config.marketplace_filter
        )
        assert count == 5
        mock_db.commit.assert_called_once()

    @patch('worker.job_executor.MarketplaceJobService')
    def test_expire_old_jobs_no_commit_when_zero(self, mock_service_class, config, mock_db):
        """Should not commit when no jobs expired."""
        mock_service = MagicMock()
        mock_service.expire_old_jobs.return_value = 0
        mock_service_class.return_value = mock_service

        executor = JobExecutor(config, mock_db)
        count = executor.expire_old_jobs()

        assert count == 0
        mock_db.commit.assert_not_called()


# =============================================================================
# Test: Force Cancel Stale Jobs
# =============================================================================


class TestJobExecutorForceCancelStaleJobs:
    """Test force_cancel_stale_jobs method."""

    @patch('worker.job_executor.MarketplaceJobService')
    def test_force_cancel_stale_jobs_marks_as_cancelled(self, mock_service_class, config, mock_db):
        """Should mark stale jobs as cancelled."""
        # Create stale jobs with cancel_requested=True
        stale_job1 = MarketplaceJob(
            id=1,
            marketplace="vinted",
            action_type_id=1,
            status=JobStatus.RUNNING,
            cancel_requested=True,
        )
        stale_job2 = MarketplaceJob(
            id=2,
            marketplace="vinted",
            action_type_id=1,
            status=JobStatus.RUNNING,
            cancel_requested=True,
        )

        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        # Mock query chain
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [stale_job1, stale_job2]
        mock_db.query.return_value = mock_query

        executor = JobExecutor(config, mock_db)
        count = executor.force_cancel_stale_jobs()

        assert count == 2
        assert mock_service.mark_job_cancelled.call_count == 2
        mock_db.commit.assert_called_once()

    @patch('worker.job_executor.MarketplaceJobService')
    def test_force_cancel_stale_jobs_handles_empty_list(self, mock_service_class, config, mock_db):
        """Should handle case when no stale jobs."""
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        executor = JobExecutor(config, mock_db)
        count = executor.force_cancel_stale_jobs()

        assert count == 0
        mock_db.commit.assert_not_called()


# =============================================================================
# Test: Safe Rollback
# =============================================================================


class TestJobExecutorSafeRollback:
    """Test _safe_rollback method."""

    @patch('worker.job_executor.MarketplaceJobService')
    def test_safe_rollback_calls_db_rollback(self, mock_service_class, config, mock_db):
        """Should call db.rollback()."""
        executor = JobExecutor(config, mock_db)
        executor._safe_rollback()

        mock_db.rollback.assert_called_once()

    @patch('worker.job_executor.MarketplaceJobService')
    def test_safe_rollback_handles_exception(self, mock_service_class, config, mock_db):
        """Should not raise on rollback exception."""
        mock_db.rollback.side_effect = Exception("Rollback failed")

        executor = JobExecutor(config, mock_db)
        # Should not raise
        executor._safe_rollback()
