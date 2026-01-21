"""
Unit Tests for AdvisoryLockHelper

Tests for PostgreSQL advisory locks used in job cancellation.

Created: 2026-01-20
"""

import pytest
from unittest.mock import MagicMock, patch, call

from shared.advisory_locks import (
    AdvisoryLockHelper,
    WORK_LOCK_NS,
    CANCEL_LOCK_NS,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_db():
    """Mock SQLAlchemy session."""
    db = MagicMock()
    db.execute = MagicMock()
    return db


# =============================================================================
# Test: Constants
# =============================================================================


class TestAdvisoryLockConstants:
    """Test namespace constants."""

    def test_work_lock_namespace(self):
        """Should define WORK_LOCK_NS as 1."""
        assert WORK_LOCK_NS == 1

    def test_cancel_lock_namespace(self):
        """Should define CANCEL_LOCK_NS as 2."""
        assert CANCEL_LOCK_NS == 2

    def test_namespaces_are_different(self):
        """Namespaces must be different to avoid conflicts."""
        assert WORK_LOCK_NS != CANCEL_LOCK_NS


# =============================================================================
# Test: try_acquire_work_lock
# =============================================================================


class TestTryAcquireWorkLock:
    """Test try_acquire_work_lock method."""

    def test_returns_true_when_lock_acquired(self, mock_db):
        """Should return True when lock is acquired."""
        mock_db.execute.return_value.scalar.return_value = True

        result = AdvisoryLockHelper.try_acquire_work_lock(mock_db, job_id=42)

        assert result is True
        mock_db.execute.assert_called_once()

    def test_returns_false_when_lock_not_acquired(self, mock_db):
        """Should return False when lock is already held."""
        mock_db.execute.return_value.scalar.return_value = False

        result = AdvisoryLockHelper.try_acquire_work_lock(mock_db, job_id=42)

        assert result is False

    def test_uses_work_lock_namespace(self, mock_db):
        """Should use WORK_LOCK_NS namespace."""
        mock_db.execute.return_value.scalar.return_value = True

        AdvisoryLockHelper.try_acquire_work_lock(mock_db, job_id=123)

        # Check the call args contain the right namespace
        call_args = mock_db.execute.call_args
        params = call_args[0][1]  # Second positional arg is params dict
        assert params["ns"] == WORK_LOCK_NS
        assert params["id"] == 123

    def test_handles_exception(self, mock_db):
        """Should return False on exception."""
        mock_db.execute.side_effect = Exception("Database error")

        result = AdvisoryLockHelper.try_acquire_work_lock(mock_db, job_id=42)

        assert result is False


# =============================================================================
# Test: release_work_lock
# =============================================================================


class TestReleaseWorkLock:
    """Test release_work_lock method."""

    def test_returns_true_when_released(self, mock_db):
        """Should return True when lock is released."""
        mock_db.execute.return_value.scalar.return_value = True

        result = AdvisoryLockHelper.release_work_lock(mock_db, job_id=42)

        assert result is True

    def test_returns_false_when_not_held(self, mock_db):
        """Should return False when lock was not held."""
        mock_db.execute.return_value.scalar.return_value = False

        result = AdvisoryLockHelper.release_work_lock(mock_db, job_id=42)

        assert result is False

    def test_uses_work_lock_namespace(self, mock_db):
        """Should use WORK_LOCK_NS namespace."""
        mock_db.execute.return_value.scalar.return_value = True

        AdvisoryLockHelper.release_work_lock(mock_db, job_id=456)

        call_args = mock_db.execute.call_args
        params = call_args[0][1]
        assert params["ns"] == WORK_LOCK_NS
        assert params["id"] == 456

    def test_handles_exception(self, mock_db):
        """Should return False on exception."""
        mock_db.execute.side_effect = Exception("Database error")

        result = AdvisoryLockHelper.release_work_lock(mock_db, job_id=42)

        assert result is False


# =============================================================================
# Test: signal_cancel
# =============================================================================


class TestSignalCancel:
    """Test signal_cancel method."""

    def test_returns_true_when_signaled(self, mock_db):
        """Should return True when cancel signal sent."""
        mock_db.execute.return_value.scalar.return_value = True

        result = AdvisoryLockHelper.signal_cancel(mock_db, job_id=42)

        assert result is True

    def test_uses_cancel_lock_namespace(self, mock_db):
        """Should use CANCEL_LOCK_NS namespace."""
        mock_db.execute.return_value.scalar.return_value = True

        AdvisoryLockHelper.signal_cancel(mock_db, job_id=789)

        call_args = mock_db.execute.call_args
        params = call_args[0][1]
        assert params["ns"] == CANCEL_LOCK_NS
        assert params["id"] == 789

    def test_retries_on_failure(self, mock_db):
        """Should retry if lock not acquired."""
        # First two attempts fail, third succeeds
        mock_db.execute.return_value.scalar.side_effect = [False, False, True]

        with patch('time.sleep'):  # Speed up test
            result = AdvisoryLockHelper.signal_cancel(mock_db, job_id=42, max_retries=3)

        assert result is True
        assert mock_db.execute.call_count == 3

    def test_returns_true_after_max_retries(self, mock_db):
        """Should return True after max retries (cancel effectively signaled)."""
        # All attempts fail
        mock_db.execute.return_value.scalar.return_value = False

        with patch('time.sleep'):
            result = AdvisoryLockHelper.signal_cancel(mock_db, job_id=42, max_retries=3)

        # Returns True because lock already held = cancel already signaled
        assert result is True

    def test_handles_exception_with_retry(self, mock_db):
        """Should retry on exception."""
        mock_db.execute.side_effect = [
            Exception("Error 1"),
            Exception("Error 2"),
            MagicMock(scalar=MagicMock(return_value=True))
        ]

        with patch('time.sleep'):
            result = AdvisoryLockHelper.signal_cancel(mock_db, job_id=42, max_retries=3)

        assert result is True


# =============================================================================
# Test: is_cancel_signaled
# =============================================================================


class TestIsCancelSignaled:
    """Test is_cancel_signaled method."""

    def test_returns_false_when_no_signal(self, mock_db):
        """Should return False when no cancel signal (we can acquire lock)."""
        # First call: pg_try_advisory_lock returns True (we got it)
        # Second call: pg_advisory_unlock releases it
        mock_db.execute.return_value.scalar.return_value = True

        result = AdvisoryLockHelper.is_cancel_signaled(mock_db, job_id=42)

        assert result is False
        # Should have called execute twice (acquire + release)
        assert mock_db.execute.call_count == 2

    def test_returns_true_when_signaled(self, mock_db):
        """Should return True when cancel signal present (can't acquire lock)."""
        mock_db.execute.return_value.scalar.return_value = False  # Lock held by cancel API

        result = AdvisoryLockHelper.is_cancel_signaled(mock_db, job_id=42)

        assert result is True
        # Should have called execute only once (acquire attempt)
        assert mock_db.execute.call_count == 1

    def test_uses_cancel_lock_namespace(self, mock_db):
        """Should use CANCEL_LOCK_NS namespace."""
        mock_db.execute.return_value.scalar.return_value = True

        AdvisoryLockHelper.is_cancel_signaled(mock_db, job_id=321)

        call_args = mock_db.execute.call_args_list[0]
        params = call_args[0][1]
        assert params["ns"] == CANCEL_LOCK_NS
        assert params["id"] == 321

    def test_handles_exception_returns_false(self, mock_db):
        """Should return False on exception (safer than false positive)."""
        mock_db.execute.side_effect = Exception("Database error")

        result = AdvisoryLockHelper.is_cancel_signaled(mock_db, job_id=42)

        assert result is False


# =============================================================================
# Test: release_cancel_signal
# =============================================================================


class TestReleaseCancelSignal:
    """Test release_cancel_signal method."""

    def test_returns_true_when_released(self, mock_db):
        """Should return True when signal released."""
        mock_db.execute.return_value.scalar.return_value = True

        result = AdvisoryLockHelper.release_cancel_signal(mock_db, job_id=42)

        assert result is True

    def test_returns_false_when_not_held(self, mock_db):
        """Should return False when signal not held."""
        mock_db.execute.return_value.scalar.return_value = False

        result = AdvisoryLockHelper.release_cancel_signal(mock_db, job_id=42)

        assert result is False

    def test_uses_cancel_lock_namespace(self, mock_db):
        """Should use CANCEL_LOCK_NS namespace."""
        mock_db.execute.return_value.scalar.return_value = True

        AdvisoryLockHelper.release_cancel_signal(mock_db, job_id=654)

        call_args = mock_db.execute.call_args
        params = call_args[0][1]
        assert params["ns"] == CANCEL_LOCK_NS
        assert params["id"] == 654

    def test_handles_exception(self, mock_db):
        """Should return False on exception."""
        mock_db.execute.side_effect = Exception("Database error")

        result = AdvisoryLockHelper.release_cancel_signal(mock_db, job_id=42)

        assert result is False


# =============================================================================
# Test: release_all_job_locks
# =============================================================================


class TestReleaseAllJobLocks:
    """Test release_all_job_locks method."""

    def test_releases_both_locks(self, mock_db):
        """Should release both work and cancel locks."""
        mock_db.execute.return_value.scalar.return_value = True

        AdvisoryLockHelper.release_all_job_locks(mock_db, job_id=42)

        # Should have called execute twice (work + cancel)
        assert mock_db.execute.call_count == 2

    def test_calls_both_release_methods(self, mock_db):
        """Should call both release methods."""
        with patch.object(AdvisoryLockHelper, 'release_work_lock') as mock_work:
            with patch.object(AdvisoryLockHelper, 'release_cancel_signal') as mock_cancel:
                AdvisoryLockHelper.release_all_job_locks(mock_db, job_id=42)

                mock_work.assert_called_once_with(mock_db, 42)
                mock_cancel.assert_called_once_with(mock_db, 42)

    def test_handles_exceptions_gracefully(self, mock_db):
        """Should not raise even if releases fail."""
        mock_db.execute.side_effect = Exception("Database error")

        # Should not raise
        AdvisoryLockHelper.release_all_job_locks(mock_db, job_id=42)


# =============================================================================
# Test: Integration-like scenarios
# =============================================================================


class TestAdvisoryLockScenarios:
    """Test realistic usage scenarios."""

    def test_worker_processing_flow(self, mock_db):
        """Test typical worker flow: acquire -> check -> release."""
        # 1. Worker acquires work lock
        mock_db.execute.return_value.scalar.return_value = True
        acquired = AdvisoryLockHelper.try_acquire_work_lock(mock_db, job_id=1)
        assert acquired is True

        # 2. Worker checks for cancel signal (none)
        # Reset mock to track new calls
        mock_db.execute.reset_mock()
        mock_db.execute.return_value.scalar.return_value = True  # We can acquire cancel lock
        cancelled = AdvisoryLockHelper.is_cancel_signaled(mock_db, job_id=1)
        assert cancelled is False

        # 3. Worker releases work lock
        mock_db.execute.reset_mock()
        mock_db.execute.return_value.scalar.return_value = True
        released = AdvisoryLockHelper.release_work_lock(mock_db, job_id=1)
        assert released is True

    def test_cancel_during_processing_flow(self, mock_db):
        """Test cancel signal detection during processing."""
        # 1. Cancel API signals cancellation
        mock_db.execute.return_value.scalar.return_value = True
        signaled = AdvisoryLockHelper.signal_cancel(mock_db, job_id=1)
        assert signaled is True

        # 2. Worker checks for cancel signal (found!)
        mock_db.execute.reset_mock()
        mock_db.execute.return_value.scalar.return_value = False  # Can't acquire cancel lock
        cancelled = AdvisoryLockHelper.is_cancel_signaled(mock_db, job_id=1)
        assert cancelled is True

    def test_concurrent_worker_prevention(self, mock_db):
        """Test that second worker can't acquire lock."""
        # Worker 1 acquires lock
        mock_db.execute.return_value.scalar.return_value = True
        worker1_acquired = AdvisoryLockHelper.try_acquire_work_lock(mock_db, job_id=1)
        assert worker1_acquired is True

        # Worker 2 tries to acquire same lock (fails)
        mock_db.execute.return_value.scalar.return_value = False
        worker2_acquired = AdvisoryLockHelper.try_acquire_work_lock(mock_db, job_id=1)
        assert worker2_acquired is False


# =============================================================================
# Test: Edge Cases
# =============================================================================


class TestAdvisoryLockEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_large_job_id(self, mock_db):
        """Should handle large job IDs."""
        mock_db.execute.return_value.scalar.return_value = True

        result = AdvisoryLockHelper.try_acquire_work_lock(mock_db, job_id=999999999)

        assert result is True
        call_args = mock_db.execute.call_args
        params = call_args[0][1]
        assert params["id"] == 999999999

    def test_job_id_zero(self, mock_db):
        """Should handle job_id=0."""
        mock_db.execute.return_value.scalar.return_value = True

        result = AdvisoryLockHelper.try_acquire_work_lock(mock_db, job_id=0)

        assert result is True

    def test_release_without_acquire(self, mock_db):
        """Should safely return False when releasing unheld lock."""
        mock_db.execute.return_value.scalar.return_value = False

        result = AdvisoryLockHelper.release_work_lock(mock_db, job_id=42)

        assert result is False
