"""
eBay Jobs API Routes

Endpoints for managing eBay marketplace jobs:
- GET /jobs: List jobs (with filters)
- POST /jobs/cancel: Cancel a job

Author: Claude
Date: 2026-01-12
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict

from api.dependencies import get_user_db
from models.user.marketplace_job import JobStatus, MarketplaceJob
from models.user.ebay_product import EbayProduct
from services.marketplace.marketplace_job_service import MarketplaceJobService
from shared.logging_setup import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/jobs", tags=["eBay Jobs"])


# =============================================================================
# SCHEMAS
# =============================================================================


class JobResponse(BaseModel):
    """Response schema for a single job."""

    id: int
    batch_id: Optional[str] = None
    action_type_id: int
    action_code: Optional[str] = None
    action_name: Optional[str] = None
    product_id: Optional[int] = None
    product_title: Optional[str] = None
    status: str
    priority: int
    error_message: Optional[str] = None
    retry_count: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    progress: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)


class JobListResponse(BaseModel):
    """Response schema for job list."""

    jobs: list[JobResponse]
    total: int
    pending: int
    running: int
    completed: int
    failed: int


class JobActionResponse(BaseModel):
    """Response schema for job actions."""

    success: bool
    job_id: int
    new_status: str
    message: Optional[str] = None


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.get("", response_model=JobListResponse)
async def list_ebay_jobs(
    user_db: tuple = Depends(get_user_db),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    List eBay jobs with optional filters.

    Returns jobs ordered by priority (highest first), then by creation date.
    """
    db, current_user = user_db
    service = MarketplaceJobService(db)

    # Build query - filter by eBay marketplace
    query = db.query(MarketplaceJob).filter(MarketplaceJob.marketplace == "ebay")

    if status_filter:
        try:
            job_status = JobStatus(status_filter)
            query = query.filter(MarketplaceJob.status == job_status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}",
            )

    # Get total count before pagination
    total = query.count()

    # Get status counts (using separate queries to avoid modifying main query)
    base_query = db.query(MarketplaceJob).filter(MarketplaceJob.marketplace == "ebay")
    pending = base_query.filter(MarketplaceJob.status == JobStatus.PENDING).count()
    running = base_query.filter(MarketplaceJob.status == JobStatus.RUNNING).count()
    completed = base_query.filter(MarketplaceJob.status == JobStatus.COMPLETED).count()
    failed = base_query.filter(MarketplaceJob.status == JobStatus.FAILED).count()

    # Get jobs with pagination
    jobs = (
        query.order_by(MarketplaceJob.priority, MarketplaceJob.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    # Build response with action codes and names
    job_responses = []
    for job in jobs:
        action_type = service.get_action_type_by_id(job.action_type_id)

        # Get product title if job has a product_id
        product_title = None
        if job.product_id:
            product = db.query(EbayProduct).filter(EbayProduct.id == job.product_id).first()
            if product:
                product_title = product.title

        job_responses.append(JobResponse(
            id=job.id,
            batch_id=job.batch_id,
            action_type_id=job.action_type_id,
            action_code=action_type.code if action_type else None,
            action_name=action_type.name if action_type else None,
            product_id=job.product_id,
            product_title=product_title,
            status=job.status.value,
            priority=job.priority,
            error_message=job.error_message,
            retry_count=job.retry_count,
            started_at=job.started_at,
            completed_at=job.completed_at,
            expires_at=job.expires_at,
            created_at=job.created_at,
            progress=job.result_data,  # Use result_data as progress info
        ))

    return JobListResponse(
        jobs=job_responses,
        total=total,
        pending=pending,
        running=running,
        completed=completed,
        failed=failed,
    )


@router.post("/cancel", response_model=JobActionResponse)
async def cancel_ebay_job(
    job_id: int = Query(..., description="Job ID to cancel"),
    user_db: tuple = Depends(get_user_db),
):
    """
    Cancel a specific eBay job.
    """
    db, current_user = user_db

    job = db.query(MarketplaceJob).filter(
        MarketplaceJob.id == job_id,
        MarketplaceJob.marketplace == "ebay"
    ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"eBay job {job_id} not found",
        )

    if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
        return JobActionResponse(
            success=False,
            job_id=job_id,
            new_status=job.status.value,
            message=f"Job already {job.status.value}",
        )

    job.status = JobStatus.CANCELLED
    db.commit()

    logger.info(f"eBay job {job_id} cancelled by user {current_user.id}")

    return JobActionResponse(
        success=True,
        job_id=job_id,
        new_status=JobStatus.CANCELLED.value,
        message="Job cancelled successfully",
    )
