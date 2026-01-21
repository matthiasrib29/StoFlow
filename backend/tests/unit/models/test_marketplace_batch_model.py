"""
Unit Tests for MarketplaceBatch Model

Tests for MarketplaceBatch properties and computed values.

Created: 2026-01-20
Updated: 2026-01-20 - Renamed BatchJob → MarketplaceBatch
"""

import pytest
from datetime import datetime, timezone

from models.user.marketplace_batch import MarketplaceBatch, MarketplaceBatchStatus


class TestMarketplaceBatchStatus:
    """Test MarketplaceBatchStatus enum values."""

    def test_all_status_values_exist(self):
        """Should have all expected status values."""
        expected = ["pending", "running", "completed", "partially_failed", "failed", "cancelled"]
        actual = [s.value for s in MarketplaceBatchStatus]
        assert sorted(actual) == sorted(expected)

    def test_status_string_values(self):
        """Should have correct string values."""
        assert MarketplaceBatchStatus.PENDING.value == "pending"
        assert MarketplaceBatchStatus.RUNNING.value == "running"
        assert MarketplaceBatchStatus.COMPLETED.value == "completed"
        assert MarketplaceBatchStatus.PARTIALLY_FAILED.value == "partially_failed"
        assert MarketplaceBatchStatus.FAILED.value == "failed"
        assert MarketplaceBatchStatus.CANCELLED.value == "cancelled"


class TestMarketplaceBatchProgressPercent:
    """Test progress_percent property."""

    def test_progress_percent_zero_when_no_jobs(self):
        """Should return 0% when total_count is 0."""
        batch = MarketplaceBatch(
            batch_id="test_001",
            marketplace="vinted",
            action_code="publish",
            total_count=0,
            completed_count=0,
        )
        assert batch.progress_percent == 0.0

    def test_progress_percent_zero_when_none_completed(self):
        """Should return 0% when no jobs completed."""
        batch = MarketplaceBatch(
            batch_id="test_002",
            marketplace="vinted",
            action_code="publish",
            total_count=10,
            completed_count=0,
        )
        assert batch.progress_percent == 0.0

    def test_progress_percent_100_when_all_completed(self):
        """Should return 100% when all jobs completed."""
        batch = MarketplaceBatch(
            batch_id="test_003",
            marketplace="vinted",
            action_code="publish",
            total_count=10,
            completed_count=10,
        )
        assert batch.progress_percent == 100.0

    def test_progress_percent_partial_completion(self):
        """Should calculate correct percentage for partial completion."""
        batch = MarketplaceBatch(
            batch_id="test_004",
            marketplace="vinted",
            action_code="publish",
            total_count=10,
            completed_count=7,
        )
        assert batch.progress_percent == 70.0

    def test_progress_percent_rounding(self):
        """Should round to 1 decimal place."""
        batch = MarketplaceBatch(
            batch_id="test_005",
            marketplace="vinted",
            action_code="publish",
            total_count=3,
            completed_count=1,  # 33.333...%
        )
        assert batch.progress_percent == 33.3


class TestMarketplaceBatchIsActive:
    """Test is_active property."""

    def test_pending_is_active(self):
        """PENDING batch should be active."""
        batch = MarketplaceBatch(
            batch_id="test_006",
            marketplace="vinted",
            action_code="publish",
            status=MarketplaceBatchStatus.PENDING,
        )
        assert batch.is_active is True

    def test_running_is_active(self):
        """RUNNING batch should be active."""
        batch = MarketplaceBatch(
            batch_id="test_007",
            marketplace="vinted",
            action_code="publish",
            status=MarketplaceBatchStatus.RUNNING,
        )
        assert batch.is_active is True

    def test_completed_not_active(self):
        """COMPLETED batch should not be active."""
        batch = MarketplaceBatch(
            batch_id="test_008",
            marketplace="vinted",
            action_code="publish",
            status=MarketplaceBatchStatus.COMPLETED,
        )
        assert batch.is_active is False

    def test_failed_not_active(self):
        """FAILED batch should not be active."""
        batch = MarketplaceBatch(
            batch_id="test_009",
            marketplace="vinted",
            action_code="publish",
            status=MarketplaceBatchStatus.FAILED,
        )
        assert batch.is_active is False

    def test_partially_failed_not_active(self):
        """PARTIALLY_FAILED batch should not be active."""
        batch = MarketplaceBatch(
            batch_id="test_010",
            marketplace="vinted",
            action_code="publish",
            status=MarketplaceBatchStatus.PARTIALLY_FAILED,
        )
        assert batch.is_active is False

    def test_cancelled_not_active(self):
        """CANCELLED batch should not be active."""
        batch = MarketplaceBatch(
            batch_id="test_011",
            marketplace="vinted",
            action_code="publish",
            status=MarketplaceBatchStatus.CANCELLED,
        )
        assert batch.is_active is False


class TestMarketplaceBatchIsTerminal:
    """Test is_terminal property."""

    def test_pending_not_terminal(self):
        """PENDING batch should not be terminal."""
        batch = MarketplaceBatch(
            batch_id="test_012",
            marketplace="vinted",
            action_code="publish",
            status=MarketplaceBatchStatus.PENDING,
        )
        assert batch.is_terminal is False

    def test_running_not_terminal(self):
        """RUNNING batch should not be terminal."""
        batch = MarketplaceBatch(
            batch_id="test_013",
            marketplace="vinted",
            action_code="publish",
            status=MarketplaceBatchStatus.RUNNING,
        )
        assert batch.is_terminal is False

    def test_completed_is_terminal(self):
        """COMPLETED batch should be terminal."""
        batch = MarketplaceBatch(
            batch_id="test_014",
            marketplace="vinted",
            action_code="publish",
            status=MarketplaceBatchStatus.COMPLETED,
        )
        assert batch.is_terminal is True

    def test_failed_is_terminal(self):
        """FAILED batch should be terminal."""
        batch = MarketplaceBatch(
            batch_id="test_015",
            marketplace="vinted",
            action_code="publish",
            status=MarketplaceBatchStatus.FAILED,
        )
        assert batch.is_terminal is True

    def test_partially_failed_is_terminal(self):
        """PARTIALLY_FAILED batch should be terminal."""
        batch = MarketplaceBatch(
            batch_id="test_016",
            marketplace="vinted",
            action_code="publish",
            status=MarketplaceBatchStatus.PARTIALLY_FAILED,
        )
        assert batch.is_terminal is True

    def test_cancelled_is_terminal(self):
        """CANCELLED batch should be terminal."""
        batch = MarketplaceBatch(
            batch_id="test_017",
            marketplace="vinted",
            action_code="publish",
            status=MarketplaceBatchStatus.CANCELLED,
        )
        assert batch.is_terminal is True


class TestMarketplaceBatchPendingCount:
    """Test pending_count property."""

    def test_pending_count_all_pending(self):
        """Should return total when none processed."""
        batch = MarketplaceBatch(
            batch_id="test_018",
            marketplace="vinted",
            action_code="publish",
            total_count=10,
            completed_count=0,
            failed_count=0,
            cancelled_count=0,
        )
        assert batch.pending_count == 10

    def test_pending_count_none_pending(self):
        """Should return 0 when all processed."""
        batch = MarketplaceBatch(
            batch_id="test_019",
            marketplace="vinted",
            action_code="publish",
            total_count=10,
            completed_count=7,
            failed_count=2,
            cancelled_count=1,
        )
        assert batch.pending_count == 0

    def test_pending_count_partial(self):
        """Should calculate correct pending count."""
        batch = MarketplaceBatch(
            batch_id="test_020",
            marketplace="vinted",
            action_code="publish",
            total_count=10,
            completed_count=3,
            failed_count=2,
            cancelled_count=1,
        )
        assert batch.pending_count == 4  # 10 - 3 - 2 - 1

    def test_pending_count_with_only_failures(self):
        """Should count failures in calculation."""
        batch = MarketplaceBatch(
            batch_id="test_021",
            marketplace="vinted",
            action_code="publish",
            total_count=10,
            completed_count=0,
            failed_count=5,
            cancelled_count=0,
        )
        assert batch.pending_count == 5


class TestMarketplaceBatchRepr:
    """Test __repr__ method."""

    def test_repr_format(self):
        """Should return formatted string representation."""
        batch = MarketplaceBatch(
            id=1,
            batch_id="publish_20260120_abc123",
            marketplace="vinted",
            action_code="publish",
            total_count=10,
            completed_count=5,
            status=MarketplaceBatchStatus.RUNNING,
        )
        repr_str = repr(batch)
        assert "MarketplaceBatch" in repr_str
        assert "id=1" in repr_str
        assert "publish_20260120_abc123" in repr_str
        assert "RUNNING" in repr_str


class TestMarketplaceBatchAttributes:
    """Test MarketplaceBatch required attributes."""

    def test_default_values(self):
        """Should have correct default values when explicitly set."""
        # Note: SQLAlchemy defaults are only applied at DB insert time.
        # For unit tests, we must explicitly set the values.
        batch = MarketplaceBatch(
            batch_id="test_022",
            marketplace="vinted",
            action_code="publish",
            status=MarketplaceBatchStatus.PENDING,  # Explicit for unit test
            priority=3,  # Explicit for unit test
            total_count=0,  # Explicit for unit test
            completed_count=0,  # Explicit for unit test
            failed_count=0,  # Explicit for unit test
            cancelled_count=0,  # Explicit for unit test
        )
        assert batch.status == MarketplaceBatchStatus.PENDING
        assert batch.priority == 3
        assert batch.total_count == 0
        assert batch.completed_count == 0
        assert batch.failed_count == 0
        assert batch.cancelled_count == 0

    def test_all_marketplaces_accepted(self):
        """Should accept all supported marketplaces."""
        for marketplace in ["vinted", "ebay", "etsy"]:
            batch = MarketplaceBatch(
                batch_id=f"test_{marketplace}",
                marketplace=marketplace,
                action_code="publish",
            )
            assert batch.marketplace == marketplace

    def test_timestamps_nullable(self):
        """Should allow null timestamps."""
        batch = MarketplaceBatch(
            batch_id="test_023",
            marketplace="vinted",
            action_code="publish",
        )
        assert batch.started_at is None
        assert batch.completed_at is None
        assert batch.created_by_user_id is None
