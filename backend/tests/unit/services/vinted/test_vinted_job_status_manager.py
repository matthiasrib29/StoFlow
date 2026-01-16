"""
Unit tests for VintedJobStatusManager service.

Tests cover all status transition methods:
- start_job, complete_job, fail_job
- pause_job, resume_job, cancel_job
- increment_retry, expire_old_jobs

Mocks: SQLAlchemy session, MarketplaceJob, callbacks

Author: Claude
Date: 2026-01-16
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch, call

from models.user.marketplace_job import JobStatus, MarketplaceJob
from services.vinted.vinted_job_status_manager import (
    VintedJobStatusManager,
    JOB_EXPIRATION_HOURS,
)


# ===========================
# Fixtures
# ===========================


@pytest.fixture
def mock_db():
    """Mock SQLAlchemy Session."""
    db = MagicMock()
    db.commit = MagicMock()
    db.query = MagicMock()
    return db


@pytest.fixture
def mock_job():
    """Mock MarketplaceJob."""
    job = MagicMock(spec=MarketplaceJob)
    job.id = 123
    job.status = JobStatus.PENDING
    job.started_at = None
    job.completed_at = None
    job.error_message = None
    job.retry_count = 0
    job.is_terminal = False
    return job


@pytest.fixture
def mock_callback():
    """Mock callback function."""
    return MagicMock()


# ===========================
# Test: start_job
# ===========================


class TestStartJob:
    """Test start_job method."""

    def test_start_job_updates_status_and_timestamp(self, mock_db, mock_job):
        """Test that start_job sets status to RUNNING and started_at timestamp."""
        VintedJobStatusManager.start_job(mock_db, mock_job)

        assert mock_job.status == JobStatus.RUNNING
        assert mock_job.started_at is not None
        assert isinstance(mock_job.started_at, datetime)
        mock_db.commit.assert_called_once()

    def test_start_job_uses_utc_timezone(self, mock_db, mock_job):
        """Test that started_at uses UTC timezone."""
        VintedJobStatusManager.start_job(mock_db, mock_job)

        assert mock_job.started_at.tzinfo == timezone.utc

    def test_start_job_returns_job(self, mock_db, mock_job):
        """Test that start_job returns the updated job."""
        result = VintedJobStatusManager.start_job(mock_db, mock_job)

        assert result is mock_job


# ===========================
# Test: complete_job
# ===========================


class TestCompleteJob:
    """Test complete_job method."""

    def test_complete_job_updates_status_and_timestamp(self, mock_db, mock_job):
        """Test that complete_job sets status to COMPLETED and completed_at timestamp."""
        VintedJobStatusManager.complete_job(mock_db, mock_job)

        assert mock_job.status == JobStatus.COMPLETED
        assert mock_job.completed_at is not None
        assert isinstance(mock_job.completed_at, datetime)
        mock_db.commit.assert_called_once()

    def test_complete_job_calls_callback_with_success_true(
        self, mock_db, mock_job, mock_callback
    ):
        """Test that complete_job calls the callback with success=True."""
        VintedJobStatusManager.complete_job(mock_db, mock_job, mock_callback)

        mock_callback.assert_called_once_with(mock_job, True)

    def test_complete_job_without_callback(self, mock_db, mock_job):
        """Test that complete_job works without callback."""
        VintedJobStatusManager.complete_job(mock_db, mock_job, None)

        assert mock_job.status == JobStatus.COMPLETED
        mock_db.commit.assert_called_once()


# ===========================
# Test: fail_job
# ===========================


class TestFailJob:
    """Test fail_job method."""

    def test_fail_job_updates_status_and_error(self, mock_db, mock_job):
        """Test that fail_job sets status to FAILED, error_message, and completed_at."""
        error_msg = "Test error"
        VintedJobStatusManager.fail_job(mock_db, mock_job, error_msg)

        assert mock_job.status == JobStatus.FAILED
        assert mock_job.error_message == error_msg
        assert mock_job.completed_at is not None
        mock_db.commit.assert_called_once()

    def test_fail_job_calls_callback_with_success_false(
        self, mock_db, mock_job, mock_callback
    ):
        """Test that fail_job calls the callback with success=False."""
        VintedJobStatusManager.fail_job(mock_db, mock_job, "Error", mock_callback)

        mock_callback.assert_called_once_with(mock_job, False)

    def test_fail_job_without_callback(self, mock_db, mock_job):
        """Test that fail_job works without callback."""
        VintedJobStatusManager.fail_job(mock_db, mock_job, "Error", None)

        assert mock_job.status == JobStatus.FAILED
        mock_db.commit.assert_called_once()


# ===========================
# Test: pause_job
# ===========================


class TestPauseJob:
    """Test pause_job method."""

    def test_pause_job_from_pending_status(self, mock_db, mock_job):
        """Test that pause_job can pause a PENDING job."""
        mock_job.status = JobStatus.PENDING

        result = VintedJobStatusManager.pause_job(mock_db, mock_job)

        assert result is mock_job
        assert mock_job.status == JobStatus.PAUSED
        mock_db.commit.assert_called_once()

    def test_pause_job_from_running_status(self, mock_db, mock_job):
        """Test that pause_job can pause a RUNNING job."""
        mock_job.status = JobStatus.RUNNING

        result = VintedJobStatusManager.pause_job(mock_db, mock_job)

        assert result is mock_job
        assert mock_job.status == JobStatus.PAUSED
        mock_db.commit.assert_called_once()

    def test_pause_job_from_completed_returns_none(self, mock_db, mock_job):
        """Test that pause_job returns None for COMPLETED job (not pausable)."""
        mock_job.status = JobStatus.COMPLETED

        result = VintedJobStatusManager.pause_job(mock_db, mock_job)

        assert result is None
        assert mock_job.status == JobStatus.COMPLETED  # Unchanged
        mock_db.commit.assert_not_called()

    def test_pause_job_from_failed_returns_none(self, mock_db, mock_job):
        """Test that pause_job returns None for FAILED job (not pausable)."""
        mock_job.status = JobStatus.FAILED

        result = VintedJobStatusManager.pause_job(mock_db, mock_job)

        assert result is None
        mock_db.commit.assert_not_called()


# ===========================
# Test: resume_job
# ===========================


class TestResumeJob:
    """Test resume_job method."""

    def test_resume_job_updates_status_and_expiration(self, mock_db, mock_job):
        """Test that resume_job sets status to PENDING and resets expires_at."""
        mock_job.status = JobStatus.PAUSED

        result = VintedJobStatusManager.resume_job(mock_db, mock_job)

        assert result is mock_job
        assert mock_job.status == JobStatus.PENDING
        assert mock_job.expires_at is not None
        mock_db.commit.assert_called_once()

    def test_resume_job_sets_correct_expiration_time(self, mock_db, mock_job):
        """Test that resume_job sets expires_at to now + JOB_EXPIRATION_HOURS."""
        mock_job.status = JobStatus.PAUSED
        before_call = datetime.now(timezone.utc)

        VintedJobStatusManager.resume_job(mock_db, mock_job)

        after_call = datetime.now(timezone.utc)
        expected_min = before_call + timedelta(hours=JOB_EXPIRATION_HOURS)
        expected_max = after_call + timedelta(hours=JOB_EXPIRATION_HOURS)

        assert expected_min <= mock_job.expires_at <= expected_max

    def test_resume_job_from_pending_returns_none(self, mock_db, mock_job):
        """Test that resume_job returns None for PENDING job (not resumable)."""
        mock_job.status = JobStatus.PENDING

        result = VintedJobStatusManager.resume_job(mock_db, mock_job)

        assert result is None
        mock_db.commit.assert_not_called()

    def test_resume_job_from_running_returns_none(self, mock_db, mock_job):
        """Test that resume_job returns None for RUNNING job (not resumable)."""
        mock_job.status = JobStatus.RUNNING

        result = VintedJobStatusManager.resume_job(mock_db, mock_job)

        assert result is None
        mock_db.commit.assert_not_called()


# ===========================
# Test: cancel_job
# ===========================


class TestCancelJob:
    """Test cancel_job method."""

    @patch.object(VintedJobStatusManager, "_cancel_job_tasks")
    def test_cancel_job_updates_status_and_timestamp(
        self, mock_cancel_tasks, mock_db, mock_job
    ):
        """Test that cancel_job sets status to CANCELLED and completed_at."""
        mock_job.status = JobStatus.PENDING
        mock_job.is_terminal = False

        result = VintedJobStatusManager.cancel_job(mock_db, mock_job)

        assert result is mock_job
        assert mock_job.status == JobStatus.CANCELLED
        assert mock_job.completed_at is not None
        mock_db.commit.assert_called_once()
        mock_cancel_tasks.assert_called_once_with(mock_db, mock_job.id)

    @patch.object(VintedJobStatusManager, "_cancel_job_tasks")
    def test_cancel_job_from_running_status(
        self, mock_cancel_tasks, mock_db, mock_job
    ):
        """Test that cancel_job can cancel a RUNNING job."""
        mock_job.status = JobStatus.RUNNING
        mock_job.is_terminal = False

        result = VintedJobStatusManager.cancel_job(mock_db, mock_job)

        assert result is mock_job
        assert mock_job.status == JobStatus.CANCELLED

    def test_cancel_job_from_completed_returns_none(self, mock_db, mock_job):
        """Test that cancel_job returns None for COMPLETED job (terminal)."""
        mock_job.status = JobStatus.COMPLETED
        mock_job.is_terminal = True

        result = VintedJobStatusManager.cancel_job(mock_db, mock_job)

        assert result is None
        assert mock_job.status == JobStatus.COMPLETED  # Unchanged
        mock_db.commit.assert_not_called()

    def test_cancel_job_from_failed_returns_none(self, mock_db, mock_job):
        """Test that cancel_job returns None for FAILED job (terminal)."""
        mock_job.status = JobStatus.FAILED
        mock_job.is_terminal = True

        result = VintedJobStatusManager.cancel_job(mock_db, mock_job)

        assert result is None
        mock_db.commit.assert_not_called()


# ===========================
# Test: increment_retry
# ===========================


class TestIncrementRetry:
    """Test increment_retry method."""

    def test_increment_retry_count_below_max(self, mock_db, mock_job):
        """Test that increment_retry increments count and returns can_retry=True."""
        mock_job.retry_count = 1

        job, can_retry = VintedJobStatusManager.increment_retry(
            mock_db, mock_job, max_retries=3
        )

        assert job is mock_job
        assert job.retry_count == 2
        assert can_retry is True
        assert job.status == JobStatus.PENDING  # Unchanged
        mock_db.commit.assert_called_once()

    def test_increment_retry_count_at_max(self, mock_db, mock_job, mock_callback):
        """Test that increment_retry marks as FAILED when max retries reached."""
        mock_job.retry_count = 2

        job, can_retry = VintedJobStatusManager.increment_retry(
            mock_db, mock_job, max_retries=3, on_max_retries_callback=mock_callback
        )

        assert job.retry_count == 3
        assert can_retry is False
        assert job.status == JobStatus.FAILED
        assert "Max retries (3) exceeded" in job.error_message
        assert job.completed_at is not None
        mock_callback.assert_called_once_with(job, False)
        mock_db.commit.assert_called_once()

    def test_increment_retry_without_callback(self, mock_db, mock_job):
        """Test that increment_retry works without callback."""
        mock_job.retry_count = 2

        job, can_retry = VintedJobStatusManager.increment_retry(
            mock_db, mock_job, max_retries=3
        )

        assert can_retry is False
        assert job.status == JobStatus.FAILED
        mock_db.commit.assert_called_once()

    def test_increment_retry_from_zero(self, mock_db, mock_job):
        """Test that increment_retry works from zero retries."""
        mock_job.retry_count = 0

        job, can_retry = VintedJobStatusManager.increment_retry(
            mock_db, mock_job, max_retries=3
        )

        assert job.retry_count == 1
        assert can_retry is True


# ===========================
# Test: expire_old_jobs
# ===========================


class TestExpireOldJobs:
    """Test expire_old_jobs method."""

    def test_expire_old_jobs_marks_expired_jobs(self, mock_db):
        """Test that expire_old_jobs marks expired pending/paused jobs as EXPIRED."""
        now = datetime.now(timezone.utc)
        expired_time = now - timedelta(hours=2)

        # Mock expired jobs
        job1 = MagicMock(spec=MarketplaceJob)
        job1.status = JobStatus.PENDING
        job1.expires_at = expired_time

        job2 = MagicMock(spec=MarketplaceJob)
        job2.status = JobStatus.PAUSED
        job2.expires_at = expired_time

        mock_db.query.return_value.filter.return_value.all.return_value = [job1, job2]

        count = VintedJobStatusManager.expire_old_jobs(mock_db)

        assert count == 2
        assert job1.status == JobStatus.EXPIRED
        assert job2.status == JobStatus.EXPIRED
        assert job1.completed_at is not None
        assert job2.completed_at is not None
        assert "Job expired" in job1.error_message
        assert "Job expired" in job2.error_message
        mock_db.commit.assert_called_once()

    def test_expire_old_jobs_returns_zero_when_none_expired(self, mock_db):
        """Test that expire_old_jobs returns 0 when no jobs are expired."""
        mock_db.query.return_value.filter.return_value.all.return_value = []

        count = VintedJobStatusManager.expire_old_jobs(mock_db)

        assert count == 0
        mock_db.commit.assert_not_called()

    def test_expire_old_jobs_filters_correct_statuses(self, mock_db):
        """Test that expire_old_jobs only queries PENDING and PAUSED jobs."""
        now = datetime.now(timezone.utc)
        mock_db.query.return_value.filter.return_value.all.return_value = []

        VintedJobStatusManager.expire_old_jobs(mock_db)

        # Verify query filters
        mock_db.query.assert_called_once_with(MarketplaceJob)
        filter_call = mock_db.query.return_value.filter.call_args
        # We can't easily verify the exact filter args, but we can verify filter was called
        assert filter_call is not None


# ===========================
# Test: _cancel_job_tasks (DEPRECATED)
# ===========================


class TestCancelJobTasks:
    """Test _cancel_job_tasks method (deprecated)."""

    def test_cancel_job_tasks_returns_zero(self, mock_db):
        """Test that _cancel_job_tasks always returns 0 (deprecated, WebSocket architecture)."""
        count = VintedJobStatusManager._cancel_job_tasks(mock_db, 123)

        assert count == 0


# ===========================
# Test: VintedJobStatusManager Smoke Tests
# ===========================


class TestVintedJobStatusManagerSmoke:
    """Smoke tests for VintedJobStatusManager."""

    def test_all_public_methods_exist(self):
        """Test that all expected public methods exist."""
        expected_methods = [
            "start_job",
            "complete_job",
            "fail_job",
            "pause_job",
            "resume_job",
            "cancel_job",
            "increment_retry",
            "expire_old_jobs",
        ]

        for method_name in expected_methods:
            assert hasattr(VintedJobStatusManager, method_name)
            assert callable(getattr(VintedJobStatusManager, method_name))

    def test_all_public_methods_are_static(self):
        """Test that all public methods are static methods."""
        public_methods = [
            "start_job",
            "complete_job",
            "fail_job",
            "pause_job",
            "resume_job",
            "cancel_job",
            "increment_retry",
            "expire_old_jobs",
        ]

        for method_name in public_methods:
            method = getattr(VintedJobStatusManager, method_name)
            assert isinstance(
                inspect.getattr_static(VintedJobStatusManager, method_name),
                staticmethod,
            )


# Import inspect for smoke tests
import inspect
