"""
Unit Tests for JobDispatcher

Tests for the central multi-tenant dispatcher:
- Initialization
- Lifecycle (start/stop)
- User ID extraction
- Notification handling
- Worker management
- Janitor cleanup
- Status reporting

Created: 2026-01-21
"""

import asyncio
import json
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, AsyncMock, patch, PropertyMock

import pytest

from worker.dispatcher import JobDispatcher
from worker.dispatcher_config import DispatcherConfig
from worker.client_worker import ClientWorker


@pytest.fixture
def dispatcher_config():
    """Configuration for JobDispatcher tests."""
    return DispatcherConfig(
        global_max_concurrent=10,
        per_client_max_concurrent=3,
        asyncpg_pool_min_size=1,
        asyncpg_pool_max_size=2,
        worker_idle_timeout_hours=2.0,
        worker_max_age_hours=24.0,
        poll_interval=30.0,
        notify_channel="test_channel",
        job_timeout=10.0,
        graceful_shutdown_timeout=5.0,
        db_url="postgresql://test:test@localhost/test",
    )


class TestJobDispatcherInit:
    """Test initialization."""

    def test_init_creates_global_semaphore(self, dispatcher_config):
        """Should create global semaphore with global_max_concurrent."""
        dispatcher = JobDispatcher(dispatcher_config)
        assert dispatcher._global_semaphore._value == 10

    def test_init_empty_workers(self, dispatcher_config):
        """Should initialize _workers as empty dict."""
        dispatcher = JobDispatcher(dispatcher_config)
        assert dispatcher._workers == {}
        assert len(dispatcher._workers) == 0

    def test_init_not_running(self, dispatcher_config):
        """Should initialize _is_running to False."""
        dispatcher = JobDispatcher(dispatcher_config)
        assert dispatcher._is_running is False

    def test_init_stores_config(self, dispatcher_config):
        """Should store configuration reference."""
        dispatcher = JobDispatcher(dispatcher_config)
        assert dispatcher.config is dispatcher_config

    def test_init_pool_not_created(self, dispatcher_config):
        """Should not create pool until start."""
        dispatcher = JobDispatcher(dispatcher_config)
        assert dispatcher._pg_pool is None

    def test_init_listen_conn_not_created(self, dispatcher_config):
        """Should not create listen connection until start."""
        dispatcher = JobDispatcher(dispatcher_config)
        assert dispatcher._listen_conn is None

    def test_init_janitor_not_started(self, dispatcher_config):
        """Should not start janitor until start."""
        dispatcher = JobDispatcher(dispatcher_config)
        assert dispatcher._janitor_task is None

    def test_init_shutdown_event_not_set(self, dispatcher_config):
        """Should initialize shutdown event in cleared state."""
        dispatcher = JobDispatcher(dispatcher_config)
        assert not dispatcher._shutdown_event.is_set()


class TestJobDispatcherLifecycle:
    """Test start/stop lifecycle."""

    @pytest.mark.asyncio
    async def test_start_creates_pool(self, dispatcher_config):
        """Should create asyncpg pool on start."""
        dispatcher = JobDispatcher(dispatcher_config)

        with patch("worker.dispatcher.asyncpg.create_pool", new_callable=AsyncMock) as mock_create:
            mock_pool = MagicMock()
            mock_pool.acquire = AsyncMock(return_value=MagicMock())
            mock_pool.close = AsyncMock()
            mock_create.return_value = mock_pool

            with patch.object(dispatcher, "_setup_listen", new_callable=AsyncMock):
                with patch.object(dispatcher, "_bootstrap_workers", new_callable=AsyncMock):
                    with patch.object(dispatcher, "_janitor_loop", new_callable=AsyncMock):
                        await dispatcher.start()

            mock_create.assert_called_once()
            assert dispatcher._pg_pool is mock_pool

            # Cleanup
            await dispatcher.stop()

    @pytest.mark.asyncio
    async def test_start_sets_up_listen(self, dispatcher_config):
        """Should call _setup_listen on start."""
        dispatcher = JobDispatcher(dispatcher_config)

        with patch("worker.dispatcher.asyncpg.create_pool", new_callable=AsyncMock) as mock_create:
            mock_pool = MagicMock()
            mock_pool.acquire = AsyncMock(return_value=MagicMock())
            mock_pool.close = AsyncMock()
            mock_create.return_value = mock_pool

            with patch.object(dispatcher, "_setup_listen", new_callable=AsyncMock) as mock_setup:
                with patch.object(dispatcher, "_bootstrap_workers", new_callable=AsyncMock):
                    with patch.object(dispatcher, "_janitor_loop", new_callable=AsyncMock):
                        await dispatcher.start()

            mock_setup.assert_called_once()

            # Cleanup
            await dispatcher.stop()

    @pytest.mark.asyncio
    async def test_start_starts_janitor(self, dispatcher_config):
        """Should create janitor task on start."""
        dispatcher = JobDispatcher(dispatcher_config)

        with patch("worker.dispatcher.asyncpg.create_pool", new_callable=AsyncMock) as mock_create:
            mock_pool = MagicMock()
            mock_pool.acquire = AsyncMock(return_value=MagicMock())
            mock_pool.close = AsyncMock()
            mock_create.return_value = mock_pool

            with patch.object(dispatcher, "_setup_listen", new_callable=AsyncMock):
                with patch.object(dispatcher, "_bootstrap_workers", new_callable=AsyncMock):
                    with patch.object(dispatcher, "_janitor_loop", new_callable=AsyncMock):
                        await dispatcher.start()

            assert dispatcher._janitor_task is not None

            # Cleanup
            await dispatcher.stop()

    @pytest.mark.asyncio
    async def test_start_sets_running_flag(self, dispatcher_config):
        """Should set _is_running to True on start."""
        dispatcher = JobDispatcher(dispatcher_config)

        with patch("worker.dispatcher.asyncpg.create_pool", new_callable=AsyncMock) as mock_create:
            mock_pool = MagicMock()
            mock_pool.acquire = AsyncMock(return_value=MagicMock())
            mock_pool.close = AsyncMock()
            mock_create.return_value = mock_pool

            with patch.object(dispatcher, "_setup_listen", new_callable=AsyncMock):
                with patch.object(dispatcher, "_bootstrap_workers", new_callable=AsyncMock):
                    with patch.object(dispatcher, "_janitor_loop", new_callable=AsyncMock):
                        await dispatcher.start()

            assert dispatcher._is_running is True

            # Cleanup
            await dispatcher.stop()

    @pytest.mark.asyncio
    async def test_stop_closes_pool(self, dispatcher_config):
        """Should close asyncpg pool on stop."""
        dispatcher = JobDispatcher(dispatcher_config)

        mock_pool = MagicMock()
        mock_pool.acquire = AsyncMock(return_value=MagicMock())
        mock_pool.close = AsyncMock()
        mock_pool.release = AsyncMock()

        with patch("worker.dispatcher.asyncpg.create_pool", new_callable=AsyncMock, return_value=mock_pool):
            with patch.object(dispatcher, "_setup_listen", new_callable=AsyncMock):
                with patch.object(dispatcher, "_bootstrap_workers", new_callable=AsyncMock):
                    with patch.object(dispatcher, "_janitor_loop", new_callable=AsyncMock):
                        await dispatcher.start()
                        await dispatcher.stop()

        mock_pool.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_stops_all_workers(self, dispatcher_config):
        """Should stop all workers on stop."""
        dispatcher = JobDispatcher(dispatcher_config)

        # Create mock workers
        mock_worker1 = MagicMock()
        mock_worker1.stop = AsyncMock()
        mock_worker2 = MagicMock()
        mock_worker2.stop = AsyncMock()

        dispatcher._workers = {1: mock_worker1, 2: mock_worker2}
        dispatcher._is_running = True

        mock_pool = MagicMock()
        mock_pool.close = AsyncMock()
        mock_pool.release = AsyncMock()
        dispatcher._pg_pool = mock_pool

        await dispatcher.stop()

        mock_worker1.stop.assert_called_once()
        mock_worker2.stop.assert_called_once()
        assert len(dispatcher._workers) == 0

    @pytest.mark.asyncio
    async def test_stop_clears_running_flag(self, dispatcher_config):
        """Should set _is_running to False on stop."""
        dispatcher = JobDispatcher(dispatcher_config)
        dispatcher._is_running = True

        mock_pool = MagicMock()
        mock_pool.close = AsyncMock()
        mock_pool.release = AsyncMock()
        dispatcher._pg_pool = mock_pool

        await dispatcher.stop()

        assert dispatcher._is_running is False


class TestJobDispatcherExtractUserId:
    """Test _extract_user_id method."""

    def test_extract_valid_schema(self, dispatcher_config):
        """Should extract user_id from 'user_123' format."""
        dispatcher = JobDispatcher(dispatcher_config)
        assert dispatcher._extract_user_id("user_123") == 123

    def test_extract_valid_schema_large_id(self, dispatcher_config):
        """Should extract large user IDs."""
        dispatcher = JobDispatcher(dispatcher_config)
        assert dispatcher._extract_user_id("user_999999") == 999999

    def test_extract_valid_schema_single_digit(self, dispatcher_config):
        """Should extract single digit user IDs."""
        dispatcher = JobDispatcher(dispatcher_config)
        assert dispatcher._extract_user_id("user_1") == 1

    def test_extract_invalid_schema_no_prefix(self, dispatcher_config):
        """Should return None for schema without 'user_' prefix."""
        dispatcher = JobDispatcher(dispatcher_config)
        assert dispatcher._extract_user_id("invalid") is None

    def test_extract_invalid_schema_wrong_format(self, dispatcher_config):
        """Should return None for wrong format."""
        dispatcher = JobDispatcher(dispatcher_config)
        assert dispatcher._extract_user_id("user_abc") is None
        assert dispatcher._extract_user_id("userX123") is None
        assert dispatcher._extract_user_id("user123") is None

    def test_extract_public_schema(self, dispatcher_config):
        """Should return None for 'public' schema."""
        dispatcher = JobDispatcher(dispatcher_config)
        assert dispatcher._extract_user_id("public") is None

    def test_extract_empty_schema(self, dispatcher_config):
        """Should return None for empty schema."""
        dispatcher = JobDispatcher(dispatcher_config)
        assert dispatcher._extract_user_id("") is None

    def test_extract_none_schema(self, dispatcher_config):
        """Should return None for None schema."""
        dispatcher = JobDispatcher(dispatcher_config)
        assert dispatcher._extract_user_id(None) is None


class TestJobDispatcherOnNotify:
    """Test _on_notify callback."""

    def test_on_notify_valid_payload(self, dispatcher_config):
        """Should route valid notification to correct worker."""
        dispatcher = JobDispatcher(dispatcher_config)

        mock_conn = MagicMock()
        payload = json.dumps({"job_id": 1, "schema": "user_42"})

        with patch.object(dispatcher, "_route_notification") as mock_route:
            # Use asyncio.create_task patch
            with patch("worker.dispatcher.asyncio.create_task") as mock_create_task:
                dispatcher._on_notify(mock_conn, 123, "test_channel", payload)

            # Should have called create_task with coroutine for user_id=42
            mock_create_task.assert_called_once()

    def test_on_notify_invalid_json(self, dispatcher_config):
        """Should not crash on invalid JSON payload."""
        dispatcher = JobDispatcher(dispatcher_config)

        mock_conn = MagicMock()
        payload = "not valid json"

        # Should not raise
        dispatcher._on_notify(mock_conn, 123, "test_channel", payload)

    def test_on_notify_missing_schema(self, dispatcher_config):
        """Should not crash if schema is missing from payload."""
        dispatcher = JobDispatcher(dispatcher_config)

        mock_conn = MagicMock()
        payload = json.dumps({"job_id": 1})

        # Should not raise
        dispatcher._on_notify(mock_conn, 123, "test_channel", payload)

    def test_on_notify_invalid_schema_format(self, dispatcher_config):
        """Should handle invalid schema format gracefully."""
        dispatcher = JobDispatcher(dispatcher_config)

        mock_conn = MagicMock()
        payload = json.dumps({"job_id": 1, "schema": "invalid_schema"})

        with patch("worker.dispatcher.asyncio.create_task") as mock_create_task:
            dispatcher._on_notify(mock_conn, 123, "test_channel", payload)

        # Should not create task for invalid schema
        mock_create_task.assert_not_called()


class TestJobDispatcherEnsureWorkerExists:
    """Test _ensure_worker_exists method."""

    @pytest.mark.asyncio
    async def test_creates_new_worker(self, dispatcher_config):
        """Should create new worker if not exists."""
        dispatcher = JobDispatcher(dispatcher_config)
        dispatcher._pg_pool = MagicMock()

        with patch("worker.dispatcher.ClientWorker") as MockWorker:
            mock_worker_instance = MagicMock()
            mock_worker_instance.start = AsyncMock()
            MockWorker.return_value = mock_worker_instance

            worker = await dispatcher._ensure_worker_exists(42)

            MockWorker.assert_called_once()
            mock_worker_instance.start.assert_called_once()
            assert worker is mock_worker_instance

    @pytest.mark.asyncio
    async def test_returns_existing_worker(self, dispatcher_config):
        """Should return existing worker without creating new one."""
        dispatcher = JobDispatcher(dispatcher_config)

        existing_worker = MagicMock()
        dispatcher._workers[42] = existing_worker

        worker = await dispatcher._ensure_worker_exists(42)

        assert worker is existing_worker

    @pytest.mark.asyncio
    async def test_worker_added_to_dict(self, dispatcher_config):
        """Should add new worker to _workers dict."""
        dispatcher = JobDispatcher(dispatcher_config)
        dispatcher._pg_pool = MagicMock()

        with patch("worker.dispatcher.ClientWorker") as MockWorker:
            mock_worker_instance = MagicMock()
            mock_worker_instance.start = AsyncMock()
            MockWorker.return_value = mock_worker_instance

            await dispatcher._ensure_worker_exists(42)

            assert 42 in dispatcher._workers
            assert dispatcher._workers[42] is mock_worker_instance


class TestJobDispatcherJanitor:
    """Test janitor cleanup logic."""

    @pytest.mark.asyncio
    async def test_janitor_removes_idle_workers(self, dispatcher_config):
        """Should remove workers that are idle with no active jobs."""
        dispatcher = JobDispatcher(dispatcher_config)

        # Create mock worker that is idle
        mock_worker = MagicMock()
        mock_worker.is_idle = True
        mock_worker.is_old = False
        mock_worker.active_job_count = 0
        mock_worker.stop = AsyncMock()

        dispatcher._workers = {1: mock_worker}

        await dispatcher._janitor_cleanup()

        mock_worker.stop.assert_called_once()
        assert 1 not in dispatcher._workers

    @pytest.mark.asyncio
    async def test_janitor_keeps_active_workers(self, dispatcher_config):
        """Should keep workers that have active jobs."""
        dispatcher = JobDispatcher(dispatcher_config)

        # Create mock worker that is idle but has active jobs
        mock_worker = MagicMock()
        mock_worker.is_idle = True
        mock_worker.is_old = False
        mock_worker.active_job_count = 2  # Has active jobs
        mock_worker.stop = AsyncMock()

        dispatcher._workers = {1: mock_worker}

        await dispatcher._janitor_cleanup()

        mock_worker.stop.assert_not_called()
        assert 1 in dispatcher._workers

    @pytest.mark.asyncio
    async def test_janitor_removes_old_workers(self, dispatcher_config):
        """Should remove workers that exceed max age."""
        dispatcher = JobDispatcher(dispatcher_config)

        # Create mock worker that is old
        mock_worker = MagicMock()
        mock_worker.is_idle = False
        mock_worker.is_old = True
        mock_worker.active_job_count = 0
        mock_worker.stop = AsyncMock()

        dispatcher._workers = {1: mock_worker}

        await dispatcher._janitor_cleanup()

        mock_worker.stop.assert_called_once()
        assert 1 not in dispatcher._workers

    @pytest.mark.asyncio
    async def test_janitor_calls_worker_stop(self, dispatcher_config):
        """Should call worker.stop() when removing."""
        dispatcher = JobDispatcher(dispatcher_config)

        mock_worker = MagicMock()
        mock_worker.is_idle = True
        mock_worker.is_old = False
        mock_worker.active_job_count = 0
        mock_worker.stop = AsyncMock()

        dispatcher._workers = {1: mock_worker}

        await dispatcher._janitor_cleanup()

        mock_worker.stop.assert_called_once_with(timeout=30)

    @pytest.mark.asyncio
    async def test_janitor_keeps_healthy_workers(self, dispatcher_config):
        """Should keep workers that are not idle and not old."""
        dispatcher = JobDispatcher(dispatcher_config)

        mock_worker = MagicMock()
        mock_worker.is_idle = False
        mock_worker.is_old = False
        mock_worker.active_job_count = 1
        mock_worker.stop = AsyncMock()

        dispatcher._workers = {1: mock_worker}

        await dispatcher._janitor_cleanup()

        mock_worker.stop.assert_not_called()
        assert 1 in dispatcher._workers

    @pytest.mark.asyncio
    async def test_janitor_removes_multiple_workers(self, dispatcher_config):
        """Should remove multiple workers in single cleanup."""
        dispatcher = JobDispatcher(dispatcher_config)

        mock_worker1 = MagicMock()
        mock_worker1.is_idle = True
        mock_worker1.is_old = False
        mock_worker1.active_job_count = 0
        mock_worker1.stop = AsyncMock()

        mock_worker2 = MagicMock()
        mock_worker2.is_idle = False
        mock_worker2.is_old = True
        mock_worker2.active_job_count = 0
        mock_worker2.stop = AsyncMock()

        mock_worker3 = MagicMock()
        mock_worker3.is_idle = False
        mock_worker3.is_old = False
        mock_worker3.active_job_count = 1
        mock_worker3.stop = AsyncMock()

        dispatcher._workers = {1: mock_worker1, 2: mock_worker2, 3: mock_worker3}

        await dispatcher._janitor_cleanup()

        # Workers 1 and 2 should be removed
        mock_worker1.stop.assert_called_once()
        mock_worker2.stop.assert_called_once()
        mock_worker3.stop.assert_not_called()

        assert 1 not in dispatcher._workers
        assert 2 not in dispatcher._workers
        assert 3 in dispatcher._workers


class TestJobDispatcherGetStatus:
    """Test get_status method."""

    def test_get_status_returns_complete_dict(self, dispatcher_config):
        """Should return dict with all required fields."""
        dispatcher = JobDispatcher(dispatcher_config)

        status = dispatcher.get_status()

        assert "is_running" in status
        assert "config" in status
        assert "workers_count" in status
        assert "total_active_jobs" in status
        assert "global_semaphore_available" in status
        assert "workers" in status
        assert "timestamp" in status

    def test_get_status_config_fields(self, dispatcher_config):
        """Should include config values in status."""
        dispatcher = JobDispatcher(dispatcher_config)

        status = dispatcher.get_status()

        assert status["config"]["global_max_concurrent"] == 10
        assert status["config"]["per_client_max_concurrent"] == 3
        assert status["config"]["worker_idle_timeout_hours"] == 2.0
        assert status["config"]["worker_max_age_hours"] == 24.0
        assert status["config"]["poll_interval"] == 30.0

    def test_get_status_counts_jobs(self, dispatcher_config):
        """Should return correct total_active_jobs count."""
        dispatcher = JobDispatcher(dispatcher_config)

        # Create mock workers with different active job counts
        mock_worker1 = MagicMock()
        mock_worker1.active_job_count = 2
        mock_worker1.get_status.return_value = {"user_id": 1, "active_jobs": 2}

        mock_worker2 = MagicMock()
        mock_worker2.active_job_count = 3
        mock_worker2.get_status.return_value = {"user_id": 2, "active_jobs": 3}

        dispatcher._workers = {1: mock_worker1, 2: mock_worker2}

        status = dispatcher.get_status()

        assert status["total_active_jobs"] == 5  # 2 + 3
        assert status["workers_count"] == 2

    def test_get_status_semaphore_available(self, dispatcher_config):
        """Should calculate available semaphore slots."""
        dispatcher = JobDispatcher(dispatcher_config)

        # Create mock workers
        mock_worker = MagicMock()
        mock_worker.active_job_count = 3
        mock_worker.get_status.return_value = {"user_id": 1, "active_jobs": 3}

        dispatcher._workers = {1: mock_worker}

        status = dispatcher.get_status()

        # global_max = 10, active = 3, available = 7
        assert status["global_semaphore_available"] == 7

    def test_get_status_workers_list(self, dispatcher_config):
        """Should include worker statuses in workers list."""
        dispatcher = JobDispatcher(dispatcher_config)

        mock_worker1 = MagicMock()
        mock_worker1.active_job_count = 1
        mock_worker1.get_status.return_value = {"user_id": 1, "active_jobs": 1}

        mock_worker2 = MagicMock()
        mock_worker2.active_job_count = 2
        mock_worker2.get_status.return_value = {"user_id": 2, "active_jobs": 2}

        dispatcher._workers = {1: mock_worker1, 2: mock_worker2}

        status = dispatcher.get_status()

        assert len(status["workers"]) == 2

    def test_get_status_timestamp_isoformat(self, dispatcher_config):
        """Should include ISO format timestamp."""
        dispatcher = JobDispatcher(dispatcher_config)

        status = dispatcher.get_status()

        assert isinstance(status["timestamp"], str)
        assert "T" in status["timestamp"]  # ISO format check

    def test_get_status_empty_workers(self, dispatcher_config):
        """Should handle empty workers dict."""
        dispatcher = JobDispatcher(dispatcher_config)

        status = dispatcher.get_status()

        assert status["workers_count"] == 0
        assert status["total_active_jobs"] == 0
        assert status["global_semaphore_available"] == 10
        assert status["workers"] == []
