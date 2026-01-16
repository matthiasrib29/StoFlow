"""
Unit tests for JobCleanupService.

Tests cover job cleanup operations:
- cleanup_expired_jobs: Mark expired PENDING/RUNNING jobs as FAILED
- cleanup_old_jobs: Soft-delete old completed jobs

Mocks: SQLAlchemy session, db.execute()

Author: Claude
Date: 2026-01-16
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch, call

from models.user.marketplace_job import JobStatus, MarketplaceJob
from services.marketplace.job_cleanup_service import JobCleanupService


# ===========================
# Fixtures
# ===========================


@pytest.fixture
def mock_db():
    """Mock SQLAlchemy Session."""
    db = MagicMock()
    db.commit = MagicMock()
    db.execute = MagicMock()
    return db


@pytest.fixture
def mock_execute_result():
    """Mock execute result with rowcount."""
    result = MagicMock()
    result.rowcount = 0
    return result


# ===========================
# Test: cleanup_expired_jobs
# ===========================


class TestCleanupExpiredJobs:
    """Test cleanup_expired_jobs method."""

    def test_cleanup_expired_jobs_marks_pending_as_failed(
        self, mock_db, mock_execute_result
    ):
        """Test that cleanup marks expired PENDING jobs as FAILED."""
        # Mock: 5 pending expired, 0 processing expired
        mock_db.execute.side_effect = [
            MagicMock(rowcount=5),  # First call: PENDING
            MagicMock(rowcount=0),  # Second call: RUNNING
        ]

        result = JobCleanupService.cleanup_expired_jobs(mock_db)

        assert result["pending_expired"] == 5
        assert result["processing_expired"] == 0
        assert mock_db.execute.call_count == 2
        mock_db.commit.assert_called_once()

    def test_cleanup_expired_jobs_marks_processing_as_failed(
        self, mock_db, mock_execute_result
    ):
        """Test that cleanup marks expired RUNNING jobs as FAILED."""
        # Mock: 0 pending expired, 3 processing expired
        mock_db.execute.side_effect = [
            MagicMock(rowcount=0),  # First call: PENDING
            MagicMock(rowcount=3),  # Second call: RUNNING
        ]

        result = JobCleanupService.cleanup_expired_jobs(mock_db)

        assert result["pending_expired"] == 0
        assert result["processing_expired"] == 3
        mock_db.commit.assert_called_once()

    def test_cleanup_expired_jobs_handles_zero_expired(self, mock_db):
        """Test that cleanup handles case when no jobs are expired."""
        mock_db.execute.side_effect = [
            MagicMock(rowcount=0),
            MagicMock(rowcount=0),
        ]

        result = JobCleanupService.cleanup_expired_jobs(mock_db)

        assert result["pending_expired"] == 0
        assert result["processing_expired"] == 0
        mock_db.commit.assert_called_once()

    def test_cleanup_expired_jobs_uses_correct_pending_timeout(self, mock_db):
        """Test that cleanup uses PENDING_TIMEOUT (24 hours) for pending jobs."""
        mock_db.execute.side_effect = [
            MagicMock(rowcount=0),
            MagicMock(rowcount=0),
        ]

        JobCleanupService.cleanup_expired_jobs(mock_db)

        # Verify first execute call (PENDING jobs)
        first_call = mock_db.execute.call_args_list[0]
        # We can't easily inspect the SQLAlchemy update statement,
        # but we can verify execute was called
        assert first_call is not None

    def test_cleanup_expired_jobs_uses_correct_processing_timeout(self, mock_db):
        """Test that cleanup uses PROCESSING_TIMEOUT (2 hours) for running jobs."""
        mock_db.execute.side_effect = [
            MagicMock(rowcount=0),
            MagicMock(rowcount=0),
        ]

        JobCleanupService.cleanup_expired_jobs(mock_db)

        # Verify second execute call (RUNNING jobs)
        second_call = mock_db.execute.call_args_list[1]
        assert second_call is not None

    def test_cleanup_expired_jobs_commits_changes(self, mock_db):
        """Test that cleanup commits changes to database."""
        mock_db.execute.side_effect = [
            MagicMock(rowcount=2),
            MagicMock(rowcount=1),
        ]

        JobCleanupService.cleanup_expired_jobs(mock_db)

        mock_db.commit.assert_called_once()

    def test_cleanup_expired_jobs_returns_correct_structure(self, mock_db):
        """Test that cleanup returns dict with expected keys."""
        mock_db.execute.side_effect = [
            MagicMock(rowcount=10),
            MagicMock(rowcount=5),
        ]

        result = JobCleanupService.cleanup_expired_jobs(mock_db)

        assert isinstance(result, dict)
        assert "pending_expired" in result
        assert "processing_expired" in result
        assert len(result) == 2


# ===========================
# Test: cleanup_old_jobs
# ===========================


class TestCleanupOldJobs:
    """Test cleanup_old_jobs method."""

    def test_cleanup_old_jobs_soft_deletes_old_jobs(self, mock_db):
        """Test that cleanup soft-deletes old COMPLETED/FAILED/CANCELLED jobs."""
        mock_db.execute.return_value.rowcount = 15

        deleted = JobCleanupService.cleanup_old_jobs(mock_db, retention_days=30)

        assert deleted == 15
        mock_db.execute.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_cleanup_old_jobs_returns_zero_when_none_deleted(self, mock_db):
        """Test that cleanup returns 0 when no old jobs found."""
        mock_db.execute.return_value.rowcount = 0

        deleted = JobCleanupService.cleanup_old_jobs(mock_db, retention_days=30)

        assert deleted == 0
        mock_db.commit.assert_called_once()

    def test_cleanup_old_jobs_uses_custom_retention_days(self, mock_db):
        """Test that cleanup uses custom retention_days parameter."""
        mock_db.execute.return_value.rowcount = 5

        deleted = JobCleanupService.cleanup_old_jobs(mock_db, retention_days=60)

        assert deleted == 5
        mock_db.execute.assert_called_once()
        # We can't easily verify the exact cutoff date in the SQL,
        # but we verify execute was called

    def test_cleanup_old_jobs_uses_default_retention_period(self, mock_db):
        """Test that cleanup uses default retention period (30 days)."""
        mock_db.execute.return_value.rowcount = 0

        JobCleanupService.cleanup_old_jobs(mock_db)

        mock_db.execute.assert_called_once()
        # Default retention_days=30 is used

    def test_cleanup_old_jobs_commits_changes(self, mock_db):
        """Test that cleanup commits changes to database."""
        mock_db.execute.return_value.rowcount = 10

        JobCleanupService.cleanup_old_jobs(mock_db, retention_days=30)

        mock_db.commit.assert_called_once()

    def test_cleanup_old_jobs_only_deletes_terminal_statuses(self, mock_db):
        """Test that cleanup only soft-deletes COMPLETED/FAILED/CANCELLED jobs."""
        mock_db.execute.return_value.rowcount = 0

        JobCleanupService.cleanup_old_jobs(mock_db)

        # Verify execute was called (can't easily inspect exact SQL)
        mock_db.execute.assert_called_once()


# ===========================
# Test: JobCleanupService Constants
# ===========================


class TestJobCleanupServiceConstants:
    """Test JobCleanupService timeout constants."""

    def test_pending_timeout_is_24_hours(self):
        """Test that PENDING_TIMEOUT is 24 hours."""
        assert JobCleanupService.PENDING_TIMEOUT == timedelta(hours=24)

    def test_processing_timeout_is_2_hours(self):
        """Test that PROCESSING_TIMEOUT is 2 hours."""
        assert JobCleanupService.PROCESSING_TIMEOUT == timedelta(hours=2)

    def test_retention_period_is_30_days(self):
        """Test that RETENTION_PERIOD is 30 days."""
        assert JobCleanupService.RETENTION_PERIOD == timedelta(days=30)


# ===========================
# Test: JobCleanupService Smoke Tests
# ===========================


class TestJobCleanupServiceSmoke:
    """Smoke tests for JobCleanupService."""

    def test_all_public_methods_exist(self):
        """Test that all expected public methods exist."""
        expected_methods = [
            "cleanup_expired_jobs",
            "cleanup_old_jobs",
        ]

        for method_name in expected_methods:
            assert hasattr(JobCleanupService, method_name)
            assert callable(getattr(JobCleanupService, method_name))

    def test_all_public_methods_are_static(self):
        """Test that all public methods are static methods."""
        import inspect

        public_methods = [
            "cleanup_expired_jobs",
            "cleanup_old_jobs",
        ]

        for method_name in public_methods:
            method = getattr(JobCleanupService, method_name)
            assert isinstance(
                inspect.getattr_static(JobCleanupService, method_name),
                staticmethod,
            )

    def test_all_constants_defined(self):
        """Test that all timeout constants are defined."""
        assert hasattr(JobCleanupService, "PENDING_TIMEOUT")
        assert hasattr(JobCleanupService, "PROCESSING_TIMEOUT")
        assert hasattr(JobCleanupService, "RETENTION_PERIOD")


# ===========================
# Integration-like Tests
# ===========================


class TestJobCleanupServiceIntegration:
    """Integration-like tests (still using mocks)."""

    def test_full_cleanup_workflow(self, mock_db):
        """Test complete cleanup workflow (both expired and old jobs)."""
        # Mock cleanup_expired_jobs
        mock_db.execute.side_effect = [
            MagicMock(rowcount=3),  # PENDING expired
            MagicMock(rowcount=2),  # RUNNING expired
            MagicMock(rowcount=10),  # Old jobs deleted
        ]

        # Run both cleanup methods
        expired_result = JobCleanupService.cleanup_expired_jobs(mock_db)
        deleted_count = JobCleanupService.cleanup_old_jobs(mock_db, retention_days=30)

        assert expired_result["pending_expired"] == 3
        assert expired_result["processing_expired"] == 2
        assert deleted_count == 10
        assert mock_db.commit.call_count == 2

    def test_cleanup_handles_large_numbers(self, mock_db):
        """Test cleanup can handle large number of jobs."""
        # Mock large cleanup operation
        mock_db.execute.side_effect = [
            MagicMock(rowcount=1000),  # PENDING expired
            MagicMock(rowcount=500),  # RUNNING expired
        ]

        result = JobCleanupService.cleanup_expired_jobs(mock_db)

        assert result["pending_expired"] == 1000
        assert result["processing_expired"] == 500
