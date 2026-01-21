"""
Unit Tests for MarketplaceBatch Migration Script

Tests the helper functions used in the retroactive migration script.

Created: 2026-01-07
Phase 5.1: Data migration testing
"""

import pytest
from datetime import datetime, timezone

from models.user.marketplace_batch import MarketplaceBatchStatus
from models.user.marketplace_job import MarketplaceJob, JobStatus
from scripts.migrate_existing_jobs_to_batch import (
    extract_action_from_batch_id,
    calculate_batch_status,
)


class TestExtractActionFromBatchId:
    """Test action extraction from batch_id string."""

    def test_extract_publish_action(self):
        """Should extract 'publish' from batch_id."""
        batch_id = "publish_20260107_120530_abc123"
        assert extract_action_from_batch_id(batch_id) == "publish"

    def test_extract_link_product_action(self):
        """Should extract 'link_product' from batch_id."""
        batch_id = "link_product_20260106_091530_def456"
        assert extract_action_from_batch_id(batch_id) == "link_product"

    def test_extract_sync_action(self):
        """Should extract 'sync' from batch_id."""
        batch_id = "sync_20260105_143022_xyz789"
        assert extract_action_from_batch_id(batch_id) == "sync"

    def test_extract_from_short_batch_id(self):
        """Should handle short batch_id with just action."""
        batch_id = "update"
        assert extract_action_from_batch_id(batch_id) == "update"

    def test_extract_from_empty_batch_id(self):
        """Should return 'unknown' for empty batch_id."""
        batch_id = ""
        assert extract_action_from_batch_id(batch_id) == "unknown"


class TestCalculateBatchStatus:
    """Test batch status calculation from child jobs."""

    def create_job(self, status: JobStatus) -> MarketplaceJob:
        """Helper to create a MarketplaceJob with given status."""
        job = MarketplaceJob(
            marketplace="vinted",
            action_type_id=1,
            product_id=1,
            status=status,
            priority=3,
            retry_count=0,
            max_retries=3,
            created_at=datetime.now(timezone.utc),
        )
        return job

    def test_all_completed(self):
        """Should return COMPLETED when all jobs completed."""
        jobs = [
            self.create_job(JobStatus.COMPLETED),
            self.create_job(JobStatus.COMPLETED),
            self.create_job(JobStatus.COMPLETED),
        ]
        assert calculate_batch_status(jobs) == MarketplaceBatchStatus.COMPLETED

    def test_all_failed(self):
        """Should return FAILED when all jobs failed."""
        jobs = [
            self.create_job(JobStatus.FAILED),
            self.create_job(JobStatus.FAILED),
        ]
        assert calculate_batch_status(jobs) == MarketplaceBatchStatus.FAILED

    def test_all_cancelled(self):
        """Should return CANCELLED when all jobs cancelled."""
        jobs = [
            self.create_job(JobStatus.CANCELLED),
            self.create_job(JobStatus.CANCELLED),
            self.create_job(JobStatus.CANCELLED),
        ]
        assert calculate_batch_status(jobs) == MarketplaceBatchStatus.CANCELLED

    def test_partially_failed(self):
        """Should return PARTIALLY_FAILED when some completed, some failed."""
        jobs = [
            self.create_job(JobStatus.COMPLETED),
            self.create_job(JobStatus.COMPLETED),
            self.create_job(JobStatus.FAILED),
        ]
        assert calculate_batch_status(jobs) == MarketplaceBatchStatus.PARTIALLY_FAILED

    def test_running(self):
        """Should return RUNNING when any job is running."""
        jobs = [
            self.create_job(JobStatus.COMPLETED),
            self.create_job(JobStatus.RUNNING),
            self.create_job(JobStatus.PENDING),
        ]
        assert calculate_batch_status(jobs) == MarketplaceBatchStatus.RUNNING

    def test_pending(self):
        """Should return PENDING for pending jobs."""
        jobs = [
            self.create_job(JobStatus.PENDING),
            self.create_job(JobStatus.PENDING),
        ]
        assert calculate_batch_status(jobs) == MarketplaceBatchStatus.PENDING

    def test_empty_jobs_list(self):
        """Should return PENDING for empty jobs list."""
        jobs = []
        assert calculate_batch_status(jobs) == MarketplaceBatchStatus.PENDING

    def test_mixed_terminal_statuses(self):
        """Should return PARTIALLY_FAILED for mixed terminal statuses."""
        jobs = [
            self.create_job(JobStatus.COMPLETED),
            self.create_job(JobStatus.FAILED),
            self.create_job(JobStatus.CANCELLED),
        ]
        # Has both completed and failed, so partially_failed
        assert calculate_batch_status(jobs) == MarketplaceBatchStatus.PARTIALLY_FAILED


class TestMigrationScriptIntegration:
    """Integration tests for the migration script."""

    @pytest.mark.skip(reason="Requires database setup - manual testing only")
    def test_migrate_schema(self, db_session):
        """
        Integration test for migrate_schema function.

        This test should be run manually in a test environment.
        It requires:
        1. A test database with old batch_id jobs
        2. The migrate_schema function imported
        3. A test schema with sample data
        """
        pass

    @pytest.mark.skip(reason="Requires database setup - manual testing only")
    def test_idempotency(self, db_session):
        """
        Test that running migration twice doesn't create duplicates.

        This test should be run manually to verify idempotency.
        """
        pass


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def sample_jobs():
    """Fixture providing sample jobs for testing."""
    now = datetime.now(timezone.utc)
    return [
        MarketplaceJob(
            id=1,
            marketplace="vinted",
            action_type_id=1,
            product_id=101,
            batch_id="publish_20260107_120530_abc123",
            status=JobStatus.COMPLETED,
            priority=3,
            retry_count=0,
            max_retries=3,
            created_at=now,
        ),
        MarketplaceJob(
            id=2,
            marketplace="vinted",
            action_type_id=1,
            product_id=102,
            batch_id="publish_20260107_120530_abc123",
            status=JobStatus.RUNNING,
            priority=3,
            retry_count=0,
            max_retries=3,
            created_at=now,
        ),
    ]
