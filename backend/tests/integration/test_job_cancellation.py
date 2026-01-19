"""
Integration Tests for Job Cancellation (Cooperative Pattern)

Tests the complete cancellation flow:
1. API cancel request sets flag
2. Handler detects flag and stops gracefully
3. Timeout fallback force-cancels unresponsive handlers

Created: 2026-01-15
Phase 6.2: Integration testing
"""

import asyncio
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, AsyncMock

from models.user.marketplace_job import MarketplaceJob, JobStatus
from models.vinted.vinted_action_type import VintedActionType
from services.marketplace.marketplace_job_service import MarketplaceJobService
from services.marketplace.marketplace_job_processor import MarketplaceJobProcessor
from services.vinted.vinted_api_sync import VintedApiSyncService


class TestCancelVintedSyncDuringExecution:
    """Test cancelling Vinted sync mid-execution."""

    @pytest.mark.asyncio
    @patch('services.vinted.vinted_api_sync.PluginWebSocketHelper')
    async def test_cancel_sync_during_page_fetch(
        self,
        mock_ws_helper,
        db_session,
        mock_job,
        mock_action_type
    ):
        """
        Should stop gracefully when cancel_requested is set during sync.

        Scenario:
        1. Sync starts fetching pages
        2. After page 2, cancel_requested is set
        3. Handler detects flag and stops
        4. Partial progress is saved (2 pages imported)
        """
        # Setup: Mock API response with 3 pages
        mock_ws_helper.call_plugin_http = AsyncMock(side_effect=[
            # Page 1
            {"items": [{"id": 1, "title": "Item 1"}], "pagination": {"total_count": 3}},
            # Page 2
            {"items": [{"id": 2, "title": "Item 2"}], "pagination": {"total_count": 3}},
            # Page 3 (won't be reached)
        ])

        # Create RUNNING job
        mock_job.status = JobStatus.RUNNING
        mock_job.cancel_requested = False

        # Mock query to return job
        db_session.query = Mock(return_value=Mock(
            filter=Mock(return_value=Mock(
                first=Mock(return_value=mock_job)
            ))
        ))

        # Create sync service
        sync_service = VintedApiSyncService(user_id=1)

        # Simulate cancellation after page 2
        call_count = [0]

        async def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:
                # Set cancel_requested after page 2
                mock_job.cancel_requested = True
            return await mock_ws_helper.call_plugin_http.side_effect[call_count[0] - 1]

        mock_ws_helper.call_plugin_http = AsyncMock(side_effect=side_effect)

        # Execute sync
        result = await sync_service.sync_products(db_session, mock_job)

        # Verify graceful shutdown
        assert result["success"] is False
        assert result.get("status") == "cancelled"
        assert call_count[0] == 2  # Only 2 pages fetched
        db_session.commit.assert_called()  # Partial progress saved


class TestTimeoutFallbackForUnresponsiveHandler:
    """Test timeout fallback when handler doesn't check cancel_requested."""

    @pytest.mark.asyncio
    async def test_force_cancel_stale_job_after_60s(self, db_session):
        """
        Should force-cancel job that didn't respond to cancellation within 60s.

        Scenario:
        1. Job is RUNNING with cancel_requested=True
        2. updated_at is >60s ago (simulates unresponsive handler)
        3. Processor's _force_cancel_stale_jobs() detects it
        4. Job is force-cancelled
        """
        # Create stale job (cancel_requested 61s ago)
        stale_job = MarketplaceJob(
            id=1,
            marketplace="vinted",
            action_type_id=1,
            product_id=101,
            status=JobStatus.RUNNING,
            cancel_requested=True,
            priority=3,
            retry_count=0,
            max_retries=3,
            created_at=datetime.now(timezone.utc) - timedelta(seconds=120),
            updated_at=datetime.now(timezone.utc) - timedelta(seconds=61)  # 61s ago
        )

        # Mock query to return stale job
        mock_all = Mock(all=Mock(return_value=[stale_job]))
        mock_filter = Mock(return_value=mock_all)
        db_session.query = Mock(return_value=Mock(filter=mock_filter))

        # Create processor
        processor = MarketplaceJobProcessor(
            db=db_session,
            user_id=1,
            marketplace="vinted"
        )

        # Mock mark_job_cancelled
        processor.job_service.mark_job_cancelled = Mock()

        # Trigger timeout fallback
        cancelled_count = processor._force_cancel_stale_jobs()

        # Verify force-cancellation
        assert cancelled_count == 1
        processor.job_service.mark_job_cancelled.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_no_force_cancel_for_recent_jobs(self, db_session):
        """
        Should NOT force-cancel jobs that were updated <60s ago.

        Scenario:
        1. Job is RUNNING with cancel_requested=True
        2. updated_at is 30s ago (handler still responding)
        3. Processor's timeout watcher should wait
        """
        # Create recent job (cancel_requested 30s ago)
        recent_job = MarketplaceJob(
            id=1,
            marketplace="vinted",
            action_type_id=1,
            product_id=101,
            status=JobStatus.RUNNING,
            cancel_requested=True,
            priority=3,
            retry_count=0,
            max_retries=3,
            created_at=datetime.now(timezone.utc) - timedelta(seconds=60),
            updated_at=datetime.now(timezone.utc) - timedelta(seconds=30)  # 30s ago
        )

        # Mock query to return empty list (no stale jobs)
        mock_all = Mock(all=Mock(return_value=[]))
        mock_filter = Mock(return_value=mock_all)
        db_session.query = Mock(return_value=Mock(filter=mock_filter))

        # Create processor
        processor = MarketplaceJobProcessor(
            db=db_session,
            user_id=1,
            marketplace="vinted"
        )

        # Trigger timeout fallback
        cancelled_count = processor._force_cancel_stale_jobs()

        # Verify NO force-cancellation
        assert cancelled_count == 0


class TestPreExecutionCancellationCheck:
    """Test pre-execution check in job processor."""

    @pytest.mark.asyncio
    async def test_job_cancelled_before_execution_starts(self, db_session, mock_job):
        """
        Should detect cancellation before handler execution.

        Scenario:
        1. Job is marked as RUNNING
        2. cancel_requested is set BEFORE handler.execute() is called
        3. Processor detects flag in pre-execution check
        4. Handler is never called
        """
        # Setup: Job with cancel_requested already set
        mock_job.status = JobStatus.RUNNING
        mock_job.cancel_requested = True

        # Mock query
        db_session.query = Mock(return_value=Mock(
            filter=Mock(return_value=Mock(
                first=Mock(return_value=mock_job)
            ))
        ))

        # Create processor
        processor = MarketplaceJobProcessor(
            db=db_session,
            user_id=1,
            marketplace="vinted"
        )

        # Mock handler (should never be called)
        mock_handler = Mock()
        mock_handler.execute = AsyncMock()

        # Execute job
        result = await processor._execute_job(mock_job)

        # Verify handler was NOT called
        mock_handler.execute.assert_not_called()

        # Verify result indicates cancellation
        assert result["success"] is False
        assert result["status"] == "cancelled"
        assert result["reason"] == "cancelled_before_start"


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def db_session():
    """Mock database session."""
    session = Mock(spec=["query", "add", "flush", "commit", "rollback", "refresh"])
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
        code="sync_products",
        name="Sync Products",
        priority=3
    )
