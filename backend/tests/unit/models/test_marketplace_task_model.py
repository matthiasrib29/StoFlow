"""
Unit Tests for MarketplaceTask Model

Tests for MarketplaceTask properties and computed values.

Created: 2026-01-20
"""

import pytest
from datetime import datetime, timezone

from models.user.marketplace_task import MarketplaceTask, MarketplaceTaskType, TaskStatus


class TestTaskStatus:
    """Test TaskStatus enum values."""

    def test_all_status_values_exist(self):
        """Should have all expected status values."""
        expected = ["pending", "processing", "success", "failed", "timeout", "cancelled"]
        actual = [s.value for s in TaskStatus]
        assert sorted(actual) == sorted(expected)

    def test_status_string_values(self):
        """Should have correct string values."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.PROCESSING.value == "processing"
        assert TaskStatus.SUCCESS.value == "success"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.TIMEOUT.value == "timeout"
        assert TaskStatus.CANCELLED.value == "cancelled"


class TestMarketplaceTaskType:
    """Test MarketplaceTaskType enum values."""

    def test_all_task_types_exist(self):
        """Should have all expected task types."""
        expected = ["plugin_http", "direct_http", "db_operation", "file_operation"]
        actual = [t.value for t in MarketplaceTaskType]
        assert sorted(actual) == sorted(expected)

    def test_task_type_string_values(self):
        """Should have correct string values."""
        assert MarketplaceTaskType.PLUGIN_HTTP.value == "plugin_http"
        assert MarketplaceTaskType.DIRECT_HTTP.value == "direct_http"
        assert MarketplaceTaskType.DB_OPERATION.value == "db_operation"
        assert MarketplaceTaskType.FILE_OPERATION.value == "file_operation"


class TestMarketplaceTaskIsPluginTask:
    """Test is_plugin_task property."""

    def test_plugin_http_is_plugin_task(self):
        """PLUGIN_HTTP task should be a plugin task."""
        task = MarketplaceTask(
            task_type=MarketplaceTaskType.PLUGIN_HTTP,
            status=TaskStatus.PENDING,
        )
        assert task.is_plugin_task is True

    def test_direct_http_not_plugin_task(self):
        """DIRECT_HTTP task should not be a plugin task."""
        task = MarketplaceTask(
            task_type=MarketplaceTaskType.DIRECT_HTTP,
            status=TaskStatus.PENDING,
        )
        assert task.is_plugin_task is False

    def test_db_operation_not_plugin_task(self):
        """DB_OPERATION task should not be a plugin task."""
        task = MarketplaceTask(
            task_type=MarketplaceTaskType.DB_OPERATION,
            status=TaskStatus.PENDING,
        )
        assert task.is_plugin_task is False

    def test_file_operation_not_plugin_task(self):
        """FILE_OPERATION task should not be a plugin task."""
        task = MarketplaceTask(
            task_type=MarketplaceTaskType.FILE_OPERATION,
            status=TaskStatus.PENDING,
        )
        assert task.is_plugin_task is False

    def test_none_task_type_not_plugin_task(self):
        """None task_type should not be a plugin task."""
        task = MarketplaceTask(
            task_type=None,
            status=TaskStatus.PENDING,
        )
        assert task.is_plugin_task is False


class TestMarketplaceTaskIsActive:
    """Test is_active property."""

    def test_pending_is_active(self):
        """PENDING task should be active."""
        task = MarketplaceTask(
            task_type=MarketplaceTaskType.PLUGIN_HTTP,
            status=TaskStatus.PENDING,
        )
        assert task.is_active is True

    def test_processing_is_active(self):
        """PROCESSING task should be active."""
        task = MarketplaceTask(
            task_type=MarketplaceTaskType.PLUGIN_HTTP,
            status=TaskStatus.PROCESSING,
        )
        assert task.is_active is True

    def test_success_not_active(self):
        """SUCCESS task should not be active."""
        task = MarketplaceTask(
            task_type=MarketplaceTaskType.PLUGIN_HTTP,
            status=TaskStatus.SUCCESS,
        )
        assert task.is_active is False

    def test_failed_not_active(self):
        """FAILED task should not be active."""
        task = MarketplaceTask(
            task_type=MarketplaceTaskType.PLUGIN_HTTP,
            status=TaskStatus.FAILED,
        )
        assert task.is_active is False

    def test_timeout_not_active(self):
        """TIMEOUT task should not be active."""
        task = MarketplaceTask(
            task_type=MarketplaceTaskType.PLUGIN_HTTP,
            status=TaskStatus.TIMEOUT,
        )
        assert task.is_active is False

    def test_cancelled_not_active(self):
        """CANCELLED task should not be active."""
        task = MarketplaceTask(
            task_type=MarketplaceTaskType.PLUGIN_HTTP,
            status=TaskStatus.CANCELLED,
        )
        assert task.is_active is False


class TestMarketplaceTaskIsTerminal:
    """Test is_terminal property."""

    def test_pending_not_terminal(self):
        """PENDING task should not be terminal."""
        task = MarketplaceTask(
            task_type=MarketplaceTaskType.PLUGIN_HTTP,
            status=TaskStatus.PENDING,
        )
        assert task.is_terminal is False

    def test_processing_not_terminal(self):
        """PROCESSING task should not be terminal."""
        task = MarketplaceTask(
            task_type=MarketplaceTaskType.PLUGIN_HTTP,
            status=TaskStatus.PROCESSING,
        )
        assert task.is_terminal is False

    def test_success_is_terminal(self):
        """SUCCESS task should be terminal."""
        task = MarketplaceTask(
            task_type=MarketplaceTaskType.PLUGIN_HTTP,
            status=TaskStatus.SUCCESS,
        )
        assert task.is_terminal is True

    def test_failed_is_terminal(self):
        """FAILED task should be terminal."""
        task = MarketplaceTask(
            task_type=MarketplaceTaskType.PLUGIN_HTTP,
            status=TaskStatus.FAILED,
        )
        assert task.is_terminal is True

    def test_timeout_is_terminal(self):
        """TIMEOUT task should be terminal."""
        task = MarketplaceTask(
            task_type=MarketplaceTaskType.PLUGIN_HTTP,
            status=TaskStatus.TIMEOUT,
        )
        assert task.is_terminal is True

    def test_cancelled_is_terminal(self):
        """CANCELLED task should be terminal."""
        task = MarketplaceTask(
            task_type=MarketplaceTaskType.PLUGIN_HTTP,
            status=TaskStatus.CANCELLED,
        )
        assert task.is_terminal is True


class TestMarketplaceTaskRepr:
    """Test __repr__ method."""

    def test_repr_with_description(self):
        """Should include description in repr when available."""
        task = MarketplaceTask(
            id=1,
            task_type=MarketplaceTaskType.PLUGIN_HTTP,
            description="Upload image 1/3",
            status=TaskStatus.PROCESSING,
        )
        repr_str = repr(task)
        assert "MarketplaceTask" in repr_str
        assert "id=1" in repr_str
        assert "Upload image 1/3" in repr_str
        assert "TaskStatus.PROCESSING" in repr_str

    def test_repr_without_description(self):
        """Should use task_type value when no description."""
        task = MarketplaceTask(
            id=2,
            task_type=MarketplaceTaskType.DIRECT_HTTP,
            description=None,
            status=TaskStatus.PENDING,
        )
        repr_str = repr(task)
        assert "direct_http" in repr_str


class TestMarketplaceTaskDefaults:
    """Test default values.

    Note: SQLAlchemy defaults are only applied at DB insert time.
    For unit tests, we must explicitly set the values.
    """

    def test_default_status(self):
        """Should accept PENDING status."""
        task = MarketplaceTask(status=TaskStatus.PENDING)
        assert task.status == TaskStatus.PENDING

    def test_default_retry_count(self):
        """Should accept 0 retries."""
        task = MarketplaceTask(status=TaskStatus.PENDING, retry_count=0)
        assert task.retry_count == 0


class TestMarketplaceTaskJSONFields:
    """Test JSON fields (payload, result)."""

    def test_payload_can_be_set(self):
        """Should accept dict for payload."""
        task = MarketplaceTask(
            task_type=MarketplaceTaskType.PLUGIN_HTTP,
            payload={"product_id": 123, "title": "Test"},
        )
        assert task.payload == {"product_id": 123, "title": "Test"}

    def test_result_can_be_set(self):
        """Should accept dict for result."""
        task = MarketplaceTask(
            task_type=MarketplaceTaskType.PLUGIN_HTTP,
            result={"vinted_id": "abc123", "success": True},
        )
        assert task.result == {"vinted_id": "abc123", "success": True}

    def test_payload_nullable(self):
        """Should allow None for payload."""
        task = MarketplaceTask(
            task_type=MarketplaceTaskType.PLUGIN_HTTP,
            payload=None,
        )
        assert task.payload is None

    def test_result_nullable(self):
        """Should allow None for result."""
        task = MarketplaceTask(
            task_type=MarketplaceTaskType.PLUGIN_HTTP,
            result=None,
        )
        assert task.result is None


class TestMarketplaceTaskHTTPFields:
    """Test HTTP-related fields."""

    def test_http_fields_can_be_set(self):
        """Should accept HTTP-related fields."""
        task = MarketplaceTask(
            task_type=MarketplaceTaskType.DIRECT_HTTP,
            platform="ebay",
            http_method="POST",
            path="/api/v1/listings",
        )
        assert task.platform == "ebay"
        assert task.http_method == "POST"
        assert task.path == "/api/v1/listings"

    def test_http_fields_nullable(self):
        """Should allow null HTTP fields."""
        task = MarketplaceTask(
            task_type=MarketplaceTaskType.DB_OPERATION,
        )
        assert task.platform is None
        assert task.http_method is None
        assert task.path is None


class TestMarketplaceTaskTimestamps:
    """Test timestamp fields."""

    def test_timestamps_nullable(self):
        """Should allow null timestamps."""
        task = MarketplaceTask()
        assert task.started_at is None
        assert task.completed_at is None

    def test_timestamps_can_be_set(self):
        """Should accept datetime for timestamps."""
        now = datetime.now(timezone.utc)
        task = MarketplaceTask(
            started_at=now,
            completed_at=now,
        )
        assert task.started_at == now
        assert task.completed_at == now


class TestMarketplaceTaskRelations:
    """Test task relations."""

    def test_job_id_nullable(self):
        """Should allow null job_id (standalone task)."""
        task = MarketplaceTask()
        assert task.job_id is None

    def test_job_id_can_be_set(self):
        """Should accept int for job_id."""
        task = MarketplaceTask(
            job_id=42,
        )
        assert task.job_id == 42

    def test_product_id_nullable(self):
        """Should allow null product_id."""
        task = MarketplaceTask()
        assert task.product_id is None

    def test_product_id_can_be_set(self):
        """Should accept int for product_id."""
        task = MarketplaceTask(
            product_id=123,
        )
        assert task.product_id == 123


class TestMarketplaceTaskErrorMessage:
    """Test error_message field."""

    def test_error_message_nullable(self):
        """Should allow null error_message."""
        task = MarketplaceTask()
        assert task.error_message is None

    def test_error_message_can_be_set(self):
        """Should accept string for error_message."""
        task = MarketplaceTask(
            status=TaskStatus.FAILED,
            error_message="Connection timeout after 60 seconds",
        )
        assert task.error_message == "Connection timeout after 60 seconds"

    def test_error_message_long_text(self):
        """Should accept long error messages."""
        long_error = "Error: " + "x" * 1000
        task = MarketplaceTask(
            status=TaskStatus.FAILED,
            error_message=long_error,
        )
        assert task.error_message == long_error
