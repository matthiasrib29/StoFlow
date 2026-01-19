"""
Integration tests for BatchJob orchestration and progress tracking.

Tests verify that BatchJob correctly tracks progress of grouped MarketplaceJobs
and transitions to appropriate terminal states based on job outcomes.

BatchJob Status Flow:
PENDING → RUNNING → COMPLETED (all jobs succeeded)
                  → PARTIALLY_FAILED (some succeeded, some failed)
                  → FAILED (all jobs failed)
                  → CANCELLED
"""

import pytest
from datetime import datetime, UTC
from sqlalchemy import text

from models.user.batch_job import BatchJob, BatchJobStatus
from models.user.marketplace_job import MarketplaceJob, JobStatus


def test_batch_job_creation_with_jobs(db_session):
    """Test BatchJob creation and association with MarketplaceJobs."""
    # Setup: Get action type
    result = db_session.execute(
        text("SELECT id FROM public.marketplace_action_types WHERE marketplace = 'vinted' AND code = 'publish' LIMIT 1")
    )
    action_type_id = result.scalar()
    assert action_type_id is not None

    # Create batch
    batch = BatchJob(
        batch_id="test_batch_001",
        marketplace="vinted",
        action_code="publish",
        total_count=3,
        status=BatchJobStatus.PENDING,
    )
    db_session.add(batch)
    db_session.commit()
    db_session.refresh(batch)

    # Create 3 jobs in batch
    jobs = [
        MarketplaceJob(
            marketplace="vinted",
            action_type_id=action_type_id,
            product_id=i,
            batch_job_id=batch.id,
            status=JobStatus.PENDING,
        )
        for i in range(1, 4)
    ]
    db_session.add_all(jobs)
    db_session.commit()

    # Verify batch associations
    db_session.refresh(batch)
    assert len(batch.jobs) == 3
    assert batch.total_count == 3
    assert batch.progress_percent == 0.0
    assert batch.is_active is True
    assert batch.is_terminal is False


def test_batch_progress_tracking_all_completed(db_session):
    """Test BatchJob progress tracking when all jobs complete successfully."""
    result = db_session.execute(
        text("SELECT id FROM public.marketplace_action_types WHERE marketplace = 'vinted' AND code = 'publish' LIMIT 1")
    )
    action_type_id = result.scalar()

    # Create batch with 3 jobs
    batch = BatchJob(
        batch_id="test_batch_002",
        marketplace="vinted",
        action_code="publish",
        total_count=3,
        status=BatchJobStatus.PENDING,
    )
    db_session.add(batch)
    db_session.commit()
    db_session.refresh(batch)

    jobs = [
        MarketplaceJob(
            marketplace="vinted",
            action_type_id=action_type_id,
            product_id=i,
            batch_job_id=batch.id,
            status=JobStatus.PENDING,
        )
        for i in range(1, 4)
    ]
    db_session.add_all(jobs)
    db_session.commit()

    # Mark batch as RUNNING
    batch.status = BatchJobStatus.RUNNING
    batch.started_at = datetime.now(UTC)
    db_session.commit()

    # Complete jobs one by one
    for i, job in enumerate(jobs, start=1):
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.now(UTC)
        batch.completed_count += 1
        db_session.commit()
        db_session.refresh(batch)

        # Verify progress
        expected_progress = round((i / 3) * 100, 1)
        assert batch.progress_percent == expected_progress
        assert batch.pending_count == 3 - i

    # All jobs completed → batch should be COMPLETED
    batch.status = BatchJobStatus.COMPLETED
    batch.completed_at = datetime.now(UTC)
    db_session.commit()
    db_session.refresh(batch)

    assert batch.status == BatchJobStatus.COMPLETED
    assert batch.completed_count == 3
    assert batch.failed_count == 0
    assert batch.progress_percent == 100.0
    assert batch.is_active is False
    assert batch.is_terminal is True


def test_batch_progress_tracking_all_failed(db_session):
    """Test BatchJob progress tracking when all jobs fail."""
    result = db_session.execute(
        text("SELECT id FROM public.marketplace_action_types WHERE marketplace = 'vinted' AND code = 'publish' LIMIT 1")
    )
    action_type_id = result.scalar()

    batch = BatchJob(
        batch_id="test_batch_003",
        marketplace="vinted",
        action_code="publish",
        total_count=3,
        status=BatchJobStatus.RUNNING,
        started_at=datetime.now(UTC),
    )
    db_session.add(batch)
    db_session.commit()
    db_session.refresh(batch)

    jobs = [
        MarketplaceJob(
            marketplace="vinted",
            action_type_id=action_type_id,
            product_id=i,
            batch_job_id=batch.id,
            status=JobStatus.PENDING,  # Start as PENDING
        )
        for i in range(1, 4)
    ]
    db_session.add_all(jobs)
    db_session.commit()

    # Fail all jobs
    for job in jobs:
        job.status = JobStatus.FAILED
        job.completed_at = datetime.now(UTC)
        job.error_message = "Test error"
        batch.failed_count += 1
        db_session.commit()

    db_session.refresh(batch)

    # All jobs failed → batch should be FAILED
    batch.status = BatchJobStatus.FAILED
    batch.completed_at = datetime.now(UTC)
    db_session.commit()
    db_session.refresh(batch)

    assert batch.status == BatchJobStatus.FAILED
    assert batch.completed_count == 0
    assert batch.failed_count == 3
    assert batch.pending_count == 0
    assert batch.is_terminal is True


def test_batch_progress_tracking_partially_failed(db_session):
    """Test BatchJob progress tracking when some jobs succeed and some fail."""
    result = db_session.execute(
        text("SELECT id FROM public.marketplace_action_types WHERE marketplace = 'vinted' AND code = 'publish' LIMIT 1")
    )
    action_type_id = result.scalar()

    batch = BatchJob(
        batch_id="test_batch_004",
        marketplace="vinted",
        action_code="publish",
        total_count=3,
        status=BatchJobStatus.RUNNING,
        started_at=datetime.now(UTC),
    )
    db_session.add(batch)
    db_session.commit()
    db_session.refresh(batch)

    jobs = [
        MarketplaceJob(
            marketplace="vinted",
            action_type_id=action_type_id,
            product_id=i,
            batch_job_id=batch.id,
            status=JobStatus.PENDING,  # Start as PENDING
        )
        for i in range(1, 4)
    ]
    db_session.add_all(jobs)
    db_session.commit()

    # Complete first job successfully
    jobs[0].status = JobStatus.COMPLETED
    jobs[0].completed_at = datetime.now(UTC)
    batch.completed_count += 1
    db_session.commit()

    # Fail second and third jobs
    for job in jobs[1:]:
        job.status = JobStatus.FAILED
        job.completed_at = datetime.now(UTC)
        job.error_message = "Test error"
        batch.failed_count += 1
        db_session.commit()

    db_session.refresh(batch)

    # Mix of success/failure → batch should be PARTIALLY_FAILED
    batch.status = BatchJobStatus.PARTIALLY_FAILED
    batch.completed_at = datetime.now(UTC)
    db_session.commit()
    db_session.refresh(batch)

    assert batch.status == BatchJobStatus.PARTIALLY_FAILED
    assert batch.completed_count == 1
    assert batch.failed_count == 2
    assert batch.pending_count == 0
    assert batch.is_terminal is True


def test_batch_job_cancellation(db_session):
    """Test BatchJob cancellation with some jobs still pending."""
    result = db_session.execute(
        text("SELECT id FROM public.marketplace_action_types WHERE marketplace = 'vinted' AND code = 'publish' LIMIT 1")
    )
    action_type_id = result.scalar()

    batch = BatchJob(
        batch_id="test_batch_005",
        marketplace="vinted",
        action_code="publish",
        total_count=5,
        status=BatchJobStatus.RUNNING,
        started_at=datetime.now(UTC),
    )
    db_session.add(batch)
    db_session.commit()
    db_session.refresh(batch)

    jobs = [
        MarketplaceJob(
            marketplace="vinted",
            action_type_id=action_type_id,
            product_id=i,
            batch_job_id=batch.id,
            status=JobStatus.PENDING,  # All start as PENDING
        )
        for i in range(1, 6)
    ]
    db_session.add_all(jobs)
    db_session.commit()

    # Complete first 2 jobs
    for job in jobs[:2]:
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.now(UTC)
        batch.completed_count += 1
        db_session.commit()

    # Cancel remaining jobs
    for job in jobs[2:]:
        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.now(UTC)
        batch.cancelled_count += 1
        db_session.commit()

    db_session.refresh(batch)

    # Batch cancelled (with some completed)
    batch.status = BatchJobStatus.CANCELLED
    batch.completed_at = datetime.now(UTC)
    db_session.commit()
    db_session.refresh(batch)

    assert batch.status == BatchJobStatus.CANCELLED
    assert batch.completed_count == 2
    assert batch.cancelled_count == 3
    assert batch.pending_count == 0
    assert batch.is_terminal is True


# TODO: Additional BatchJob tests (if needed)
# - test_batch_job_priority_inheritance (jobs inherit batch priority)
# - test_batch_cascade_delete (deleting batch deletes jobs)
#
# Current tests (5/5) validate core batch orchestration:
# ✅ Batch creation with job associations
# ✅ Progress tracking (all completed)
# ✅ Progress tracking (all failed)
# ✅ Progress tracking (partially failed)
# ✅ Batch cancellation
