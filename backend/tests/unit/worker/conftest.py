"""
Shared fixtures for worker tests.

Provides mock objects and test configurations for:
- DispatcherConfig
- ClientWorker
- JobDispatcher

Created: 2026-01-21
"""

import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

from worker.dispatcher_config import DispatcherConfig


@pytest.fixture
def mock_config():
    """Configuration with reduced values for fast tests."""
    return DispatcherConfig(
        global_max_concurrent=10,
        per_client_max_concurrent=3,
        asyncpg_pool_min_size=1,
        asyncpg_pool_max_size=2,
        worker_idle_timeout_hours=0.001,  # ~3.6s
        worker_max_age_hours=0.002,  # ~7.2s
        poll_interval=0.1,
        notify_channel="test_channel",
        job_timeout=10.0,
        graceful_shutdown_timeout=5.0,
        db_url="postgresql://test:test@localhost/test",
    )


@pytest.fixture
def default_config():
    """Configuration with default values."""
    return DispatcherConfig(
        db_url="postgresql://test:test@localhost/test"
    )


@pytest.fixture
def mock_pg_pool():
    """Mock asyncpg pool."""
    pool = MagicMock()
    pool.acquire = AsyncMock()
    pool.release = AsyncMock()
    pool.close = AsyncMock()
    return pool


@pytest.fixture
def mock_pg_connection():
    """Mock asyncpg connection."""
    conn = MagicMock()
    conn.add_listener = AsyncMock()
    conn.remove_listener = AsyncMock()
    conn.execute = AsyncMock()
    conn.fetch = AsyncMock(return_value=[])
    conn.fetchval = AsyncMock(return_value=0)
    return conn


@pytest.fixture
def global_semaphore():
    """Global semaphore for tests."""
    return asyncio.Semaphore(10)


@pytest.fixture
def mock_job():
    """Mock marketplace job."""
    job = MagicMock()
    job.id = 123
    job.action = "create_listing"
    job.marketplace = "vinted"
    job.status = "pending"
    job.created_at = datetime.now(timezone.utc)
    return job


@pytest.fixture
def mock_job_executor():
    """Mock JobExecutor."""
    executor = MagicMock()
    executor.claim_next_job = MagicMock(return_value=None)
    executor.execute_job = AsyncMock(return_value={"success": True, "duration_ms": 100})
    executor.expire_old_jobs = MagicMock()
    executor.force_cancel_stale_jobs = MagicMock()
    return executor


@pytest.fixture
def mock_session():
    """Mock SQLAlchemy session."""
    session = MagicMock()
    session.execute = MagicMock()
    session.commit = MagicMock()
    session.close = MagicMock()
    return session


@pytest.fixture
def frozen_time():
    """Utility to freeze time for tests."""
    return datetime(2026, 1, 21, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def time_helpers(frozen_time):
    """Helper functions for time-based tests."""
    def hours_ago(hours: float) -> datetime:
        return frozen_time - timedelta(hours=hours)

    def seconds_ago(seconds: float) -> datetime:
        return frozen_time - timedelta(seconds=seconds)

    return {
        "now": frozen_time,
        "hours_ago": hours_ago,
        "seconds_ago": seconds_ago,
    }
