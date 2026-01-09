"""
Unit Tests for BatchJobService

Tests batch job creation, progress tracking, and cancellation.

Created: 2026-01-07
Phase 6.1: Unit testing
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from models.user.batch_job import BatchJob, BatchJobStatus
from models.user.marketplace_job import MarketplaceJob, JobStatus
from models.vinted.vinted_action_type import VintedActionType
from services.marketplace.batch_job_service import BatchJobService


class TestBatchJobServiceCreate:
    """Test batch job creation."""

    def test_create_batch_job_success(self, db_session, mock_action_type):
        """Should create BatchJob with N MarketplaceJobs."""
        service = BatchJobService(db_session)

        # Mock action type lookup
        db_session.query = Mock(return_value=Mock(
            filter=Mock(return_value=Mock(
                first=Mock(return_value=mock_action_type)
            ))
        ))

        # Create batch
        batch = service.create_batch_job(
            marketplace="vinted",
            action_code="publish",
            product_ids=[1, 2, 3],
            priority=3,
            created_by_user_id=1
        )

        assert batch is not None
        assert batch.marketplace == "vinted"
        assert batch.action_code == "publish"
        assert batch.total_count == 3
        assert batch.completed_count == 0
        assert batch.failed_count == 0
        assert batch.status == BatchJobStatus.PENDING
        assert batch.priority == 3

    def test_create_batch_job_empty_products_raises(self, db_session):
        """Should raise ValueError for empty product_ids."""
        service = BatchJobService(db_session)

        with pytest.raises(ValueError, match="product_ids cannot be empty"):
            service.create_batch_job(
                marketplace="vinted",
                action_code="publish",
                product_ids=[],
                priority=3
            )

    def test_create_batch_job_invalid_action_raises(self, db_session):
        """Should raise ValueError for invalid action_code."""
        service = BatchJobService(db_session)

        # Mock action type not found
        db_session.query = Mock(return_value=Mock(
            filter=Mock(return_value=Mock(
                first=Mock(return_value=None)
            ))
        ))

        with pytest.raises(ValueError, match="Invalid action_code 'invalid_action' for marketplace 'vinted'"):
            service.create_batch_job(
                marketplace="vinted",
                action_code="invalid_action",
                product_ids=[1, 2, 3],
                priority=3
            )

    def test_create_batch_generates_unique_batch_id(self, db_session, mock_action_type):
        """Should generate unique batch_id for each batch."""
        service = BatchJobService(db_session)

        # Mock action type lookup
        db_session.query = Mock(return_value=Mock(
            filter=Mock(return_value=Mock(
                first=Mock(return_value=mock_action_type)
            ))
        ))

        batch1 = service.create_batch_job(
            marketplace="vinted",
            action_code="publish",
            product_ids=[1, 2],
            priority=3
        )

        batch2 = service.create_batch_job(
            marketplace="vinted",
            action_code="publish",
            product_ids=[3, 4],
            priority=3
        )

        assert batch1.batch_id != batch2.batch_id


class TestBatchJobServiceProgress:
    """Test batch progress tracking."""

    def test_update_batch_progress_all_completed(self, db_session):
        """Should update batch to COMPLETED when all jobs completed."""
        service = BatchJobService(db_session)

        # Create mock batch
        batch = BatchJob(
            id=1,
            batch_id="test_batch_1",
            marketplace="vinted",
            action_code="publish",
            total_count=3,
            status=BatchJobStatus.RUNNING,
            priority=3,
            created_at=datetime.now(timezone.utc)
        )

        # Create mock jobs (all completed)
        jobs = [
            MarketplaceJob(
                id=1,
                batch_job_id=1,
                marketplace="vinted",
                action_type_id=1,
                product_id=101,
                status=JobStatus.COMPLETED,
                priority=3,
                retry_count=0,
                max_retries=3,
                created_at=datetime.now(timezone.utc)
            ),
            MarketplaceJob(
                id=2,
                batch_job_id=1,
                marketplace="vinted",
                action_type_id=1,
                product_id=102,
                status=JobStatus.COMPLETED,
                priority=3,
                retry_count=0,
                max_retries=3,
                created_at=datetime.now(timezone.utc)
            ),
            MarketplaceJob(
                id=3,
                batch_job_id=1,
                marketplace="vinted",
                action_type_id=1,
                product_id=103,
                status=JobStatus.COMPLETED,
                priority=3,
                retry_count=0,
                max_retries=3,
                created_at=datetime.now(timezone.utc)
            ),
        ]

        # Mock query chain for batch and jobs
        def query_side_effect(model):
            if model == BatchJob:
                # For batch query
                return Mock(filter=Mock(return_value=Mock(first=Mock(return_value=batch))))
            else:  # MarketplaceJob
                # For jobs query
                return Mock(filter=Mock(return_value=Mock(all=Mock(return_value=jobs))))

        db_session.query = Mock(side_effect=query_side_effect)

        # Update progress
        updated_batch = service.update_batch_progress(1)

        assert updated_batch.completed_count == 3
        assert updated_batch.failed_count == 0
        assert updated_batch.cancelled_count == 0
        assert updated_batch.status == BatchJobStatus.COMPLETED

    def test_update_batch_progress_partially_failed(self, db_session):
        """Should update batch to PARTIALLY_FAILED when some jobs failed."""
        service = BatchJobService(db_session)

        # Create mock batch
        batch = BatchJob(
            id=1,
            batch_id="test_batch_2",
            marketplace="vinted",
            action_code="publish",
            total_count=3,
            status=BatchJobStatus.RUNNING,
            priority=3,
            created_at=datetime.now(timezone.utc)
        )

        # Create mock jobs (2 completed, 1 failed)
        jobs = [
            MarketplaceJob(
                id=1,
                batch_job_id=1,
                marketplace="vinted",
                action_type_id=1,
                product_id=101,
                status=JobStatus.COMPLETED,
                priority=3,
                retry_count=0,
                max_retries=3,
                created_at=datetime.now(timezone.utc)
            ),
            MarketplaceJob(
                id=2,
                batch_job_id=1,
                marketplace="vinted",
                action_type_id=1,
                product_id=102,
                status=JobStatus.COMPLETED,
                priority=3,
                retry_count=0,
                max_retries=3,
                created_at=datetime.now(timezone.utc)
            ),
            MarketplaceJob(
                id=3,
                batch_job_id=1,
                marketplace="vinted",
                action_type_id=1,
                product_id=103,
                status=JobStatus.FAILED,
                priority=3,
                retry_count=3,
                max_retries=3,
                created_at=datetime.now(timezone.utc)
            ),
        ]

        # Mock query chain for batch and jobs
        def query_side_effect(model):
            if model == BatchJob:
                return Mock(filter=Mock(return_value=Mock(first=Mock(return_value=batch))))
            else:  # MarketplaceJob
                return Mock(filter=Mock(return_value=Mock(all=Mock(return_value=jobs))))

        db_session.query = Mock(side_effect=query_side_effect)

        # Update progress
        updated_batch = service.update_batch_progress(1)

        assert updated_batch.completed_count == 2
        assert updated_batch.failed_count == 1
        assert updated_batch.status == BatchJobStatus.PARTIALLY_FAILED

    def test_update_batch_progress_still_running(self, db_session):
        """Should keep batch as RUNNING when jobs still in progress."""
        service = BatchJobService(db_session)

        # Create mock batch
        batch = BatchJob(
            id=1,
            batch_id="test_batch_3",
            marketplace="vinted",
            action_code="publish",
            total_count=3,
            status=BatchJobStatus.RUNNING,
            priority=3,
            created_at=datetime.now(timezone.utc)
        )

        # Create mock jobs (1 completed, 2 running)
        jobs = [
            MarketplaceJob(
                id=1,
                batch_job_id=1,
                marketplace="vinted",
                action_type_id=1,
                product_id=101,
                status=JobStatus.COMPLETED,
                priority=3,
                retry_count=0,
                max_retries=3,
                created_at=datetime.now(timezone.utc)
            ),
            MarketplaceJob(
                id=2,
                batch_job_id=1,
                marketplace="vinted",
                action_type_id=1,
                product_id=102,
                status=JobStatus.RUNNING,
                priority=3,
                retry_count=0,
                max_retries=3,
                created_at=datetime.now(timezone.utc)
            ),
            MarketplaceJob(
                id=3,
                batch_job_id=1,
                marketplace="vinted",
                action_type_id=1,
                product_id=103,
                status=JobStatus.PENDING,
                priority=3,
                retry_count=0,
                max_retries=3,
                created_at=datetime.now(timezone.utc)
            ),
        ]

        # Mock query chain for batch and jobs
        def query_side_effect(model):
            if model == BatchJob:
                return Mock(filter=Mock(return_value=Mock(first=Mock(return_value=batch))))
            else:  # MarketplaceJob
                return Mock(filter=Mock(return_value=Mock(all=Mock(return_value=jobs))))

        db_session.query = Mock(side_effect=query_side_effect)

        # Update progress
        updated_batch = service.update_batch_progress(1)

        assert updated_batch.completed_count == 1
        assert updated_batch.status == BatchJobStatus.RUNNING


class TestBatchJobServiceCancel:
    """Test batch cancellation."""

    def test_cancel_batch_cancels_pending_and_running(self, db_session):
        """Should cancel all pending and running jobs in batch."""
        service = BatchJobService(db_session)

        # Create mock batch
        batch = BatchJob(
            id=1,
            batch_id="test_batch_4",
            marketplace="vinted",
            action_code="publish",
            total_count=4,
            status=BatchJobStatus.RUNNING,
            priority=3,
            created_at=datetime.now(timezone.utc)
        )

        # Create mock jobs (1 completed, 1 running, 2 pending)
        # Only running/pending jobs should be returned by the filtered query
        cancelable_jobs = [
            MarketplaceJob(
                id=2,
                batch_job_id=1,
                marketplace="vinted",
                action_type_id=1,
                product_id=102,
                status=JobStatus.RUNNING,  # Should be cancelled
                priority=3,
                retry_count=0,
                max_retries=3,
                created_at=datetime.now(timezone.utc)
            ),
            MarketplaceJob(
                id=3,
                batch_job_id=1,
                marketplace="vinted",
                action_type_id=1,
                product_id=103,
                status=JobStatus.PENDING,  # Should be cancelled
                priority=3,
                retry_count=0,
                max_retries=3,
                created_at=datetime.now(timezone.utc)
            ),
            MarketplaceJob(
                id=4,
                batch_job_id=1,
                marketplace="vinted",
                action_type_id=1,
                product_id=104,
                status=JobStatus.PENDING,  # Should be cancelled
                priority=3,
                retry_count=0,
                max_retries=3,
                created_at=datetime.now(timezone.utc)
            ),
        ]

        # Tasks removed (2026-01-09): WebSocket architecture, no granular tasks in DB

        # Completed job for progress update
        completed_job = MarketplaceJob(
            id=1,
            batch_job_id=1,
            marketplace="vinted",
            action_type_id=1,
            product_id=101,
            status=JobStatus.COMPLETED,
            priority=3,
            retry_count=0,
            max_retries=3,
            created_at=datetime.now(timezone.utc)
        )

        # All jobs for progress update (use same instances so status changes are reflected)
        all_jobs = [completed_job] + cancelable_jobs

        # Mock query chain - need to handle multiple calls
        call_count = [0]  # Mutable to track calls

        def query_side_effect(model):
            call_count[0] += 1
            if model == BatchJob:
                # Batch query (first call)
                return Mock(filter=Mock(return_value=Mock(first=Mock(return_value=batch))))
            else:  # MarketplaceJob
                if call_count[0] == 2:
                    # Cancel query - needs .filter().filter().all() chain (no options)
                    mock_all = Mock(all=Mock(return_value=cancelable_jobs))
                    mock_filter2 = Mock(filter=Mock(return_value=mock_all))
                    mock_filter1 = Mock(return_value=mock_filter2)
                    return Mock(filter=mock_filter1)
                else:
                    # Progress update query - all jobs
                    return Mock(filter=Mock(return_value=Mock(all=Mock(return_value=all_jobs))))

        db_session.query = Mock(side_effect=query_side_effect)

        # Cancel batch
        cancelled_count = service.cancel_batch(1)

        # Should cancel 3 jobs (1 running + 2 pending)
        assert cancelled_count == 3
        assert cancelable_jobs[0].status == JobStatus.CANCELLED
        assert cancelable_jobs[1].status == JobStatus.CANCELLED
        assert cancelable_jobs[2].status == JobStatus.CANCELLED
        assert batch.status == BatchJobStatus.CANCELLED

    def test_cancel_batch_invalid_id_raises(self, db_session):
        """Should raise ValueError for invalid batch_id."""
        service = BatchJobService(db_session)

        # Mock batch not found
        db_session.query = Mock(return_value=Mock(
            filter=Mock(return_value=Mock(first=Mock(return_value=None)))
        ))

        with pytest.raises(ValueError, match="BatchJob with id=999 not found"):
            service.cancel_batch(999)


class TestBatchJobServiceSummary:
    """Test batch summary retrieval."""

    def test_get_batch_summary_success(self, db_session):
        """Should return batch summary dict."""
        service = BatchJobService(db_session)

        # Create mock batch
        batch = BatchJob(
            id=1,
            batch_id="test_batch_5",
            marketplace="vinted",
            action_code="publish",
            total_count=10,
            completed_count=7,
            failed_count=2,
            cancelled_count=1,
            status=BatchJobStatus.PARTIALLY_FAILED,
            priority=3,
            created_at=datetime.now(timezone.utc)
        )

        # Mock query chain with options()
        mock_filter = Mock(return_value=Mock(first=Mock(return_value=batch)))
        mock_options = Mock(return_value=Mock(filter=mock_filter))
        db_session.query = Mock(return_value=Mock(options=mock_options))

        # Get summary
        summary = service.get_batch_summary("test_batch_5")

        assert summary is not None
        assert summary["batch_id"] == "test_batch_5"
        assert summary["marketplace"] == "vinted"
        assert summary["total_count"] == 10
        assert summary["completed_count"] == 7
        assert summary["failed_count"] == 2
        assert summary["cancelled_count"] == 1
        assert summary["pending_count"] == 0  # 10 - 7 - 2 - 1
        assert summary["progress_percent"] == 70.0  # 7/10

    def test_get_batch_summary_not_found_returns_none(self, db_session):
        """Should return None when batch not found."""
        service = BatchJobService(db_session)

        # Mock batch not found
        mock_filter = Mock(return_value=Mock(first=Mock(return_value=None)))
        mock_options = Mock(return_value=Mock(filter=mock_filter))
        db_session.query = Mock(return_value=Mock(options=mock_options))

        summary = service.get_batch_summary("nonexistent_batch")
        assert summary is None


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def db_session():
    """Mock database session."""
    session = Mock(spec=["query", "add", "flush", "commit", "rollback"])
    return session


@pytest.fixture
def mock_action_type():
    """Mock VintedActionType."""
    return VintedActionType(
        id=1,
        code="publish",
        name="Publish Product",
        priority=3
    )
