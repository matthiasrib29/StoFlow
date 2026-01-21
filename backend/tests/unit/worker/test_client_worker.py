"""
Unit Tests for ClientWorker

Tests for the per-tenant worker:
- Initialization
- Lifecycle (start/stop)
- Properties (is_idle, is_old, active_job_count)
- Notifications
- Double semaphore pattern

Created: 2026-01-21
"""

import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

from worker.client_worker import ClientWorker
from worker.dispatcher_config import DispatcherConfig


class TestClientWorkerInit:
    """Test initialization."""

    def test_init_creates_schema_name(self, mock_config, mock_pg_pool, global_semaphore):
        """Should create schema_name from user_id."""
        worker = ClientWorker(
            user_id=123,
            config=mock_config,
            global_semaphore=global_semaphore,
            pg_pool=mock_pg_pool,
        )
        assert worker.schema_name == "user_123"

    def test_init_creates_local_semaphore(self, mock_config, mock_pg_pool, global_semaphore):
        """Should create local semaphore with per_client_max_concurrent."""
        mock_config.per_client_max_concurrent = 5
        worker = ClientWorker(
            user_id=1,
            config=mock_config,
            global_semaphore=global_semaphore,
            pg_pool=mock_pg_pool,
        )
        # Semaphore internal value (not public, but we can test behavior)
        assert worker._local_semaphore._value == 5

    def test_init_sets_timestamps(self, mock_config, mock_pg_pool, global_semaphore):
        """Should set created_at and last_activity to now."""
        before = datetime.now(timezone.utc)
        worker = ClientWorker(
            user_id=1,
            config=mock_config,
            global_semaphore=global_semaphore,
            pg_pool=mock_pg_pool,
        )
        after = datetime.now(timezone.utc)

        assert before <= worker._created_at <= after
        assert before <= worker._last_activity <= after

    def test_init_empty_active_tasks(self, mock_config, mock_pg_pool, global_semaphore):
        """Should initialize _active_tasks as empty set."""
        worker = ClientWorker(
            user_id=1,
            config=mock_config,
            global_semaphore=global_semaphore,
            pg_pool=mock_pg_pool,
        )
        assert worker._active_tasks == set()
        assert len(worker._active_tasks) == 0

    def test_init_events_not_set(self, mock_config, mock_pg_pool, global_semaphore):
        """Should initialize events in cleared state."""
        worker = ClientWorker(
            user_id=1,
            config=mock_config,
            global_semaphore=global_semaphore,
            pg_pool=mock_pg_pool,
        )
        assert not worker._shutdown_event.is_set()
        assert not worker._job_available.is_set()

    def test_init_not_running(self, mock_config, mock_pg_pool, global_semaphore):
        """Should initialize is_running to False."""
        worker = ClientWorker(
            user_id=1,
            config=mock_config,
            global_semaphore=global_semaphore,
            pg_pool=mock_pg_pool,
        )
        assert worker._is_running is False
        assert worker.is_running is False

    def test_init_stores_references(self, mock_config, mock_pg_pool, global_semaphore):
        """Should store config, global_semaphore, and pg_pool."""
        worker = ClientWorker(
            user_id=42,
            config=mock_config,
            global_semaphore=global_semaphore,
            pg_pool=mock_pg_pool,
        )
        assert worker.user_id == 42
        assert worker.config is mock_config
        assert worker._global_semaphore is global_semaphore
        assert worker._pg_pool is mock_pg_pool


class TestClientWorkerLifecycle:
    """Test start/stop lifecycle."""

    @pytest.mark.asyncio
    async def test_start_sets_running_flag(self, mock_config, mock_pg_pool, global_semaphore):
        """Should set is_running to True after start."""
        worker = ClientWorker(
            user_id=1,
            config=mock_config,
            global_semaphore=global_semaphore,
            pg_pool=mock_pg_pool,
        )

        # Patch _run to prevent actual loop execution
        with patch.object(worker, "_run", new_callable=AsyncMock):
            await worker.start()

        assert worker._is_running is True
        assert worker.is_running is True

        # Cleanup
        worker._shutdown_event.set()
        if worker._task:
            worker._task.cancel()
            try:
                await worker._task
            except asyncio.CancelledError:
                pass

    @pytest.mark.asyncio
    async def test_start_twice_does_not_crash(self, mock_config, mock_pg_pool, global_semaphore):
        """Should log warning but not crash on double start."""
        worker = ClientWorker(
            user_id=1,
            config=mock_config,
            global_semaphore=global_semaphore,
            pg_pool=mock_pg_pool,
        )

        with patch.object(worker, "_run", new_callable=AsyncMock):
            await worker.start()
            # Second start should just log warning
            await worker.start()

        assert worker.is_running is True

        # Cleanup
        worker._shutdown_event.set()
        if worker._task:
            worker._task.cancel()
            try:
                await worker._task
            except asyncio.CancelledError:
                pass

    @pytest.mark.asyncio
    async def test_stop_sets_shutdown_event(self, mock_config, mock_pg_pool, global_semaphore):
        """Should set _shutdown_event after stop."""
        worker = ClientWorker(
            user_id=1,
            config=mock_config,
            global_semaphore=global_semaphore,
            pg_pool=mock_pg_pool,
        )

        with patch.object(worker, "_run", new_callable=AsyncMock):
            await worker.start()
            await worker.stop(timeout=1.0)

        assert worker._shutdown_event.is_set()

    @pytest.mark.asyncio
    async def test_stop_clears_running_flag(self, mock_config, mock_pg_pool, global_semaphore):
        """Should set is_running to False after stop."""
        worker = ClientWorker(
            user_id=1,
            config=mock_config,
            global_semaphore=global_semaphore,
            pg_pool=mock_pg_pool,
        )

        with patch.object(worker, "_run", new_callable=AsyncMock):
            await worker.start()
            assert worker.is_running is True
            await worker.stop(timeout=1.0)

        assert worker._is_running is False
        assert worker.is_running is False

    @pytest.mark.asyncio
    async def test_stop_when_not_running_does_nothing(self, mock_config, mock_pg_pool, global_semaphore):
        """Should do nothing if stop called when not running."""
        worker = ClientWorker(
            user_id=1,
            config=mock_config,
            global_semaphore=global_semaphore,
            pg_pool=mock_pg_pool,
        )

        # Never started
        await worker.stop()
        # Should not crash, just return
        assert worker.is_running is False


class TestClientWorkerProperties:
    """Test properties: is_idle, is_old, active_job_count."""

    def test_is_idle_false_when_recent_activity(self, mock_config, mock_pg_pool, global_semaphore):
        """Should return False if activity was recent."""
        mock_config.worker_idle_timeout_hours = 2.0  # 2 hours
        worker = ClientWorker(
            user_id=1,
            config=mock_config,
            global_semaphore=global_semaphore,
            pg_pool=mock_pg_pool,
        )
        # Just created, so last_activity is now
        assert worker.is_idle is False

    def test_is_idle_true_after_timeout(self, mock_config, mock_pg_pool, global_semaphore):
        """Should return True if idle timeout exceeded."""
        mock_config.worker_idle_timeout_hours = 0.001  # ~3.6 seconds
        worker = ClientWorker(
            user_id=1,
            config=mock_config,
            global_semaphore=global_semaphore,
            pg_pool=mock_pg_pool,
        )
        # Manually set last_activity to past
        worker._last_activity = datetime.now(timezone.utc) - timedelta(hours=1)
        assert worker.is_idle is True

    def test_is_old_false_when_young(self, mock_config, mock_pg_pool, global_semaphore):
        """Should return False if worker was created recently."""
        mock_config.worker_max_age_hours = 24.0  # 24 hours
        worker = ClientWorker(
            user_id=1,
            config=mock_config,
            global_semaphore=global_semaphore,
            pg_pool=mock_pg_pool,
        )
        # Just created
        assert worker.is_old is False

    def test_is_old_true_after_max_age(self, mock_config, mock_pg_pool, global_semaphore):
        """Should return True if max age exceeded."""
        mock_config.worker_max_age_hours = 0.001  # ~3.6 seconds
        worker = ClientWorker(
            user_id=1,
            config=mock_config,
            global_semaphore=global_semaphore,
            pg_pool=mock_pg_pool,
        )
        # Manually set created_at to past
        worker._created_at = datetime.now(timezone.utc) - timedelta(hours=1)
        assert worker.is_old is True

    def test_active_job_count_zero_initially(self, mock_config, mock_pg_pool, global_semaphore):
        """Should return 0 when no active tasks."""
        worker = ClientWorker(
            user_id=1,
            config=mock_config,
            global_semaphore=global_semaphore,
            pg_pool=mock_pg_pool,
        )
        assert worker.active_job_count == 0

    def test_active_job_count_reflects_tasks(self, mock_config, mock_pg_pool, global_semaphore):
        """Should return count of active tasks."""
        worker = ClientWorker(
            user_id=1,
            config=mock_config,
            global_semaphore=global_semaphore,
            pg_pool=mock_pg_pool,
        )
        # Manually add fake tasks
        worker._active_tasks.add(MagicMock())
        worker._active_tasks.add(MagicMock())
        worker._active_tasks.add(MagicMock())

        assert worker.active_job_count == 3


class TestClientWorkerNotify:
    """Test notify_job_available method."""

    def test_notify_sets_event(self, mock_config, mock_pg_pool, global_semaphore):
        """Should set _job_available event."""
        worker = ClientWorker(
            user_id=1,
            config=mock_config,
            global_semaphore=global_semaphore,
            pg_pool=mock_pg_pool,
        )
        assert not worker._job_available.is_set()

        worker.notify_job_available()

        assert worker._job_available.is_set()

    def test_notify_updates_last_activity(self, mock_config, mock_pg_pool, global_semaphore):
        """Should update last_activity timestamp."""
        worker = ClientWorker(
            user_id=1,
            config=mock_config,
            global_semaphore=global_semaphore,
            pg_pool=mock_pg_pool,
        )
        # Set last_activity to past
        old_activity = datetime.now(timezone.utc) - timedelta(hours=1)
        worker._last_activity = old_activity

        worker.notify_job_available()

        assert worker._last_activity > old_activity


class TestClientWorkerGetStatus:
    """Test get_status method."""

    def test_get_status_returns_complete_dict(self, mock_config, mock_pg_pool, global_semaphore):
        """Should return dict with all required fields."""
        worker = ClientWorker(
            user_id=42,
            config=mock_config,
            global_semaphore=global_semaphore,
            pg_pool=mock_pg_pool,
        )

        status = worker.get_status()

        assert "user_id" in status
        assert "schema" in status
        assert "is_running" in status
        assert "active_jobs" in status
        assert "is_idle" in status
        assert "is_old" in status
        assert "created_at" in status
        assert "last_activity" in status
        assert "age_hours" in status
        assert "idle_hours" in status

    def test_get_status_user_id_correct(self, mock_config, mock_pg_pool, global_semaphore):
        """Should return correct user_id."""
        worker = ClientWorker(
            user_id=42,
            config=mock_config,
            global_semaphore=global_semaphore,
            pg_pool=mock_pg_pool,
        )

        status = worker.get_status()

        assert status["user_id"] == 42
        assert status["schema"] == "user_42"

    def test_get_status_active_jobs_count(self, mock_config, mock_pg_pool, global_semaphore):
        """Should return correct active jobs count."""
        worker = ClientWorker(
            user_id=1,
            config=mock_config,
            global_semaphore=global_semaphore,
            pg_pool=mock_pg_pool,
        )
        # Add some fake tasks
        worker._active_tasks.add(MagicMock())
        worker._active_tasks.add(MagicMock())

        status = worker.get_status()

        assert status["active_jobs"] == 2

    def test_get_status_timestamps_isoformat(self, mock_config, mock_pg_pool, global_semaphore):
        """Should return timestamps in ISO format."""
        worker = ClientWorker(
            user_id=1,
            config=mock_config,
            global_semaphore=global_semaphore,
            pg_pool=mock_pg_pool,
        )

        status = worker.get_status()

        # Should be parseable ISO strings
        assert isinstance(status["created_at"], str)
        assert isinstance(status["last_activity"], str)
        # Basic ISO format check
        assert "T" in status["created_at"]
        assert "T" in status["last_activity"]


class TestClientWorkerSemaphores:
    """Test double semaphore pattern."""

    @pytest.mark.asyncio
    async def test_semaphore_values_initialized(self, mock_config, global_semaphore):
        """Should initialize both semaphores with correct values."""
        mock_config.per_client_max_concurrent = 5
        mock_config.global_max_concurrent = 10
        pg_pool = MagicMock()

        worker = ClientWorker(
            user_id=1,
            config=mock_config,
            global_semaphore=global_semaphore,
            pg_pool=pg_pool,
        )

        # Local semaphore should have per_client limit
        assert worker._local_semaphore._value == 5
        # Global semaphore should be passed reference
        assert worker._global_semaphore is global_semaphore

    @pytest.mark.asyncio
    async def test_execute_with_semaphores_acquires_both(self, mock_config, mock_pg_pool, global_semaphore):
        """Should acquire global then local semaphore during execution."""
        mock_config.per_client_max_concurrent = 2
        worker = ClientWorker(
            user_id=1,
            config=mock_config,
            global_semaphore=global_semaphore,
            pg_pool=mock_pg_pool,
        )

        # Create mock executor and job
        mock_executor = MagicMock()
        mock_executor.execute_job = AsyncMock(return_value={"success": True, "duration_ms": 50})
        mock_job = MagicMock()
        mock_job.id = 1
        mock_db = MagicMock()

        global_before = global_semaphore._value
        local_before = worker._local_semaphore._value

        await worker._execute_with_semaphores(mock_executor, mock_job, mock_db)

        # Semaphores should be released after execution
        assert global_semaphore._value == global_before
        assert worker._local_semaphore._value == local_before

        # Executor should have been called
        mock_executor.execute_job.assert_called_once_with(mock_job)
        # DB should be closed
        mock_db.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_semaphores_released_on_error(self, mock_config, mock_pg_pool, global_semaphore):
        """Should release semaphores even if execution fails."""
        mock_config.per_client_max_concurrent = 2
        worker = ClientWorker(
            user_id=1,
            config=mock_config,
            global_semaphore=global_semaphore,
            pg_pool=mock_pg_pool,
        )

        # Create mock executor that raises
        mock_executor = MagicMock()
        mock_executor.execute_job = AsyncMock(side_effect=Exception("Test error"))
        mock_job = MagicMock()
        mock_job.id = 1
        mock_db = MagicMock()

        global_before = global_semaphore._value
        local_before = worker._local_semaphore._value

        # Should not raise (error is caught)
        await worker._execute_with_semaphores(mock_executor, mock_job, mock_db)

        # Semaphores should still be released
        assert global_semaphore._value == global_before
        assert worker._local_semaphore._value == local_before

        # DB should still be closed
        mock_db.close.assert_called_once()
