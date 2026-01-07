"""
Unit Tests for MarketplaceJobService

Tests marketplace job management and batch progress auto-update.

Created: 2026-01-07
Phase 6.1: Unit testing
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock, patch

from models.user.marketplace_job import MarketplaceJob, JobStatus
from models.vinted.vinted_action_type import VintedActionType
from services.marketplace.marketplace_job_service import MarketplaceJobService


class TestMarketplaceJobServiceComplete:
    """Test job completion with batch progress auto-update."""

    @patch.object(MarketplaceJobService, '_update_job_stats')
    def test_complete_job_updates_status(self, mock_update_stats, db_session, mock_job):
        """Should update job status to COMPLETED."""
        service = MarketplaceJobService(db_session)

        # Mock query
        db_session.query = Mock(return_value=Mock(
            filter=Mock(return_value=Mock(
                first=Mock(return_value=mock_job)
            ))
        ))

        # Complete job
        completed = service.complete_job(1)

        assert completed is not None
        assert completed.status == JobStatus.COMPLETED
        assert completed.completed_at is not None

    @patch.object(MarketplaceJobService, '_update_job_stats')
    @patch('services.marketplace.batch_job_service.BatchJobService')
    def test_complete_job_updates_batch_progress(self, mock_batch_service_class, mock_update_stats, db_session, mock_job):
        """Should call BatchJobService.update_batch_progress when job has batch_job_id."""
        service = MarketplaceJobService(db_session)

        # Set batch_job_id on mock job
        mock_job.batch_job_id = 123

        # Mock query
        db_session.query = Mock(return_value=Mock(
            filter=Mock(return_value=Mock(
                first=Mock(return_value=mock_job)
            ))
        ))

        # Mock BatchJobService
        mock_batch_service = MagicMock()
        mock_batch_service_class.return_value = mock_batch_service

        # Complete job
        service.complete_job(1)

        # Should have called update_batch_progress
        mock_batch_service.update_batch_progress.assert_called_once_with(123)

    def test_complete_job_not_found_returns_none(self, db_session):
        """Should return None when job not found."""
        service = MarketplaceJobService(db_session)

        # Mock job not found
        db_session.query = Mock(return_value=Mock(
            filter=Mock(return_value=Mock(
                first=Mock(return_value=None)
            ))
        ))

        result = service.complete_job(999)
        assert result is None


class TestMarketplaceJobServiceFail:
    """Test job failure with batch progress auto-update."""

    @patch.object(MarketplaceJobService, '_update_job_stats')
    def test_fail_job_updates_status(self, mock_update_stats, db_session, mock_job):
        """Should update job status to FAILED with error message."""
        service = MarketplaceJobService(db_session)

        # Mock query
        db_session.query = Mock(return_value=Mock(
            filter=Mock(return_value=Mock(
                first=Mock(return_value=mock_job)
            ))
        ))

        # Fail job
        failed = service.fail_job(1, "Connection timeout")

        assert failed is not None
        assert failed.status == JobStatus.FAILED
        assert failed.error_message == "Connection timeout"
        assert failed.completed_at is not None

    @patch.object(MarketplaceJobService, '_update_job_stats')
    @patch('services.marketplace.batch_job_service.BatchJobService')
    def test_fail_job_updates_batch_progress(self, mock_batch_service_class, mock_update_stats, db_session, mock_job):
        """Should call BatchJobService.update_batch_progress when job has batch_job_id."""
        service = MarketplaceJobService(db_session)

        # Set batch_job_id on mock job
        mock_job.batch_job_id = 456

        # Mock query
        db_session.query = Mock(return_value=Mock(
            filter=Mock(return_value=Mock(
                first=Mock(return_value=mock_job)
            ))
        ))

        # Mock BatchJobService
        mock_batch_service = MagicMock()
        mock_batch_service_class.return_value = mock_batch_service

        # Fail job
        service.fail_job(1, "Error occurred")

        # Should have called update_batch_progress
        mock_batch_service.update_batch_progress.assert_called_once_with(456)


class TestMarketplaceJobServiceCancel:
    """Test job cancellation."""

    @patch.object(MarketplaceJobService, '_cancel_job_tasks', return_value=0)
    def test_cancel_job_pending_success(self, mock_cancel_tasks, db_session, mock_job):
        """Should cancel a pending job."""
        service = MarketplaceJobService(db_session)

        mock_job.status = JobStatus.PENDING

        # Mock query
        db_session.query = Mock(return_value=Mock(
            filter=Mock(return_value=Mock(
                first=Mock(return_value=mock_job)
            ))
        ))

        # Cancel job
        cancelled = service.cancel_job(1)

        assert cancelled is not None
        assert cancelled.status == JobStatus.CANCELLED

    @patch.object(MarketplaceJobService, '_cancel_job_tasks', return_value=0)
    def test_cancel_job_running_success(self, mock_cancel_tasks, db_session, mock_job):
        """Should cancel a running job."""
        service = MarketplaceJobService(db_session)

        mock_job.status = JobStatus.RUNNING

        # Mock query
        db_session.query = Mock(return_value=Mock(
            filter=Mock(return_value=Mock(
                first=Mock(return_value=mock_job)
            ))
        ))

        # Cancel job
        cancelled = service.cancel_job(1)

        assert cancelled is not None
        assert cancelled.status == JobStatus.CANCELLED

    def test_cancel_job_completed_returns_none(self, db_session, mock_job):
        """Should not cancel a completed job."""
        service = MarketplaceJobService(db_session)

        mock_job.status = JobStatus.COMPLETED

        # Mock query
        db_session.query = Mock(return_value=Mock(
            filter=Mock(return_value=Mock(
                first=Mock(return_value=mock_job)
            ))
        ))

        # Try to cancel completed job
        result = service.cancel_job(1)

        # Should return None (cannot cancel terminal status)
        assert result is None

    def test_cancel_job_failed_returns_none(self, db_session, mock_job):
        """Should not cancel a failed job."""
        service = MarketplaceJobService(db_session)

        mock_job.status = JobStatus.FAILED

        # Mock query
        db_session.query = Mock(return_value=Mock(
            filter=Mock(return_value=Mock(
                first=Mock(return_value=mock_job)
            ))
        ))

        # Try to cancel failed job
        result = service.cancel_job(1)

        # Should return None (cannot cancel terminal status)
        assert result is None


class TestMarketplaceJobServiceGet:
    """Test job retrieval."""

    def test_get_job_success(self, db_session, mock_job):
        """Should return job by ID."""
        service = MarketplaceJobService(db_session)

        # Mock query
        db_session.query = Mock(return_value=Mock(
            filter=Mock(return_value=Mock(
                first=Mock(return_value=mock_job)
            ))
        ))

        job = service.get_job(1)

        assert job is not None
        assert job.id == 1
        assert job.marketplace == "vinted"

    def test_get_job_not_found_returns_none(self, db_session):
        """Should return None when job not found."""
        service = MarketplaceJobService(db_session)

        # Mock job not found
        db_session.query = Mock(return_value=Mock(
            filter=Mock(return_value=Mock(
                first=Mock(return_value=None)
            ))
        ))

        job = service.get_job(999)
        assert job is None


class TestMarketplaceJobServiceBatchJobs:
    """Test retrieving batch jobs."""

    def test_get_batch_jobs_success(self, db_session):
        """Should return all jobs for a batch_id."""
        service = MarketplaceJobService(db_session)

        # Create mock jobs
        mock_jobs = [
            MarketplaceJob(
                id=1,
                marketplace="vinted",
                action_type_id=1,
                product_id=101,
                batch_id="batch_123",
                status=JobStatus.COMPLETED,
                priority=3,
                retry_count=0,
                max_retries=3,
                created_at=datetime.now(timezone.utc)
            ),
            MarketplaceJob(
                id=2,
                marketplace="vinted",
                action_type_id=1,
                product_id=102,
                batch_id="batch_123",
                status=JobStatus.RUNNING,
                priority=3,
                retry_count=0,
                max_retries=3,
                created_at=datetime.now(timezone.utc)
            ),
        ]

        # Mock query with order_by
        mock_all = Mock(all=Mock(return_value=mock_jobs))
        mock_order_by = Mock(return_value=mock_all)
        mock_filter = Mock(return_value=Mock(order_by=mock_order_by))
        db_session.query = Mock(return_value=Mock(filter=mock_filter))

        jobs = service.get_batch_jobs("batch_123")

        assert len(jobs) == 2
        assert all(job.batch_id == "batch_123" for job in jobs)

    def test_get_batch_jobs_empty(self, db_session):
        """Should return empty list when no jobs found."""
        service = MarketplaceJobService(db_session)

        # Mock no jobs with order_by
        mock_all = Mock(all=Mock(return_value=[]))
        mock_order_by = Mock(return_value=mock_all)
        mock_filter = Mock(return_value=Mock(order_by=mock_order_by))
        db_session.query = Mock(return_value=Mock(filter=mock_filter))

        jobs = service.get_batch_jobs("nonexistent_batch")
        assert jobs == []


class TestMarketplaceJobServiceActionType:
    """Test action type retrieval."""

    def test_get_action_type_by_id_success(self, db_session, mock_action_type):
        """Should return action type by ID."""
        service = MarketplaceJobService(db_session)

        # Mock query
        db_session.query = Mock(return_value=Mock(
            filter=Mock(return_value=Mock(
                first=Mock(return_value=mock_action_type)
            ))
        ))

        action_type = service.get_action_type_by_id(1)

        assert action_type is not None
        assert action_type.id == 1
        assert action_type.code == "publish"

    def test_get_action_type_by_code_success(self, db_session, mock_action_type):
        """Should return action type by code and marketplace."""
        service = MarketplaceJobService(db_session)

        # Mock query
        db_session.query = Mock(return_value=Mock(
            filter=Mock(return_value=Mock(
                first=Mock(return_value=mock_action_type)
            ))
        ))

        action_type = service.get_action_type("vinted", "publish")

        assert action_type is not None
        assert action_type.code == "publish"


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def db_session():
    """Mock database session."""
    session = Mock(spec=["query", "add", "flush", "commit", "rollback"])
    return session


@pytest.fixture
def mock_job():
    """Mock MarketplaceJob."""
    return MarketplaceJob(
        id=1,
        marketplace="vinted",
        action_type_id=1,
        product_id=101,
        batch_id="batch_123",
        batch_job_id=None,  # Can be set in tests
        status=JobStatus.PENDING,
        priority=3,
        retry_count=0,
        max_retries=3,
        created_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def mock_action_type():
    """Mock VintedActionType."""
    return VintedActionType(
        id=1,
        code="publish",
        name="Publish Product",
        priority=3
    )
