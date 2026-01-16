"""
Unit Tests for VintedJobStatsService

Tests for the Vinted job statistics service that tracks and retrieves
job performance metrics.

Coverage target: >80%

Author: Claude
Date: 2026-01-16
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
import pytest

from models.user.marketplace_job import MarketplaceJob, JobStatus
from models.user.vinted_job_stats import VintedJobStats
from models.vinted.vinted_action_type import VintedActionType
from services.vinted.vinted_job_stats_service import VintedJobStatsService


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_db():
    """Mock SQLAlchemy session."""
    db = MagicMock()
    return db


@pytest.fixture
def mock_job():
    """Mock MarketplaceJob instance."""
    job = MagicMock(spec=MarketplaceJob)
    job.id = 1
    job.action_type_id = 10
    job.status = JobStatus.COMPLETED
    job.started_at = datetime(2026, 1, 16, 10, 0, 0, tzinfo=timezone.utc)
    job.completed_at = datetime(2026, 1, 16, 10, 1, 30, tzinfo=timezone.utc)  # 90 seconds = 90000 ms
    return job


@pytest.fixture
def mock_stats():
    """Mock VintedJobStats instance."""
    stats = MagicMock(spec=VintedJobStats)
    stats.id = 1
    stats.action_type_id = 10
    stats.date = datetime.now(timezone.utc).date()
    stats.total_jobs = 5
    stats.success_count = 4
    stats.failure_count = 1
    stats.avg_duration_ms = 60000  # 60 seconds
    stats.success_rate = 80.0
    return stats


@pytest.fixture
def mock_action_type():
    """Mock VintedActionType instance."""
    action_type = MagicMock(spec=VintedActionType)
    action_type.id = 10
    action_type.code = "publish"
    action_type.name = "Publish Product"
    return action_type


# =============================================================================
# TESTS - UPDATE JOB STATS
# =============================================================================


class TestUpdateJobStats:
    """Tests for update_job_stats method."""

    @patch('services.vinted.vinted_job_stats_service.VintedJobStats')
    def test_update_stats_creates_new_record_when_none_exists(self, mock_stats_class, mock_db, mock_job):
        """Test creating a new stats record when none exists for today."""
        # Setup: No existing stats
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Mock the VintedJobStats constructor
        mock_new_stats = MagicMock()
        mock_new_stats.total_jobs = 0
        mock_new_stats.success_count = 0
        mock_new_stats.failure_count = 0
        mock_new_stats.avg_duration_ms = None
        mock_stats_class.return_value = mock_new_stats

        # Execute
        VintedJobStatsService.update_job_stats(mock_db, mock_job, success=True)

        # Verify: New stats record was created with correct fields
        mock_stats_class.assert_called_once()
        call_kwargs = mock_stats_class.call_args[1]
        assert call_kwargs['action_type_id'] == mock_job.action_type_id
        assert call_kwargs['total_jobs'] == 0
        assert call_kwargs['success_count'] == 0
        assert call_kwargs['failure_count'] == 0

        # Verify: Stats was added and committed
        mock_db.add.assert_called_once_with(mock_new_stats)
        mock_db.commit.assert_called_once()

    def test_update_stats_increments_success_count_for_successful_job(
        self, mock_db, mock_stats
    ):
        """Test incrementing success count for a successful job."""
        # Setup: Existing stats
        mock_db.query.return_value.filter.return_value.first.return_value = mock_stats
        mock_stats.total_jobs = 5
        mock_stats.success_count = 4

        mock_job = MagicMock(spec=MarketplaceJob)
        mock_job.action_type_id = 10
        mock_job.started_at = datetime(2026, 1, 16, 10, 0, 0, tzinfo=timezone.utc)
        mock_job.completed_at = datetime(2026, 1, 16, 10, 1, 0, tzinfo=timezone.utc)

        # Execute
        VintedJobStatsService.update_job_stats(mock_db, mock_job, success=True)

        # Verify: Counts were incremented correctly
        assert mock_stats.total_jobs == 6
        assert mock_stats.success_count == 5
        mock_db.commit.assert_called_once()

    def test_update_stats_increments_failure_count_for_failed_job(
        self, mock_db, mock_stats
    ):
        """Test incrementing failure count for a failed job."""
        # Setup: Existing stats
        mock_db.query.return_value.filter.return_value.first.return_value = mock_stats
        mock_stats.total_jobs = 5
        mock_stats.failure_count = 1

        mock_job = MagicMock(spec=MarketplaceJob)
        mock_job.action_type_id = 10
        mock_job.started_at = datetime(2026, 1, 16, 10, 0, 0, tzinfo=timezone.utc)
        mock_job.completed_at = datetime(2026, 1, 16, 10, 1, 0, tzinfo=timezone.utc)

        # Execute
        VintedJobStatsService.update_job_stats(mock_db, mock_job, success=False)

        # Verify: Failure count was incremented
        assert mock_stats.total_jobs == 6
        assert mock_stats.failure_count == 2
        mock_db.commit.assert_called_once()

    def test_update_stats_calculates_avg_duration_for_first_job(self, mock_db):
        """Test calculating average duration for the first job."""
        # Setup: New stats record
        mock_stats = MagicMock(spec=VintedJobStats)
        mock_stats.total_jobs = 0
        mock_stats.avg_duration_ms = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_stats

        mock_job = MagicMock(spec=MarketplaceJob)
        mock_job.action_type_id = 10
        mock_job.started_at = datetime(2026, 1, 16, 10, 0, 0, tzinfo=timezone.utc)
        mock_job.completed_at = datetime(2026, 1, 16, 10, 1, 30, tzinfo=timezone.utc)  # 90 seconds

        # Execute
        VintedJobStatsService.update_job_stats(mock_db, mock_job, success=True)

        # Verify: Average duration is set to job duration
        assert mock_stats.avg_duration_ms == 90000  # 90 seconds in milliseconds
        mock_db.commit.assert_called_once()

    def test_update_stats_calculates_rolling_average_duration(self, mock_db, mock_stats):
        """Test calculating rolling average duration for subsequent jobs."""
        # Setup: Existing stats with avg_duration_ms
        mock_db.query.return_value.filter.return_value.first.return_value = mock_stats
        mock_stats.total_jobs = 5
        mock_stats.avg_duration_ms = 60000  # Previous average: 60 seconds

        mock_job = MagicMock(spec=MarketplaceJob)
        mock_job.action_type_id = 10
        mock_job.started_at = datetime(2026, 1, 16, 10, 0, 0, tzinfo=timezone.utc)
        mock_job.completed_at = datetime(2026, 1, 16, 10, 2, 0, tzinfo=timezone.utc)  # 120 seconds

        # Execute
        VintedJobStatsService.update_job_stats(mock_db, mock_job, success=True)

        # Verify: Rolling average is calculated correctly
        # Expected: (60000 * 5 + 120000) / 6 = 70000
        expected_avg = int((60000 * 5 + 120000) / 6)
        assert mock_stats.avg_duration_ms == expected_avg
        mock_db.commit.assert_called_once()

    def test_update_stats_skips_duration_when_timestamps_missing(self, mock_db, mock_stats):
        """Test that duration calculation is skipped when timestamps are missing."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = mock_stats
        mock_stats.avg_duration_ms = 60000

        mock_job = MagicMock(spec=MarketplaceJob)
        mock_job.action_type_id = 10
        mock_job.started_at = None  # Missing timestamp
        mock_job.completed_at = None

        # Execute
        VintedJobStatsService.update_job_stats(mock_db, mock_job, success=True)

        # Verify: Average duration unchanged
        assert mock_stats.avg_duration_ms == 60000
        mock_db.commit.assert_called_once()


# =============================================================================
# TESTS - GET STATS
# =============================================================================


class TestGetStats:
    """Tests for get_stats method."""

    def test_get_stats_returns_empty_list_when_no_data(self, mock_db):
        """Test returning empty list when no stats exist."""
        # Setup: No stats records
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        # Execute
        result = VintedJobStatsService.get_stats(mock_db, days=7)

        # Verify
        assert result == []

    def test_get_stats_queries_last_n_days(self, mock_db):
        """Test that stats are queried for the last N days."""
        # Setup
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        # Execute
        result = VintedJobStatsService.get_stats(mock_db, days=7)

        # Verify: Query was made for VintedJobStats and empty result returned
        mock_db.query.assert_any_call(VintedJobStats)
        assert result == []

    def test_get_stats_returns_formatted_data_with_action_types(
        self, mock_db, mock_stats, mock_action_type
    ):
        """Test returning formatted stats with action type information."""
        # Setup
        mock_stats.date = datetime(2026, 1, 16).date()
        mock_stats.action_type_id = 10
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_stats
        ]

        # Mock action type query for N+1 optimization
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_action_type]

        # Execute
        result = VintedJobStatsService.get_stats(mock_db, days=7)

        # Verify
        assert len(result) == 1
        assert result[0]["date"] == "2026-01-16"
        assert result[0]["action_code"] == "publish"
        assert result[0]["action_name"] == "Publish Product"
        assert result[0]["total_jobs"] == 5
        assert result[0]["success_count"] == 4
        assert result[0]["failure_count"] == 1
        assert result[0]["success_rate"] == 80.0
        assert result[0]["avg_duration_ms"] == 60000

    def test_get_stats_uses_provided_action_type_resolver(self, mock_db, mock_stats):
        """Test using a provided action_type_resolver function."""
        # Setup
        mock_stats.date = datetime(2026, 1, 16).date()
        mock_stats.action_type_id = 10
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_stats
        ]

        # Custom resolver
        def custom_resolver(action_type_id):
            action_type = MagicMock()
            action_type.code = "custom_action"
            action_type.name = "Custom Action"
            return action_type

        # Execute
        result = VintedJobStatsService.get_stats(
            mock_db, days=7, action_type_resolver=custom_resolver
        )

        # Verify: Custom resolver was used
        assert result[0]["action_code"] == "custom_action"
        assert result[0]["action_name"] == "Custom Action"

    def test_get_stats_handles_missing_action_types(self, mock_db, mock_stats):
        """Test handling when action type is not found."""
        # Setup
        mock_stats.date = datetime(2026, 1, 16).date()
        mock_stats.action_type_id = 999  # Non-existent
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_stats
        ]

        # Mock empty action types query
        mock_db.query.return_value.filter.return_value.all.return_value = []

        # Execute
        result = VintedJobStatsService.get_stats(mock_db, days=7)

        # Verify: Uses "unknown" for missing action types
        assert result[0]["action_code"] == "unknown"
        assert result[0]["action_name"] == "Unknown"


# =============================================================================
# TESTS - GET DAILY SUMMARY
# =============================================================================


class TestGetDailySummary:
    """Tests for get_daily_summary method."""

    def test_get_daily_summary_returns_empty_summary_when_no_data(self, mock_db):
        """Test returning empty summary when no stats exist for the date."""
        # Setup: No stats records
        mock_db.query.return_value.filter.return_value.all.return_value = []

        # Execute
        result = VintedJobStatsService.get_daily_summary(mock_db)

        # Verify: Empty summary with zero counts
        assert result["total_jobs"] == 0
        assert result["success_count"] == 0
        assert result["failure_count"] == 0
        assert result["success_rate"] == 0.0
        assert result["by_action"] == []

    def test_get_daily_summary_defaults_to_today(self, mock_db):
        """Test that summary defaults to today's date when no date provided."""
        # Setup
        mock_db.query.return_value.filter.return_value.all.return_value = []

        # Execute
        result = VintedJobStatsService.get_daily_summary(mock_db)

        # Verify: Date is today
        today = datetime.now(timezone.utc).date()
        assert result["date"] == today.isoformat()

    def test_get_daily_summary_accepts_datetime_object(self, mock_db):
        """Test accepting datetime object and converting to date."""
        # Setup
        mock_db.query.return_value.filter.return_value.all.return_value = []
        test_datetime = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

        # Execute
        result = VintedJobStatsService.get_daily_summary(mock_db, date=test_datetime)

        # Verify: Date extracted from datetime
        assert result["date"] == "2026-01-15"

    def test_get_daily_summary_aggregates_multiple_action_types(
        self, mock_db, mock_action_type
    ):
        """Test aggregating stats across multiple action types."""
        # Setup: Multiple stats records for different actions
        stats1 = MagicMock(spec=VintedJobStats)
        stats1.action_type_id = 10
        stats1.total_jobs = 5
        stats1.success_count = 4
        stats1.failure_count = 1
        stats1.success_rate = 80.0

        stats2 = MagicMock(spec=VintedJobStats)
        stats2.action_type_id = 20
        stats2.total_jobs = 10
        stats2.success_count = 9
        stats2.failure_count = 1
        stats2.success_rate = 90.0

        mock_db.query.return_value.filter.return_value.all.side_effect = [
            [stats1, stats2],  # First call: all stats
            [mock_action_type],  # Second call: action type for stats1
            [mock_action_type],  # Third call: action type for stats2
        ]

        # Execute
        result = VintedJobStatsService.get_daily_summary(mock_db)

        # Verify: Aggregated totals
        assert result["total_jobs"] == 15  # 5 + 10
        assert result["success_count"] == 13  # 4 + 9
        assert result["failure_count"] == 2  # 1 + 1
        assert result["success_rate"] == 86.7  # (13 / 15) * 100, rounded to 1 decimal

        # Verify: By-action breakdown
        assert len(result["by_action"]) == 2
        assert result["by_action"][0]["total_jobs"] == 5
        assert result["by_action"][1]["total_jobs"] == 10

    def test_get_daily_summary_handles_zero_total_jobs(self, mock_db):
        """Test handling division by zero when no jobs exist."""
        # Setup: Empty stats
        mock_db.query.return_value.filter.return_value.all.return_value = []

        # Execute
        result = VintedJobStatsService.get_daily_summary(mock_db)

        # Verify: Success rate is 0.0 (no division by zero error)
        assert result["success_rate"] == 0.0

    def test_get_daily_summary_includes_action_details(self, mock_db):
        """Test that by_action includes detailed action information."""
        # Setup
        mock_stats = MagicMock(spec=VintedJobStats)
        mock_stats.action_type_id = 10
        mock_stats.total_jobs = 5
        mock_stats.success_count = 4
        mock_stats.failure_count = 1
        mock_stats.success_rate = 80.0

        mock_action_type = MagicMock(spec=VintedActionType)
        mock_action_type.code = "publish"
        mock_action_type.name = "Publish Product"

        # Mock query chain for stats
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_stats]

        # Mock query for action type (called inside the loop)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_action_type

        # Execute
        result = VintedJobStatsService.get_daily_summary(mock_db)

        # Verify: By-action details
        assert len(result["by_action"]) == 1
        action_detail = result["by_action"][0]
        assert action_detail["action_code"] == "publish"
        assert action_detail["total_jobs"] == 5
        assert action_detail["success_count"] == 4
        assert action_detail["failure_count"] == 1
        assert action_detail["success_rate"] == 80.0


# =============================================================================
# INTEGRATION SMOKE TESTS
# =============================================================================


class TestVintedJobStatsServiceSmoke:
    """Smoke tests for overall service functionality."""

    def test_service_has_all_required_methods(self):
        """Test that service has all expected public methods."""
        assert hasattr(VintedJobStatsService, "update_job_stats")
        assert hasattr(VintedJobStatsService, "get_stats")
        assert hasattr(VintedJobStatsService, "get_daily_summary")

    def test_all_methods_are_static(self):
        """Test that all public methods are static."""
        assert isinstance(
            VintedJobStatsService.__dict__["update_job_stats"], staticmethod
        )
        assert isinstance(VintedJobStatsService.__dict__["get_stats"], staticmethod)
        assert isinstance(
            VintedJobStatsService.__dict__["get_daily_summary"], staticmethod
        )
