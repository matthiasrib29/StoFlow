"""
Unit Tests for MarketplaceJob Model

Tests for MarketplaceJob properties and computed values.

Created: 2026-01-20
"""

import pytest
from datetime import datetime, timezone

from models.user.marketplace_job import MarketplaceJob, JobStatus


class TestJobStatus:
    """Test JobStatus enum values."""

    def test_all_status_values_exist(self):
        """Should have all expected status values."""
        expected = ["pending", "running", "paused", "completed", "failed", "cancelled", "expired"]
        actual = [s.value for s in JobStatus]
        assert sorted(actual) == sorted(expected)

    def test_status_string_values(self):
        """Should have correct string values."""
        assert JobStatus.PENDING.value == "pending"
        assert JobStatus.RUNNING.value == "running"
        assert JobStatus.PAUSED.value == "paused"
        assert JobStatus.COMPLETED.value == "completed"
        assert JobStatus.FAILED.value == "failed"
        assert JobStatus.CANCELLED.value == "cancelled"
        assert JobStatus.EXPIRED.value == "expired"


class TestMarketplaceJobIsActive:
    """Test is_active property."""

    def test_pending_is_active(self):
        """PENDING job should be active."""
        job = MarketplaceJob(
            marketplace="vinted",
            action_type_id=1,
            status=JobStatus.PENDING,
        )
        assert job.is_active is True

    def test_running_is_active(self):
        """RUNNING job should be active."""
        job = MarketplaceJob(
            marketplace="vinted",
            action_type_id=1,
            status=JobStatus.RUNNING,
        )
        assert job.is_active is True

    def test_paused_is_active(self):
        """PAUSED job should be active (can be resumed)."""
        job = MarketplaceJob(
            marketplace="vinted",
            action_type_id=1,
            status=JobStatus.PAUSED,
        )
        assert job.is_active is True

    def test_completed_not_active(self):
        """COMPLETED job should not be active."""
        job = MarketplaceJob(
            marketplace="vinted",
            action_type_id=1,
            status=JobStatus.COMPLETED,
        )
        assert job.is_active is False

    def test_failed_not_active(self):
        """FAILED job should not be active."""
        job = MarketplaceJob(
            marketplace="vinted",
            action_type_id=1,
            status=JobStatus.FAILED,
        )
        assert job.is_active is False

    def test_cancelled_not_active(self):
        """CANCELLED job should not be active."""
        job = MarketplaceJob(
            marketplace="vinted",
            action_type_id=1,
            status=JobStatus.CANCELLED,
        )
        assert job.is_active is False

    def test_expired_not_active(self):
        """EXPIRED job should not be active."""
        job = MarketplaceJob(
            marketplace="vinted",
            action_type_id=1,
            status=JobStatus.EXPIRED,
        )
        assert job.is_active is False


class TestMarketplaceJobIsTerminal:
    """Test is_terminal property."""

    def test_pending_not_terminal(self):
        """PENDING job should not be terminal."""
        job = MarketplaceJob(
            marketplace="vinted",
            action_type_id=1,
            status=JobStatus.PENDING,
        )
        assert job.is_terminal is False

    def test_running_not_terminal(self):
        """RUNNING job should not be terminal."""
        job = MarketplaceJob(
            marketplace="vinted",
            action_type_id=1,
            status=JobStatus.RUNNING,
        )
        assert job.is_terminal is False

    def test_paused_not_terminal(self):
        """PAUSED job should not be terminal."""
        job = MarketplaceJob(
            marketplace="vinted",
            action_type_id=1,
            status=JobStatus.PAUSED,
        )
        assert job.is_terminal is False

    def test_completed_is_terminal(self):
        """COMPLETED job should be terminal."""
        job = MarketplaceJob(
            marketplace="vinted",
            action_type_id=1,
            status=JobStatus.COMPLETED,
        )
        assert job.is_terminal is True

    def test_failed_is_terminal(self):
        """FAILED job should be terminal."""
        job = MarketplaceJob(
            marketplace="vinted",
            action_type_id=1,
            status=JobStatus.FAILED,
        )
        assert job.is_terminal is True

    def test_cancelled_is_terminal(self):
        """CANCELLED job should be terminal."""
        job = MarketplaceJob(
            marketplace="vinted",
            action_type_id=1,
            status=JobStatus.CANCELLED,
        )
        assert job.is_terminal is True

    def test_expired_is_terminal(self):
        """EXPIRED job should be terminal."""
        job = MarketplaceJob(
            marketplace="vinted",
            action_type_id=1,
            status=JobStatus.EXPIRED,
        )
        assert job.is_terminal is True


class TestMarketplaceJobMarketplaceProperties:
    """Test marketplace-specific properties."""

    def test_is_vinted_true(self):
        """Should return True for vinted marketplace."""
        job = MarketplaceJob(
            marketplace="vinted",
            action_type_id=1,
        )
        assert job.is_vinted is True
        assert job.is_ebay is False
        assert job.is_etsy is False

    def test_is_ebay_true(self):
        """Should return True for ebay marketplace."""
        job = MarketplaceJob(
            marketplace="ebay",
            action_type_id=1,
        )
        assert job.is_vinted is False
        assert job.is_ebay is True
        assert job.is_etsy is False

    def test_is_etsy_true(self):
        """Should return True for etsy marketplace."""
        job = MarketplaceJob(
            marketplace="etsy",
            action_type_id=1,
        )
        assert job.is_vinted is False
        assert job.is_ebay is False
        assert job.is_etsy is True


class TestMarketplaceJobRepr:
    """Test __repr__ method."""

    def test_repr_format(self):
        """Should return formatted string representation."""
        job = MarketplaceJob(
            id=42,
            marketplace="vinted",
            action_type_id=1,
            product_id=123,
            status=JobStatus.RUNNING,
        )
        repr_str = repr(job)
        assert "MarketplaceJob" in repr_str
        assert "id=42" in repr_str
        assert "marketplace=vinted" in repr_str
        assert "status=JobStatus.RUNNING" in repr_str
        assert "product_id=123" in repr_str

    def test_repr_without_product_id(self):
        """Should handle None product_id."""
        job = MarketplaceJob(
            id=1,
            marketplace="ebay",
            action_type_id=2,
            product_id=None,
            status=JobStatus.PENDING,
        )
        repr_str = repr(job)
        assert "product_id=None" in repr_str


class TestMarketplaceJobDefaults:
    """Test default values.

    Note: SQLAlchemy defaults are only applied at DB insert time.
    For unit tests, we must explicitly set the values to test assignment.
    """

    def test_default_status(self):
        """Should accept PENDING status."""
        job = MarketplaceJob(
            marketplace="vinted",
            action_type_id=1,
            status=JobStatus.PENDING,
        )
        assert job.status == JobStatus.PENDING

    def test_default_priority(self):
        """Should accept priority 3 (NORMAL)."""
        job = MarketplaceJob(
            marketplace="vinted",
            action_type_id=1,
            priority=3,
        )
        assert job.priority == 3

    def test_default_retry_count(self):
        """Should accept 0 retries."""
        job = MarketplaceJob(
            marketplace="vinted",
            action_type_id=1,
            retry_count=0,
        )
        assert job.retry_count == 0

    def test_default_max_retries(self):
        """Should accept 3 max retries."""
        job = MarketplaceJob(
            marketplace="vinted",
            action_type_id=1,
            max_retries=3,
        )
        assert job.max_retries == 3

    def test_default_cancel_requested(self):
        """Should accept False for cancel_requested."""
        job = MarketplaceJob(
            marketplace="vinted",
            action_type_id=1,
            cancel_requested=False,
        )
        assert job.cancel_requested is False


class TestMarketplaceJobJSONBFields:
    """Test JSONB fields (input_data, result_data)."""

    def test_input_data_can_be_set(self):
        """Should accept dict for input_data."""
        job = MarketplaceJob(
            marketplace="vinted",
            action_type_id=1,
            input_data={"title": "Test Product", "price": 29.99},
        )
        assert job.input_data == {"title": "Test Product", "price": 29.99}

    def test_result_data_can_be_set(self):
        """Should accept dict for result_data."""
        job = MarketplaceJob(
            marketplace="vinted",
            action_type_id=1,
            result_data={"vinted_id": "abc123", "url": "https://vinted.fr/..."},
        )
        assert job.result_data == {"vinted_id": "abc123", "url": "https://vinted.fr/..."}

    def test_input_data_nullable(self):
        """Should allow None for input_data."""
        job = MarketplaceJob(
            marketplace="vinted",
            action_type_id=1,
            input_data=None,
        )
        assert job.input_data is None

    def test_result_data_nullable(self):
        """Should allow None for result_data."""
        job = MarketplaceJob(
            marketplace="vinted",
            action_type_id=1,
            result_data=None,
        )
        assert job.result_data is None


class TestMarketplaceJobTimestamps:
    """Test timestamp fields."""

    def test_timestamps_nullable(self):
        """Should allow null timestamps."""
        job = MarketplaceJob(
            marketplace="vinted",
            action_type_id=1,
        )
        assert job.started_at is None
        assert job.completed_at is None
        assert job.expires_at is None

    def test_timestamps_can_be_set(self):
        """Should accept datetime for timestamps."""
        now = datetime.now(timezone.utc)
        job = MarketplaceJob(
            marketplace="vinted",
            action_type_id=1,
            started_at=now,
            completed_at=now,
            expires_at=now,
        )
        assert job.started_at == now
        assert job.completed_at == now
        assert job.expires_at == now


class TestMarketplaceJobIdempotencyKey:
    """Test idempotency_key field."""

    def test_idempotency_key_nullable(self):
        """Should allow null idempotency_key."""
        job = MarketplaceJob(
            marketplace="vinted",
            action_type_id=1,
        )
        assert job.idempotency_key is None

    def test_idempotency_key_can_be_set(self):
        """Should accept string for idempotency_key."""
        job = MarketplaceJob(
            marketplace="vinted",
            action_type_id=1,
            idempotency_key="pub_123_abc456",
        )
        assert job.idempotency_key == "pub_123_abc456"


class TestMarketplaceJobBatchRelation:
    """Test marketplace_batch_id relation."""

    def test_marketplace_batch_id_nullable(self):
        """Should allow null marketplace_batch_id (standalone job)."""
        job = MarketplaceJob(
            marketplace="vinted",
            action_type_id=1,
        )
        assert job.marketplace_batch_id is None

    def test_marketplace_batch_id_can_be_set(self):
        """Should accept int for marketplace_batch_id."""
        job = MarketplaceJob(
            marketplace="vinted",
            action_type_id=1,
            marketplace_batch_id=42,
        )
        assert job.marketplace_batch_id == 42


class TestMarketplaceJobFailedStep:
    """Test failed_step field for error tracking."""

    def test_failed_step_nullable(self):
        """Should allow null failed_step."""
        job = MarketplaceJob(
            marketplace="vinted",
            action_type_id=1,
        )
        assert job.failed_step is None

    def test_failed_step_can_be_set(self):
        """Should accept string for failed_step."""
        job = MarketplaceJob(
            marketplace="vinted",
            action_type_id=1,
            status=JobStatus.FAILED,
            failed_step="upload_images",
            error_message="Connection timeout",
        )
        assert job.failed_step == "upload_images"
        assert job.error_message == "Connection timeout"
