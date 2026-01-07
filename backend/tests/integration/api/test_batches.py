"""
Integration Tests for Batch API Endpoints

Tests the /api/batches endpoints with real database interactions.

Created: 2026-01-07
Phase 6.2: Integration testing
"""

import pytest
from fastapi import status
from sqlalchemy.orm import Session

from models.user.batch_job import BatchJob, BatchJobStatus
from models.user.marketplace_job import MarketplaceJob, JobStatus
from models.vinted.vinted_action_type import VintedActionType
from services.marketplace.batch_job_service import BatchJobService


class TestCreateBatch:
    """Test POST /api/batches - Create batch job."""

    def test_create_batch_success(self, client, auth_headers, db_session):
        """Should create a batch with child jobs."""
        # Create test products (assuming they exist)
        product_ids = [1, 2, 3]

        payload = {
            "marketplace": "vinted",
            "action_code": "publish",
            "product_ids": product_ids,
            "priority": 3
        }

        response = client.post(
            "/api/batches",
            json=payload,
            headers=auth_headers
        )

        # DEBUG: Print error details if status != 201
        if response.status_code != status.HTTP_201_CREATED:
            print(f"\n❌ ERROR {response.status_code}: {response.json()}")

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        assert data["marketplace"] == "vinted"
        assert data["action_code"] == "publish"
        assert data["total_count"] == 3
        assert data["status"] == "pending"

        # Verify batch exists in database
        batch_id = data["batch_id"]
        batch = db_session.query(BatchJob).filter(
            BatchJob.batch_id == batch_id
        ).first()
        assert batch is not None
        assert batch.total_count == 3

        # Verify child jobs were created
        jobs = db_session.query(MarketplaceJob).filter(
            MarketplaceJob.batch_job_id == batch.id
        ).all()
        assert len(jobs) == 3

    def test_create_batch_empty_products_fails(self, client, auth_headers):
        """Should fail with 422 when product_ids is empty (Pydantic validation)."""
        payload = {
            "marketplace": "vinted",
            "action_code": "publish",
            "product_ids": [],
            "priority": 3
        }

        response = client.post(
            "/api/batches",
            json=payload,
            headers=auth_headers
        )

        # Pydantic validation returns 422 for min_items violation
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_batch_invalid_action_fails(self, client, auth_headers):
        """Should fail with 400 when action_code is invalid."""
        payload = {
            "marketplace": "vinted",
            "action_code": "invalid_action",
            "product_ids": [1, 2, 3],
            "priority": 3
        }

        response = client.post(
            "/api/batches",
            json=payload,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "Invalid action_code" in data["detail"]

    def test_create_batch_without_auth_fails(self, client):
        """Should fail with 403 when not authenticated."""
        payload = {
            "marketplace": "vinted",
            "action_code": "publish",
            "product_ids": [1, 2, 3]
        }

        response = client.post("/api/batches", json=payload)
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestListBatches:
    """Test GET /api/batches - List active batches."""

    def test_list_batches_success(self, client, auth_headers, db_session):
        """Should return list of active batches."""
        # Create test batches
        service = BatchJobService(db_session)
        batch1 = service.create_batch_job(
            marketplace="vinted",
            action_code="publish",
            product_ids=[1, 2],
            priority=3
        )
        batch2 = service.create_batch_job(
            marketplace="vinted",
            action_code="link_product",
            product_ids=[3, 4, 5],
            priority=2
        )

        response = client.get("/api/batches", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "batches" in data
        assert len(data["batches"]) >= 2

        # Verify our batches are in the list
        batch_ids = [b["batch_id"] for b in data["batches"]]
        assert batch1.batch_id in batch_ids
        assert batch2.batch_id in batch_ids

    def test_list_batches_filtered_by_marketplace(
        self, client, auth_headers, db_session
    ):
        """Should return only batches for specified marketplace."""
        # Create test batches for different marketplaces
        service = BatchJobService(db_session)
        vinted_batch = service.create_batch_job(
            marketplace="vinted",
            action_code="publish",
            product_ids=[1, 2],
            priority=3
        )

        response = client.get(
            "/api/batches?marketplace=vinted",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "batches" in data
        # All returned batches should be for vinted
        for batch in data["batches"]:
            assert batch["marketplace"] == "vinted"

    def test_list_batches_respects_limit(self, client, auth_headers, db_session):
        """Should respect limit parameter."""
        # Create multiple batches
        service = BatchJobService(db_session)
        for i in range(5):
            service.create_batch_job(
                marketplace="vinted",
                action_code="publish",
                product_ids=[i * 10 + j for j in range(1, 4)],
                priority=3
            )

        response = client.get(
            "/api/batches?limit=3",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "batches" in data
        assert len(data["batches"]) <= 3

    def test_list_batches_without_auth_fails(self, client):
        """Should fail with 403 when not authenticated."""
        response = client.get("/api/batches")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestGetBatch:
    """Test GET /api/batches/{batch_id} - Get batch summary."""

    def test_get_batch_success(self, client, auth_headers, db_session):
        """Should return batch summary."""
        # Create test batch
        service = BatchJobService(db_session)
        batch = service.create_batch_job(
            marketplace="vinted",
            action_code="publish",
            product_ids=[1, 2, 3],
            priority=3
        )

        response = client.get(
            f"/api/batches/{batch.batch_id}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["batch_id"] == batch.batch_id
        assert data["marketplace"] == "vinted"
        assert data["action_code"] == "publish"
        assert data["total_count"] == 3
        assert data["status"] == "pending"
        assert "progress_percent" in data

    def test_get_batch_not_found(self, client, auth_headers):
        """Should return 404 when batch not found."""
        response = client.get(
            "/api/batches/nonexistent_batch_id",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_get_batch_without_auth_fails(self, client):
        """Should fail with 403 when not authenticated."""
        # Use fake batch_id since we're testing auth failure
        fake_batch_id = "test_batch_123"

        response = client.get(f"/api/batches/{fake_batch_id}")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestCancelBatch:
    """Test POST /api/batches/{batch_id}/cancel - Cancel batch."""

    def test_cancel_batch_success(self, client, auth_headers, db_session, test_user):
        """Should cancel batch and all child jobs."""
        # Configure search_path for verification queries
        user, _ = test_user
        from sqlalchemy import text
        db_session.execute(text(f"SET search_path TO {user.schema_name}, public"))

        # Create test batch via API (not directly with service to avoid transaction conflicts)
        create_response = client.post(
            "/api/batches",
            json={
                "marketplace": "vinted",
                "action_code": "publish",
                "product_ids": [1, 2, 3],
                "priority": 3
            },
            headers=auth_headers
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        batch_id = create_response.json()["batch_id"]

        response = client.post(
            f"/api/batches/{batch_id}/cancel",
            headers=auth_headers
        )

        # DEBUG: Print error if status != 200
        if response.status_code != status.HTTP_200_OK:
            print(f"\n❌ CANCEL ERROR {response.status_code}: {response.json()}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "cancelled_count" in data
        assert data["cancelled_count"] == 3
        assert "message" in data

        # Verify batch status in database
        batch = db_session.query(BatchJob).filter(
            BatchJob.batch_id == batch_id
        ).first()
        assert batch is not None
        assert batch.status == BatchJobStatus.CANCELLED

        # Verify child jobs are cancelled
        jobs = db_session.query(MarketplaceJob).filter(
            MarketplaceJob.batch_job_id == batch.id
        ).all()
        for job in jobs:
            assert job.status == JobStatus.CANCELLED

    def test_cancel_batch_not_found(self, client, auth_headers):
        """Should return 404 when batch not found."""
        response = client.post(
            "/api/batches/nonexistent_batch_id/cancel",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_cancel_batch_without_auth_fails(self, client):
        """Should fail with 403 when not authenticated."""
        # Use fake batch_id since we're testing auth failure
        fake_batch_id = "test_batch_123"

        response = client.post(f"/api/batches/{fake_batch_id}/cancel")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestGetBatchJobs:
    """Test GET /api/batches/{batch_id}/jobs - Get child jobs."""

    def test_get_batch_jobs_success(self, client, auth_headers, db_session):
        """Should return list of child jobs."""
        # Create test batch
        service = BatchJobService(db_session)
        batch = service.create_batch_job(
            marketplace="vinted",
            action_code="publish",
            product_ids=[1, 2, 3],
            priority=3
        )

        response = client.get(
            f"/api/batches/{batch.batch_id}/jobs",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "jobs" in data
        assert len(data["jobs"]) == 3

        # Verify job structure
        for job in data["jobs"]:
            assert "id" in job
            assert "product_id" in job
            assert "status" in job
            assert "marketplace" in job
            assert job["marketplace"] == "vinted"

    def test_get_batch_jobs_not_found(self, client, auth_headers):
        """Should return 404 when batch not found."""
        response = client.get(
            "/api/batches/nonexistent_batch_id/jobs",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_get_batch_jobs_without_auth_fails(self, client):
        """Should fail with 403 when not authenticated."""
        # Use fake batch_id since we're testing auth failure
        fake_batch_id = "test_batch_123"

        response = client.get(f"/api/batches/{fake_batch_id}/jobs")
        assert response.status_code == status.HTTP_403_FORBIDDEN
