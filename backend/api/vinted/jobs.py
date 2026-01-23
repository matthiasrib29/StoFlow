"""
Vinted Jobs API Routes

Endpoints for managing Vinted jobs:
- GET /jobs: List jobs (with filters)
- GET /jobs/batch/{batch_id}: Get batch summary
- GET /jobs/{job_id}: Get job details
- POST /jobs/batch: Create batch jobs
- POST /jobs/cancel: Cancel job or batch (via job_id or batch_id param)

Updated: 2026-01-05 - Removed pause/resume/stats/process, merged cancel endpoints

Author: Claude
Date: 2025-12-19
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from api.dependencies import get_user_db
from api.dependencies.vinted_dependencies import build_job_response_dict
from models.user.marketplace_job import JobStatus, MarketplaceJob
from models.user.marketplace_batch import MarketplaceBatch
from services.vinted.vinted_job_service import VintedJobService
from services.marketplace.marketplace_batch_service import MarketplaceBatchService
from shared.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/jobs", tags=["Vinted Jobs"])


# =============================================================================
# SCHEMAS
# =============================================================================


class JobResponse(BaseModel):
    """Response schema for a single job (updated 2026-01-15)."""

    id: int
    batch_id: Optional[str] = None
    action_type_id: int
    action_code: Optional[str] = None
    action_name: Optional[str] = None  # Human-readable name for frontend
    product_id: Optional[int] = None
    product_title: Optional[str] = None  # Product title for display
    status: str
    cancel_requested: bool = False  # NEW: Cooperative cancellation flag (2026-01-15)
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


class BatchCreateRequest(BaseModel):
    """Request schema for creating batch jobs."""

    action_code: str = Field(..., description="Action type code (publish, sync, etc.)")
    product_ids: list[int] = Field(..., description="List of product IDs")
    priority: Optional[int] = Field(None, description="Override priority (1-4)")


class BatchCreateResponse(BaseModel):
    """Response schema for batch creation."""

    batch_id: str
    jobs_created: int
    jobs: list[JobResponse]


class BatchSummaryResponse(BaseModel):
    """Response schema for batch summary."""

    batch_id: str
    total: int
    completed: int
    failed: int
    pending: int
    running: int
    paused: int
    cancelled: int
    progress_percent: float


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def build_job_response(
    job: MarketplaceJob,
    service: VintedJobService,
    db: Session,
    include_progress: bool = True
) -> JobResponse:
    """Build a JobResponse with all fields including action_name and product_title."""
    return JobResponse(**build_job_response_dict(
        job=job,
        db=db,
        service=service,
        include_progress=include_progress,
    ))


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.get("", response_model=JobListResponse)
async def list_jobs(
    user_db: tuple = Depends(get_user_db),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    batch_id: Optional[str] = Query(None, description="Filter by batch ID"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    List all jobs with optional filters.

    Returns jobs ordered by priority (highest first), then by creation date.
    """
    db, current_user = user_db
    service = VintedJobService(db)

    # Build query - filter by marketplace="vinted" (this is the Vinted jobs endpoint)
    query = db.query(MarketplaceJob).filter(MarketplaceJob.marketplace == "vinted")

    if status_filter:
        try:
            job_status = JobStatus(status_filter)
            query = query.filter(MarketplaceJob.status == job_status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}",
            )

    if batch_id:
        # Get MarketplaceBatch by batch_id string first
        batch = db.query(MarketplaceBatch).filter(MarketplaceBatch.batch_id == batch_id).first()
        if batch:
            query = query.filter(MarketplaceJob.marketplace_batch_id == batch.id)
        else:
            # If batch not found, return empty results
            query = query.filter(MarketplaceJob.id == -1)  # Always false

    # Get counts (use fresh query for each count to avoid filter stacking)
    base_query = db.query(MarketplaceJob).filter(MarketplaceJob.marketplace == "vinted")
    total = base_query.count()
    pending = base_query.filter(MarketplaceJob.status == JobStatus.PENDING).count()
    running = base_query.filter(MarketplaceJob.status == JobStatus.RUNNING).count()
    completed = base_query.filter(MarketplaceJob.status == JobStatus.COMPLETED).count()
    failed = base_query.filter(MarketplaceJob.status == JobStatus.FAILED).count()

    # Get jobs
    jobs = (
        query.order_by(MarketplaceJob.priority, MarketplaceJob.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    # Build response with action codes, names, product titles and progress
    job_responses = [build_job_response(job, service, db) for job in jobs]

    return JobListResponse(
        jobs=job_responses,
        total=total,
        pending=pending,
        running=running,
        completed=completed,
        failed=failed,
    )


@router.get("/batch/{batch_id}", response_model=BatchSummaryResponse)
async def get_batch_summary(
    batch_id: str,
    user_db: tuple = Depends(get_user_db),
):
    """
    Get summary of a batch operation.

    Returns progress and status counts for all jobs in the batch.
    """
    db, current_user = user_db
    service = VintedJobService(db)

    summary = service.get_batch_summary(batch_id)
    if summary["total"] == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch not found: {batch_id}",
        )

    return BatchSummaryResponse(**summary)




@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    user_db: tuple = Depends(get_user_db),
):
    """
    Get details of a specific job.

    Returns job info with progress if applicable.
    """
    db, current_user = user_db
    service = VintedJobService(db)

    job = service.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {job_id}",
        )

    return build_job_response(job, service, db)


@router.post("/batch", response_model=BatchCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_batch_jobs(
    request: BatchCreateRequest,
    user_db: tuple = Depends(get_user_db),
):
    """
    Create multiple jobs for a batch operation.

    **UPDATED (2026-01-07):** Now uses MarketplaceBatchService for better tracking.
    Creates a MarketplaceBatch parent with N MarketplaceJobs (1 per product).

    **RECOMMENDED:** Use POST /api/batches instead for new code.
    This endpoint is kept for backward compatibility.

    Returns:
        batch_id: UUID-like identifier for the batch
        jobs_created: Number of jobs created
        jobs: List of created job summaries
    """
    db, current_user = user_db

    if not request.product_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="product_ids cannot be empty",
        )

    try:
        # Use MarketplaceBatchService (creates MarketplaceBatch + MarketplaceJobs)
        batch_service = MarketplaceBatchService(db)
        batch = batch_service.create_batch_job(
            marketplace="vinted",
            action_code=request.action_code,
            product_ids=request.product_ids,
            priority=request.priority,
            created_by_user_id=current_user.id,
        )

        # Get child jobs for response
        jobs = (
            db.query(MarketplaceJob)
            .filter(MarketplaceJob.marketplace_batch_id == batch.id)
            .all()
        )

        # Build response using helper (no progress for new jobs)
        job_responses = [
            JobResponse(**build_job_response_dict(
                job=job,
                db=db,
                include_progress=False,
                batch_id_override=batch.batch_id,
            ))
            for job in jobs
        ]

        return BatchCreateResponse(
            batch_id=batch.batch_id,
            jobs_created=len(jobs),
            jobs=job_responses,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create batch: {str(e)}",
        )


@router.post("/cancel")
async def cancel_jobs(
    user_db: tuple = Depends(get_user_db),
    job_id: Optional[int] = Query(None, description="ID job à annuler"),
    batch_id: Optional[str] = Query(None, description="ID batch à annuler (tous les jobs)"),
) -> dict:
    """
    Annule un job ou tous les jobs d'un batch.

    - Avec job_id : annule un job spécifique
    - Avec batch_id : annule tous les jobs du batch

    Exactement un des deux paramètres doit être fourni.

    Returns:
        {
            "success": bool,
            "job_id": int | None,
            "batch_id": str | None,
            "cancelled_count": int,
            "total_jobs": int (batch only),
            "message": str
        }
    """
    db, current_user = user_db

    # Validation: exactly one parameter required
    if (job_id is None) == (batch_id is None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Exactly one of job_id or batch_id must be provided",
        )

    service = VintedJobService(db)

    # Cancel single job
    if job_id:
        # Get job first to check for Temporal workflow
        job = service.get_job(job_id)
        workflow_id = job.input_data.get("workflow_id") if job and job.input_data else None

        job = service.cancel_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel job {job_id} (not found or already terminal)",
            )

        # Send Temporal cancel signal if this is a Temporal workflow
        if workflow_id:
            try:
                from temporal.client import get_temporal_client
                client = await get_temporal_client()
                handle = client.get_workflow_handle(workflow_id)
                await handle.signal("cancel_sync")
                logger.info(f"Sent cancel signal to Temporal workflow {workflow_id}")
            except Exception as e:
                logger.warning(f"Failed to cancel Temporal workflow {workflow_id}: {e}")

        return {
            "success": True,
            "job_id": job_id,
            "cancelled_count": 1,
            "message": f"Job {job_id} cancelled",
        }

    # Cancel batch
    jobs = service.get_batch_jobs(batch_id)
    if not jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch not found: {batch_id}",
        )

    cancelled_count = 0
    for job in jobs:
        if service.cancel_job(job.id):
            cancelled_count += 1

    return {
        "success": True,
        "batch_id": batch_id,
        "cancelled_count": cancelled_count,
        "total_jobs": len(jobs),
        "message": f"Cancelled {cancelled_count}/{len(jobs)} jobs in batch",
    }
