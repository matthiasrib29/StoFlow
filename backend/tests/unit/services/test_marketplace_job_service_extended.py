"""
Extended Unit Tests for MarketplaceJobService

Tests for additional methods: create_job, start_job, pause_job, resume_job,
expire_old_jobs, get_pending_jobs, get_stats, get_job_progress, etc.

Created: 2026-01-20
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, MagicMock, patch

from models.user.marketplace_job import MarketplaceJob, JobStatus
from models.user.marketplace_task import MarketplaceTask, TaskStatus
from models.user.marketplace_job_stats import MarketplaceJobStats
from models.public.marketplace_action_type import MarketplaceActionType
from services.marketplace.marketplace_job_service import MarketplaceJobService


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def db_session():
    """Mock database session."""
    session = Mock(spec=["query", "add", "flush", "commit", "rollback"])
    return session


@pytest.fixture
def mock_action_type():
    """Mock MarketplaceActionType."""
    return MarketplaceActionType(
        id=1,
        marketplace="vinted",
        code="publish",
        name="Publish Product",
        priority=3
    )


@pytest.fixture
def mock_job():
    """Mock MarketplaceJob."""
    return MarketplaceJob(
        id=1,
        marketplace="vinted",
        action_type_id=1,
        product_id=101,
        status=JobStatus.PENDING,
        priority=3,
        retry_count=0,
        max_retries=3,
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )


# =============================================================================
# Test: create_job
# =============================================================================


class TestCreateJob:
    """Test create_job method."""

    def test_create_job_success(self, db_session, mock_action_type):
        """Should create a new job with correct attributes."""
        service = MarketplaceJobService(db_session)

        # Mock action type lookup
        db_session.query = Mock(return_value=Mock(
            filter=Mock(return_value=Mock(
                first=Mock(return_value=mock_action_type)
            ))
        ))

        job = service.create_job(
            marketplace="vinted",
            action_code="publish",
            product_id=123,
            priority=2,
        )

        assert job is not None
        assert job.marketplace == "vinted"
        assert job.action_type_id == mock_action_type.id
        assert job.product_id == 123
        assert job.priority == 2
        assert job.status == JobStatus.PENDING
        db_session.add.assert_called_once()
        db_session.flush.assert_called_once()

    def test_create_job_uses_action_type_default_priority(self, db_session, mock_action_type):
        """Should use action type priority when not specified."""
        service = MarketplaceJobService(db_session)

        db_session.query = Mock(return_value=Mock(
            filter=Mock(return_value=Mock(
                first=Mock(return_value=mock_action_type)
            ))
        ))

        job = service.create_job(
            marketplace="vinted",
            action_code="publish",
            product_id=123,
            # No priority specified
        )

        assert job.priority == mock_action_type.priority

    def test_create_job_invalid_action_raises(self, db_session):
        """Should raise ValueError for invalid action code."""
        service = MarketplaceJobService(db_session)

        # Mock action type not found
        db_session.query = Mock(return_value=Mock(
            filter=Mock(return_value=Mock(
                first=Mock(return_value=None)
            ))
        ))

        with pytest.raises(ValueError, match="Invalid action code"):
            service.create_job(
                marketplace="vinted",
                action_code="invalid_action",
                product_id=123,
            )

    def test_create_job_with_input_data(self, db_session, mock_action_type):
        """Should store input_data when provided."""
        service = MarketplaceJobService(db_session)

        db_session.query = Mock(return_value=Mock(
            filter=Mock(return_value=Mock(
                first=Mock(return_value=mock_action_type)
            ))
        ))

        input_data = {"title": "Test Product", "price": 29.99}
        job = service.create_job(
            marketplace="vinted",
            action_code="publish",
            product_id=123,
            input_data=input_data,
        )

        assert job.input_data == input_data

    def test_create_job_with_marketplace_batch_id(self, db_session, mock_action_type):
        """Should store marketplace_batch_id when provided."""
        service = MarketplaceJobService(db_session)

        db_session.query = Mock(return_value=Mock(
            filter=Mock(return_value=Mock(
                first=Mock(return_value=mock_action_type)
            ))
        ))

        job = service.create_job(
            marketplace="vinted",
            action_code="publish",
            product_id=123,
            marketplace_batch_id=42,
        )

        assert job.marketplace_batch_id == 42


# =============================================================================
# Test: start_job
# =============================================================================


class TestStartJob:
    """Test start_job method."""

    def test_start_job_success(self, db_session, mock_job):
        """Should update job status to RUNNING."""
        service = MarketplaceJobService(db_session)

        db_session.query = Mock(return_value=Mock(
            filter=Mock(return_value=Mock(
                first=Mock(return_value=mock_job)
            ))
        ))

        started = service.start_job(1)

        assert started is not None
        assert started.status == JobStatus.RUNNING
        assert started.started_at is not None
        db_session.flush.assert_called_once()

    def test_start_job_not_found(self, db_session):
        """Should return None when job not found."""
        service = MarketplaceJobService(db_session)

        db_session.query = Mock(return_value=Mock(
            filter=Mock(return_value=Mock(
                first=Mock(return_value=None)
            ))
        ))

        result = service.start_job(999)
        assert result is None


# =============================================================================
# Test: pause_job
# =============================================================================


class TestPauseJob:
    """Test pause_job method."""

    def test_pause_running_job(self, db_session, mock_job):
        """Should pause a running job."""
        service = MarketplaceJobService(db_session)
        mock_job.status = JobStatus.RUNNING

        db_session.query = Mock(return_value=Mock(
            filter=Mock(return_value=Mock(
                first=Mock(return_value=mock_job)
            ))
        ))

        paused = service.pause_job(1)

        assert paused is not None
        assert paused.status == JobStatus.PAUSED
        db_session.flush.assert_called_once()

    def test_pause_pending_job(self, db_session, mock_job):
        """Should pause a pending job."""
        service = MarketplaceJobService(db_session)
        mock_job.status = JobStatus.PENDING

        db_session.query = Mock(return_value=Mock(
            filter=Mock(return_value=Mock(
                first=Mock(return_value=mock_job)
            ))
        ))

        paused = service.pause_job(1)

        assert paused is not None
        assert paused.status == JobStatus.PAUSED

    def test_pause_completed_job_returns_none(self, db_session, mock_job):
        """Should return None for terminal jobs."""
        service = MarketplaceJobService(db_session)
        mock_job.status = JobStatus.COMPLETED

        db_session.query = Mock(return_value=Mock(
            filter=Mock(return_value=Mock(
                first=Mock(return_value=mock_job)
            ))
        ))

        result = service.pause_job(1)
        assert result is None

    def test_pause_job_not_found(self, db_session):
        """Should return None when job not found."""
        service = MarketplaceJobService(db_session)

        db_session.query = Mock(return_value=Mock(
            filter=Mock(return_value=Mock(
                first=Mock(return_value=None)
            ))
        ))

        result = service.pause_job(999)
        assert result is None


# =============================================================================
# Test: resume_job
# =============================================================================


class TestResumeJob:
    """Test resume_job method."""

    def test_resume_paused_job(self, db_session, mock_job):
        """Should resume a paused job."""
        service = MarketplaceJobService(db_session)
        mock_job.status = JobStatus.PAUSED

        db_session.query = Mock(return_value=Mock(
            filter=Mock(return_value=Mock(
                first=Mock(return_value=mock_job)
            ))
        ))

        resumed = service.resume_job(1)

        assert resumed is not None
        assert resumed.status == JobStatus.PENDING
        assert resumed.expires_at is not None  # Should be reset
        db_session.flush.assert_called_once()

    def test_resume_non_paused_job_returns_none(self, db_session, mock_job):
        """Should return None for non-paused jobs."""
        service = MarketplaceJobService(db_session)
        mock_job.status = JobStatus.RUNNING

        db_session.query = Mock(return_value=Mock(
            filter=Mock(return_value=Mock(
                first=Mock(return_value=mock_job)
            ))
        ))

        result = service.resume_job(1)
        assert result is None


# =============================================================================
# Test: expire_old_jobs
# =============================================================================


class TestExpireOldJobs:
    """Test expire_old_jobs method."""

    def test_expire_old_pending_jobs(self, db_session):
        """Should expire old pending jobs."""
        service = MarketplaceJobService(db_session)

        # Create expired jobs
        expired_job1 = MarketplaceJob(
            id=1,
            marketplace="vinted",
            action_type_id=1,
            status=JobStatus.PENDING,
            expires_at=datetime.now(timezone.utc) - timedelta(hours=2),
        )
        expired_job2 = MarketplaceJob(
            id=2,
            marketplace="vinted",
            action_type_id=1,
            status=JobStatus.PAUSED,
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )

        # Use MagicMock - filter is called with 2 args at once: .filter(cond1, cond2).all()
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = [expired_job1, expired_job2]
        db_session.query = MagicMock(return_value=mock_query)

        count = service.expire_old_jobs()

        assert count == 2
        assert expired_job1.status == JobStatus.EXPIRED
        assert expired_job2.status == JobStatus.EXPIRED
        assert expired_job1.error_message == "Job expired (pending > 1h)"
        db_session.flush.assert_called_once()

    def test_expire_old_jobs_with_marketplace_filter(self, db_session):
        """Should filter by marketplace when specified."""
        service = MarketplaceJobService(db_session)

        # With marketplace filter: .filter(cond1, cond2).filter(cond3).all()
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.all.return_value = []
        db_session.query = MagicMock(return_value=mock_query)

        count = service.expire_old_jobs(marketplace="ebay")

        assert count == 0

    def test_expire_old_jobs_none_expired(self, db_session):
        """Should return 0 when no jobs expired."""
        service = MarketplaceJobService(db_session)

        # Without marketplace filter: .filter(cond1, cond2).all()
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = []
        db_session.query = MagicMock(return_value=mock_query)

        count = service.expire_old_jobs()

        assert count == 0
        # No flush should be called when nothing expired


# =============================================================================
# Test: get_pending_jobs
# =============================================================================


class TestGetPendingJobs:
    """Test get_pending_jobs method."""

    def test_get_pending_jobs_success(self, db_session):
        """Should return pending jobs ordered by priority."""
        service = MarketplaceJobService(db_session)

        jobs = [
            MarketplaceJob(id=1, marketplace="vinted", action_type_id=1, status=JobStatus.PENDING),
            MarketplaceJob(id=2, marketplace="vinted", action_type_id=1, status=JobStatus.PENDING),
        ]

        # Use MagicMock for proper chaining
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = jobs
        db_session.query = MagicMock(return_value=mock_query)

        result = service.get_pending_jobs(limit=10)

        assert len(result) == 2

    def test_get_pending_jobs_with_marketplace_filter(self, db_session):
        """Should filter by marketplace."""
        service = MarketplaceJobService(db_session)

        jobs = [
            MarketplaceJob(id=1, marketplace="ebay", action_type_id=1, status=JobStatus.PENDING),
        ]

        # Use MagicMock for proper chaining
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = jobs
        db_session.query = MagicMock(return_value=mock_query)

        result = service.get_pending_jobs(limit=10, marketplace="ebay")

        assert len(result) == 1
        assert result[0].marketplace == "ebay"


# =============================================================================
# Test: increment_retry
# =============================================================================


class TestIncrementRetry:
    """Test increment_retry method."""

    def test_increment_retry_can_retry(self, db_session, mock_job, mock_action_type):
        """Should return can_retry=True when retries available."""
        service = MarketplaceJobService(db_session)
        mock_job.retry_count = 0  # Will be 1 after increment
        mock_job.max_retries = 3

        # Mock queries using MagicMock
        def query_side_effect(model):
            if model == MarketplaceJob:
                mock_query = MagicMock()
                mock_query.filter.return_value.first.return_value = mock_job
                return mock_query
            else:
                mock_query = MagicMock()
                mock_query.filter.return_value.first.return_value = mock_action_type
                return mock_query

        db_session.query = MagicMock(side_effect=query_side_effect)

        job, can_retry = service.increment_retry(1)

        assert job is not None
        assert job.retry_count == 1
        assert can_retry is True
        db_session.flush.assert_called_once()

    def test_increment_retry_max_reached(self, db_session, mock_job, mock_action_type):
        """Should return can_retry=False when max retries reached."""
        service = MarketplaceJobService(db_session)
        mock_job.retry_count = 2  # Will be 3 after increment (== max_retries)
        mock_job.max_retries = 3
        mock_job.marketplace_batch_id = None  # No batch job to avoid extra queries
        mock_job.started_at = None  # No duration calculation
        mock_job.completed_at = None

        # Mock stats for _update_job_stats
        mock_stats = MagicMock()
        mock_stats.total_jobs = 0
        mock_stats.success_count = 0
        mock_stats.failure_count = 0
        mock_stats.avg_duration_ms = None

        def query_side_effect(model):
            if model == MarketplaceJob:
                mock_query = MagicMock()
                mock_query.filter.return_value.first.return_value = mock_job
                return mock_query
            elif model == MarketplaceActionType:
                mock_query = MagicMock()
                mock_query.filter.return_value.first.return_value = mock_action_type
                return mock_query
            else:  # MarketplaceJobStats
                mock_query = MagicMock()
                mock_query.filter.return_value.first.return_value = mock_stats
                return mock_query

        db_session.query = MagicMock(side_effect=query_side_effect)

        job, can_retry = service.increment_retry(1)

        assert job is not None
        assert job.retry_count == 3
        assert can_retry is False
        assert job.status == JobStatus.FAILED
        assert "Max retries" in job.error_message

    def test_increment_retry_job_not_found(self, db_session):
        """Should return (None, False) when job not found."""
        service = MarketplaceJobService(db_session)

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        db_session.query = MagicMock(return_value=mock_query)

        job, can_retry = service.increment_retry(999)

        assert job is None
        assert can_retry is False


# =============================================================================
# Test: get_interrupted_jobs
# =============================================================================


class TestGetInterruptedJobs:
    """Test get_interrupted_jobs method."""

    def test_get_interrupted_jobs_success(self, db_session):
        """Should return running/paused non-expired jobs."""
        service = MarketplaceJobService(db_session)

        jobs = [
            MarketplaceJob(
                id=1,
                marketplace="vinted",
                action_type_id=1,
                status=JobStatus.RUNNING,
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            ),
            MarketplaceJob(
                id=2,
                marketplace="vinted",
                action_type_id=1,
                status=JobStatus.PAUSED,
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            ),
        ]

        # Without marketplace filter: .filter(cond1, cond2).order_by(...).all()
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = jobs
        db_session.query = MagicMock(return_value=mock_query)

        result = service.get_interrupted_jobs()

        assert len(result) == 2


# =============================================================================
# Test: get_job_progress
# =============================================================================


class TestGetJobProgress:
    """Test get_job_progress method."""

    def test_get_job_progress_with_tasks(self, db_session):
        """Should calculate progress from tasks."""
        service = MarketplaceJobService(db_session)

        tasks = [
            MarketplaceTask(id=1, job_id=1, status=TaskStatus.SUCCESS),
            MarketplaceTask(id=2, job_id=1, status=TaskStatus.SUCCESS),
            MarketplaceTask(id=3, job_id=1, status=TaskStatus.FAILED),
            MarketplaceTask(id=4, job_id=1, status=TaskStatus.PENDING),
        ]

        # Use MagicMock for proper chaining
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = tasks
        db_session.query = MagicMock(return_value=mock_query)

        progress = service.get_job_progress(1)

        assert progress["total"] == 4
        assert progress["completed"] == 2
        assert progress["failed"] == 1
        assert progress["pending"] == 1
        assert progress["progress_percent"] == 50.0

    def test_get_job_progress_no_tasks(self, db_session):
        """Should return zeros when no tasks."""
        service = MarketplaceJobService(db_session)

        # Use MagicMock for proper chaining
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = []
        db_session.query = MagicMock(return_value=mock_query)

        progress = service.get_job_progress(1)

        assert progress["total"] == 0
        assert progress["completed"] == 0
        assert progress["progress_percent"] == 0


# =============================================================================
# Test: get_stats
# =============================================================================


class TestGetStats:
    """Test get_stats method."""

    def test_get_stats_success(self, db_session, mock_action_type):
        """Should return stats for the last N days."""
        service = MarketplaceJobService(db_session)

        today = datetime.now(timezone.utc).date()
        stats = [
            MarketplaceJobStats(
                id=1,
                marketplace="vinted",
                action_type_id=1,
                date=today,
                total_jobs=100,
                success_count=90,
                failure_count=10,
                avg_duration_ms=500,
            ),
        ]

        # Mock for different query models
        def query_side_effect(model):
            if model == MarketplaceJobStats:
                mock_stats_query = MagicMock()
                mock_stats_query.filter.return_value.order_by.return_value.all.return_value = stats
                return mock_stats_query
            else:
                # MarketplaceActionType query
                mock_action_query = MagicMock()
                mock_action_query.filter.return_value.first.return_value = mock_action_type
                return mock_action_query

        db_session.query = MagicMock(side_effect=query_side_effect)

        result = service.get_stats(days=7)

        assert len(result) == 1
        assert result[0]["marketplace"] == "vinted"
        assert result[0]["total_jobs"] == 100
        assert result[0]["success_count"] == 90

    def test_get_stats_with_marketplace_filter(self, db_session, mock_action_type):
        """Should filter stats by marketplace."""
        service = MarketplaceJobService(db_session)

        # Use MagicMock for proper chaining
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []
        db_session.query = MagicMock(return_value=mock_query)

        result = service.get_stats(days=7, marketplace="ebay")

        assert len(result) == 0


# =============================================================================
# Test: Action Type Caching
# =============================================================================


class TestActionTypeCaching:
    """Test action type caching."""

    def test_action_type_cached(self, db_session, mock_action_type):
        """Should cache action type after first lookup."""
        service = MarketplaceJobService(db_session)

        # .filter(cond1, cond2).first() - single filter call with 2 args
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_action_type
        db_session.query = MagicMock(return_value=mock_query)

        # First call - should query
        result1 = service.get_action_type("vinted", "publish")
        assert result1 == mock_action_type

        # Second call - should use cache
        result2 = service.get_action_type("vinted", "publish")
        assert result2 == mock_action_type

        # query should only be called once
        assert db_session.query.call_count == 1

    def test_action_type_not_found(self, db_session):
        """Should return None for unknown action type."""
        service = MarketplaceJobService(db_session)

        # .filter(cond1, cond2).first() - single filter call with 2 args
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        db_session.query = MagicMock(return_value=mock_query)

        result = service.get_action_type("vinted", "unknown")

        assert result is None
