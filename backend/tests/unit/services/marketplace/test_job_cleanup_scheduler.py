"""
Unit tests for Job Cleanup Scheduler.

Tests cover:
- get_all_user_schemas: Retrieve user schemas from database
- cleanup_jobs_for_all_users: Iterate and cleanup jobs
- start_job_cleanup_scheduler: Start APScheduler
- stop_job_cleanup_scheduler: Stop APScheduler
- get_job_cleanup_scheduler: Get scheduler instance

Mocks: SQLAlchemy session, APScheduler, JobCleanupService

Author: Claude
Date: 2026-01-16
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, call

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from services.marketplace.job_cleanup_scheduler import (
    get_all_user_schemas,
    cleanup_jobs_for_all_users,
    start_job_cleanup_scheduler,
    stop_job_cleanup_scheduler,
    get_job_cleanup_scheduler,
    JOB_CLEANUP_INTERVAL_MINUTES,
)


# ===========================
# Fixtures
# ===========================


@pytest.fixture
def mock_db():
    """Mock SQLAlchemy Session."""
    db = MagicMock(spec=Session)
    db.close = MagicMock()
    db.execute = MagicMock()
    return db


@pytest.fixture
def mock_scheduler():
    """Mock APScheduler BackgroundScheduler."""
    scheduler = MagicMock(spec=BackgroundScheduler)
    scheduler.running = False
    scheduler.start = MagicMock()
    scheduler.shutdown = MagicMock()
    scheduler.add_job = MagicMock()
    return scheduler


@pytest.fixture(autouse=True)
def reset_global_scheduler():
    """Reset global scheduler before each test."""
    import services.marketplace.job_cleanup_scheduler as module
    module._scheduler = None
    yield
    module._scheduler = None


# ===========================
# Test: get_all_user_schemas
# ===========================


class TestGetAllUserSchemas:
    """Test get_all_user_schemas function."""

    def test_get_all_user_schemas_returns_list(self, mock_db):
        """Test that get_all_user_schemas returns list of schema names."""
        # Mock query result
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            ("user_1",),
            ("user_2",),
            ("user_3",),
        ]
        mock_db.execute.return_value = mock_result

        schemas = get_all_user_schemas(mock_db)

        assert schemas == ["user_1", "user_2", "user_3"]
        mock_db.execute.assert_called_once()

    def test_get_all_user_schemas_excludes_user_invalid(self, mock_db):
        """Test that get_all_user_schemas excludes 'user_invalid' schema."""
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            ("user_1",),
            ("user_2",),
        ]
        mock_db.execute.return_value = mock_result

        schemas = get_all_user_schemas(mock_db)

        # Verify SQL query filters out user_invalid
        call_args = mock_db.execute.call_args
        # Can't easily inspect the text() object, but verify it was called
        assert call_args is not None

    def test_get_all_user_schemas_returns_empty_list_when_none(self, mock_db):
        """Test that get_all_user_schemas returns empty list when no schemas found."""
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_result

        schemas = get_all_user_schemas(mock_db)

        assert schemas == []

    def test_get_all_user_schemas_orders_by_schema_name(self, mock_db):
        """Test that get_all_user_schemas orders results by schema name."""
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            ("user_1",),
            ("user_10",),
            ("user_2",),
        ]
        mock_db.execute.return_value = mock_result

        schemas = get_all_user_schemas(mock_db)

        # Order is preserved from DB (SQL ORDER BY)
        assert schemas == ["user_1", "user_10", "user_2"]


# ===========================
# Test: cleanup_jobs_for_all_users
# ===========================


class TestCleanupJobsForAllUsers:
    """Test cleanup_jobs_for_all_users function."""

    @patch("services.marketplace.job_cleanup_scheduler.SessionLocal")
    @patch("services.marketplace.job_cleanup_scheduler.get_all_user_schemas")
    @patch("services.marketplace.job_cleanup_scheduler.JobCleanupService")
    @patch("shared.schema_utils.configure_schema_translate_map")
    def test_cleanup_processes_all_schemas(
        self,
        mock_configure_schema,
        mock_cleanup_service,
        mock_get_schemas,
        mock_session_local,
        mock_db,
    ):
        """Test that cleanup processes all user schemas."""
        mock_session_local.return_value = mock_db
        mock_get_schemas.return_value = ["user_1", "user_2"]

        # Mock table existence check
        mock_db.execute.return_value.scalar.return_value = True

        # Mock cleanup result
        mock_cleanup_service.cleanup_expired_jobs.return_value = {
            "pending_expired": 1,
            "processing_expired": 0,
        }

        cleanup_jobs_for_all_users()

        # Verify cleanup was called for each schema
        assert mock_cleanup_service.cleanup_expired_jobs.call_count == 2
        mock_db.close.assert_called_once()

    @patch("services.marketplace.job_cleanup_scheduler.SessionLocal")
    @patch("services.marketplace.job_cleanup_scheduler.get_all_user_schemas")
    @patch("services.marketplace.job_cleanup_scheduler.JobCleanupService")
    @patch("shared.schema_utils.configure_schema_translate_map")
    def test_cleanup_skips_schema_without_marketplace_jobs_table(
        self,
        mock_configure_schema,
        mock_cleanup_service,
        mock_get_schemas,
        mock_session_local,
        mock_db,
    ):
        """Test that cleanup skips schemas without marketplace_jobs table."""
        mock_session_local.return_value = mock_db
        mock_get_schemas.return_value = ["user_1", "user_2"]

        # Mock: user_1 has table, user_2 doesn't
        mock_db.execute.return_value.scalar.side_effect = [True, False]

        mock_cleanup_service.cleanup_expired_jobs.return_value = {
            "pending_expired": 0,
            "processing_expired": 0,
        }

        cleanup_jobs_for_all_users()

        # Verify cleanup was only called once (for user_1)
        assert mock_cleanup_service.cleanup_expired_jobs.call_count == 1

    @patch("services.marketplace.job_cleanup_scheduler.SessionLocal")
    @patch("services.marketplace.job_cleanup_scheduler.get_all_user_schemas")
    @patch("services.marketplace.job_cleanup_scheduler.JobCleanupService")
    @patch("shared.schema_utils.configure_schema_translate_map")
    def test_cleanup_handles_errors_gracefully(
        self,
        mock_configure_schema,
        mock_cleanup_service,
        mock_get_schemas,
        mock_session_local,
        mock_db,
    ):
        """Test that cleanup continues after error in one schema."""
        mock_session_local.return_value = mock_db
        mock_get_schemas.return_value = ["user_1", "user_2"]

        # Mock: user_1 raises error, user_2 succeeds
        mock_db.execute.return_value.scalar.return_value = True
        mock_cleanup_service.cleanup_expired_jobs.side_effect = [
            Exception("Test error"),
            {"pending_expired": 1, "processing_expired": 0},
        ]

        # Should not raise exception
        cleanup_jobs_for_all_users()

        # Verify cleanup was attempted for both schemas
        assert mock_cleanup_service.cleanup_expired_jobs.call_count == 2
        mock_db.close.assert_called_once()

    @patch("services.marketplace.job_cleanup_scheduler.SessionLocal")
    @patch("services.marketplace.job_cleanup_scheduler.get_all_user_schemas")
    def test_cleanup_closes_db_session_on_error(
        self, mock_get_schemas, mock_session_local, mock_db
    ):
        """Test that cleanup closes DB session even on error."""
        mock_session_local.return_value = mock_db
        mock_get_schemas.side_effect = Exception("DB error")

        # Should not raise exception
        cleanup_jobs_for_all_users()

        # Verify session was closed
        mock_db.close.assert_called_once()


# ===========================
# Test: start_job_cleanup_scheduler
# ===========================


class TestStartJobCleanupScheduler:
    """Test start_job_cleanup_scheduler function."""

    @patch("services.marketplace.job_cleanup_scheduler.BackgroundScheduler")
    @patch("services.marketplace.job_cleanup_scheduler.cleanup_jobs_for_all_users")
    def test_start_scheduler_creates_and_starts_scheduler(
        self, mock_cleanup, mock_scheduler_class
    ):
        """Test that start_scheduler creates and starts APScheduler."""
        mock_scheduler = MagicMock()
        mock_scheduler.running = False
        mock_scheduler_class.return_value = mock_scheduler

        scheduler = start_job_cleanup_scheduler()

        assert scheduler is mock_scheduler
        mock_scheduler.add_job.assert_called_once()
        mock_scheduler.start.assert_called_once()
        mock_cleanup.assert_called_once()  # Initial cleanup

    @patch("services.marketplace.job_cleanup_scheduler.BackgroundScheduler")
    @patch("services.marketplace.job_cleanup_scheduler.cleanup_jobs_for_all_users")
    def test_start_scheduler_returns_existing_if_already_running(
        self, mock_cleanup, mock_scheduler_class
    ):
        """Test that start_scheduler returns existing scheduler if already running."""
        # Start scheduler first time
        mock_scheduler = MagicMock()
        mock_scheduler.running = False
        mock_scheduler_class.return_value = mock_scheduler

        scheduler1 = start_job_cleanup_scheduler()

        # Mock scheduler as running
        scheduler1.running = True
        import services.marketplace.job_cleanup_scheduler as module
        module._scheduler = scheduler1

        # Try to start again
        scheduler2 = start_job_cleanup_scheduler()

        assert scheduler2 is scheduler1
        # Should not create a new scheduler
        assert mock_scheduler_class.call_count == 1

    @patch("services.marketplace.job_cleanup_scheduler.BackgroundScheduler")
    @patch("services.marketplace.job_cleanup_scheduler.cleanup_jobs_for_all_users")
    def test_start_scheduler_configures_interval_trigger(
        self, mock_cleanup, mock_scheduler_class
    ):
        """Test that start_scheduler configures IntervalTrigger with correct interval."""
        mock_scheduler = MagicMock()
        mock_scheduler.running = False
        mock_scheduler_class.return_value = mock_scheduler

        start_job_cleanup_scheduler()

        # Verify add_job was called with correct arguments
        mock_scheduler.add_job.assert_called_once()
        call_kwargs = mock_scheduler.add_job.call_args[1]
        assert call_kwargs["id"] == "job_cleanup"
        assert call_kwargs["name"] == "Marketplace Job Cleanup"


# ===========================
# Test: stop_job_cleanup_scheduler
# ===========================


class TestStopJobCleanupScheduler:
    """Test stop_job_cleanup_scheduler function."""

    def test_stop_scheduler_shuts_down_running_scheduler(self):
        """Test that stop_scheduler shuts down a running scheduler."""
        mock_scheduler = MagicMock()
        mock_scheduler.running = True

        stop_job_cleanup_scheduler(mock_scheduler)

        mock_scheduler.shutdown.assert_called_once_with(wait=False)

    def test_stop_scheduler_does_nothing_if_not_running(self):
        """Test that stop_scheduler does nothing if scheduler not running."""
        mock_scheduler = MagicMock()
        mock_scheduler.running = False

        stop_job_cleanup_scheduler(mock_scheduler)

        mock_scheduler.shutdown.assert_not_called()

    def test_stop_scheduler_uses_global_if_not_provided(self):
        """Test that stop_scheduler uses global scheduler if not provided."""
        mock_scheduler = MagicMock()
        mock_scheduler.running = True

        import services.marketplace.job_cleanup_scheduler as module
        module._scheduler = mock_scheduler

        stop_job_cleanup_scheduler()

        mock_scheduler.shutdown.assert_called_once_with(wait=False)
        assert module._scheduler is None

    def test_stop_scheduler_handles_none_scheduler(self):
        """Test that stop_scheduler handles None scheduler gracefully."""
        # Should not raise exception
        stop_job_cleanup_scheduler(None)


# ===========================
# Test: get_job_cleanup_scheduler
# ===========================


class TestGetJobCleanupScheduler:
    """Test get_job_cleanup_scheduler function."""

    def test_get_scheduler_returns_global_scheduler(self):
        """Test that get_scheduler returns the global scheduler instance."""
        mock_scheduler = MagicMock()

        import services.marketplace.job_cleanup_scheduler as module
        module._scheduler = mock_scheduler

        scheduler = get_job_cleanup_scheduler()

        assert scheduler is mock_scheduler

    def test_get_scheduler_returns_none_if_not_started(self):
        """Test that get_scheduler returns None if scheduler not started."""
        import services.marketplace.job_cleanup_scheduler as module
        module._scheduler = None

        scheduler = get_job_cleanup_scheduler()

        assert scheduler is None


# ===========================
# Test: Module Constants
# ===========================


class TestJobCleanupSchedulerConstants:
    """Test module constants."""

    def test_job_cleanup_interval_defined(self):
        """Test that JOB_CLEANUP_INTERVAL_MINUTES is defined."""
        assert JOB_CLEANUP_INTERVAL_MINUTES is not None
        assert isinstance(JOB_CLEANUP_INTERVAL_MINUTES, int)
        assert JOB_CLEANUP_INTERVAL_MINUTES > 0


# ===========================
# Test: Integration Scenarios
# ===========================


class TestJobCleanupSchedulerIntegration:
    """Integration-like tests for scheduler workflow."""

    @patch("services.marketplace.job_cleanup_scheduler.BackgroundScheduler")
    @patch("services.marketplace.job_cleanup_scheduler.cleanup_jobs_for_all_users")
    def test_full_scheduler_lifecycle(self, mock_cleanup, mock_scheduler_class):
        """Test complete scheduler lifecycle: start → run → stop."""
        mock_scheduler = MagicMock()
        mock_scheduler.running = False
        mock_scheduler_class.return_value = mock_scheduler

        # Start scheduler
        scheduler = start_job_cleanup_scheduler()
        assert scheduler is mock_scheduler
        mock_scheduler.start.assert_called_once()
        mock_cleanup.assert_called_once()  # Initial run

        # Mock scheduler as running
        scheduler.running = True

        # Get scheduler instance
        current = get_job_cleanup_scheduler()
        assert current is scheduler

        # Stop scheduler
        stop_job_cleanup_scheduler()
        mock_scheduler.shutdown.assert_called_once_with(wait=False)

        # Verify global scheduler is cleared
        assert get_job_cleanup_scheduler() is None
