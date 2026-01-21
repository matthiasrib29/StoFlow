"""
Batch Jobs API Routes

Generic endpoints for managing batch operations across marketplaces.

Endpoints:
- POST /api/batches: Create a new batch job
- GET /api/batches: List active batch jobs
- GET /api/batches/{batch_id}: Get batch summary
- POST /api/batches/{batch_id}/cancel: Cancel batch
- GET /api/batches/{batch_id}/jobs: Get child jobs

Author: Claude
Date: 2026-01-07
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from api.dependencies import get_user_db
from models.user.marketplace_batch import MarketplaceBatch, MarketplaceBatchStatus
from models.user.marketplace_job import MarketplaceJob
from services.marketplace.marketplace_batch_service import MarketplaceBatchService
from services.marketplace.marketplace_job_service import MarketplaceJobService

router = APIRouter(prefix="/batches", tags=["Batch Jobs"])


# =============================================================================
# SCHEMAS
# =============================================================================


class BatchCreateRequest(BaseModel):
    """Request schema for creating a batch job."""

    marketplace: str = Field(..., description="Target marketplace (vinted, ebay, etsy)")
    action_code: str = Field(
        ..., description="Action code (publish, update, delete, link_product, sync)"
    )
    product_ids: list[int] = Field(..., min_length=1, description="List of product IDs")
    priority: Optional[int] = Field(
        None, ge=1, le=4, description="Priority override (1=CRITICAL, 4=LOW)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "marketplace": "vinted",
                "action_code": "link_product",
                "product_ids": [123, 456, 789],
                "priority": 3,
            }
        }
    )


class BatchCreateResponse(BaseModel):
    """Response schema for batch creation."""

    id: int
    batch_id: str
    marketplace: str
    action_code: str
    total_count: int
    status: str
    priority: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BatchSummaryResponse(BaseModel):
    """Response schema for batch summary."""

    id: int
    batch_id: str
    marketplace: str
    action_code: str
    status: str
    priority: int
    total_count: int
    completed_count: int
    failed_count: int
    cancelled_count: int
    pending_count: int
    progress_percent: float
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class BatchListResponse(BaseModel):
    """Response schema for batch list."""

    batches: list[BatchSummaryResponse]
    total: int


class JobResponse(BaseModel):
    """Response schema for a marketplace job."""

    id: int
    marketplace_batch_id: Optional[int] = None
    marketplace: str
    action_type_id: int
    product_id: Optional[int] = None
    status: str
    priority: int
    error_message: Optional[str] = None
    retry_count: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class BatchJobsResponse(BaseModel):
    """Response schema for batch child jobs."""

    batch_id: str
    total: int
    jobs: list[JobResponse]


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.post("", response_model=BatchCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_batch(
    request: BatchCreateRequest,
    db_user: tuple[Session, any] = Depends(get_user_db),
):
    """
    Create a new batch job.

    Creates a MarketplaceBatch parent with N MarketplaceJobs (1 per product).

    Args:
        request: Batch creation parameters
        db_user: Database session and user

    Returns:
        Created MarketplaceBatch summary

    Raises:
        400: Invalid action_code or empty product_ids
        500: Internal server error
    """
    db, user = db_user

    try:
        batch_service = MarketplaceBatchService(db)
        batch = batch_service.create_batch_job(
            marketplace=request.marketplace,
            action_code=request.action_code,
            product_ids=request.product_ids,
            priority=request.priority,
            created_by_user_id=user.id,
        )

        return BatchCreateResponse(
            id=batch.id,
            batch_id=batch.batch_id,
            marketplace=batch.marketplace,
            action_code=batch.action_code,
            total_count=batch.total_count,
            status=batch.status.value,
            priority=batch.priority,
            created_at=batch.created_at,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create batch: {str(e)}",
        )


@router.get("", response_model=BatchListResponse)
async def list_batches(
    marketplace: Optional[str] = Query(None, description="Filter by marketplace"),
    limit: int = Query(50, ge=1, le=100, description="Max results"),
    db_user: tuple[Session, any] = Depends(get_user_db),
):
    """
    List active batch jobs (pending or running).

    Args:
        marketplace: Filter by marketplace (optional)
        limit: Maximum number of results
        db_user: Database session and user

    Returns:
        List of active MarketplaceBatches
    """
    db, user = db_user

    batch_service = MarketplaceBatchService(db)
    batches = batch_service.list_active_batches(marketplace=marketplace, limit=limit)

    batch_responses = [
        BatchSummaryResponse(
            id=batch.id,
            batch_id=batch.batch_id,
            marketplace=batch.marketplace,
            action_code=batch.action_code,
            status=batch.status.value,
            priority=batch.priority,
            total_count=batch.total_count,
            completed_count=batch.completed_count,
            failed_count=batch.failed_count,
            cancelled_count=batch.cancelled_count,
            pending_count=batch.pending_count,
            progress_percent=batch.progress_percent,
            created_at=batch.created_at,
            started_at=batch.started_at,
            completed_at=batch.completed_at,
        )
        for batch in batches
    ]

    return BatchListResponse(batches=batch_responses, total=len(batch_responses))


@router.get("/{batch_id}", response_model=BatchSummaryResponse)
async def get_batch(
    batch_id: str,
    db_user: tuple[Session, any] = Depends(get_user_db),
):
    """
    Get batch summary by batch_id string.

    Args:
        batch_id: Batch identifier (UUID-like string)
        db_user: Database session and user

    Returns:
        MarketplaceBatch summary

    Raises:
        404: Batch not found
    """
    db, user = db_user

    batch_service = MarketplaceBatchService(db)
    summary = batch_service.get_batch_summary(batch_id)

    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch {batch_id} not found",
        )

    # Convert to response model
    return BatchSummaryResponse(
        id=summary["id"],
        batch_id=summary["batch_id"],
        marketplace=summary["marketplace"],
        action_code=summary["action_code"],
        status=summary["status"],
        priority=summary["priority"],
        total_count=summary["total_count"],
        completed_count=summary["completed_count"],
        failed_count=summary["failed_count"],
        cancelled_count=summary["cancelled_count"],
        pending_count=summary["pending_count"],
        progress_percent=summary["progress_percent"],
        created_at=datetime.fromisoformat(summary["created_at"])
        if summary["created_at"]
        else None,
        started_at=datetime.fromisoformat(summary["started_at"])
        if summary["started_at"]
        else None,
        completed_at=datetime.fromisoformat(summary["completed_at"])
        if summary["completed_at"]
        else None,
    )


@router.post("/{batch_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel_batch(
    batch_id: str,
    db_user: tuple[Session, any] = Depends(get_user_db),
):
    """
    Cancel all pending/running jobs in a batch.

    Args:
        batch_id: Batch identifier (UUID-like string)
        db_user: Database session and user

    Returns:
        Number of jobs cancelled

    Raises:
        404: Batch not found
        500: Internal server error
    """
    db, user = db_user

    try:
        batch_service = MarketplaceBatchService(db)

        # Get batch by batch_id string
        batch = (
            db.query(MarketplaceBatch).filter(MarketplaceBatch.batch_id == batch_id).first()
        )

        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch {batch_id} not found",
            )

        # Cancel batch by ID
        cancelled_count = batch_service.cancel_batch(batch.id)

        return {
            "batch_id": batch_id,
            "cancelled_count": cancelled_count,
            "message": f"Cancelled {cancelled_count} jobs in batch {batch_id}",
        }

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel batch: {str(e)}",
        )


@router.get("/{batch_id}/jobs", response_model=BatchJobsResponse)
async def get_batch_jobs(
    batch_id: str,
    db_user: tuple[Session, any] = Depends(get_user_db),
):
    """
    Get all child jobs for a batch.

    Args:
        batch_id: Batch identifier (UUID-like string)
        db_user: Database session and user

    Returns:
        List of MarketplaceJobs in the batch

    Raises:
        404: Batch not found
    """
    db, user = db_user

    # Get batch by batch_id string
    batch = db.query(MarketplaceBatch).filter(MarketplaceBatch.batch_id == batch_id).first()

    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch {batch_id} not found",
        )

    # Get all child jobs
    jobs = (
        db.query(MarketplaceJob)
        .filter(MarketplaceJob.marketplace_batch_id == batch.id)
        .order_by(MarketplaceJob.created_at)
        .all()
    )

    job_responses = [
        JobResponse(
            id=job.id,
            marketplace_batch_id=job.marketplace_batch_id,
            marketplace=job.marketplace,
            action_type_id=job.action_type_id,
            product_id=job.product_id,
            status=job.status.value,
            priority=job.priority,
            error_message=job.error_message,
            retry_count=job.retry_count,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
        )
        for job in jobs
    ]

    return BatchJobsResponse(
        batch_id=batch_id, total=len(job_responses), jobs=job_responses
    )
