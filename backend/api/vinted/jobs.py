"""
Vinted Jobs API Routes

Endpoints for managing Vinted jobs:
- List jobs (with filters)
- Get job details and progress
- Batch operations
- Pause/Resume/Cancel jobs
- Job statistics

Author: Claude
Date: 2025-12-19
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.dependencies import get_user_db
from models.user.vinted_job import JobStatus, VintedJob
from models.user.product import Product
from services.vinted.vinted_job_service import VintedJobService
from services.vinted.vinted_job_processor import VintedJobProcessor
from .shared import get_active_vinted_connection

router = APIRouter(prefix="/jobs", tags=["Vinted Jobs"])


# =============================================================================
# SCHEMAS
# =============================================================================


class JobResponse(BaseModel):
    """Response schema for a single job."""

    id: int
    batch_id: Optional[str] = None
    action_type_id: int
    action_code: Optional[str] = None
    action_name: Optional[str] = None  # Human-readable name for frontend
    product_id: Optional[int] = None
    product_title: Optional[str] = None  # Product title for display
    status: str
    priority: int
    error_message: Optional[str] = None
    retry_count: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    progress: Optional[dict] = None

    class Config:
        from_attributes = True


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


class JobActionResponse(BaseModel):
    """Response schema for job actions (pause, resume, cancel)."""

    success: bool
    job_id: int
    new_status: str
    message: str


class StatsResponse(BaseModel):
    """Response schema for job statistics."""

    stats: list[dict]
    period_days: int


class InterruptedJobsResponse(BaseModel):
    """Response schema for interrupted jobs check."""

    has_interrupted: bool
    count: int
    jobs: list[JobResponse]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def build_job_response(
    job: VintedJob,
    service: VintedJobService,
    db: Session,
    include_progress: bool = True
) -> JobResponse:
    """
    Build a JobResponse with all fields including action_name and product_title.
    """
    action_type = service.get_action_type_by_id(job.action_type_id)
    progress = service.get_job_progress(job.id) if include_progress else None

    # Get product title if job has a product_id
    product_title = None
    if job.product_id:
        product = db.query(Product).filter(Product.id == job.product_id).first()
        if product:
            product_title = product.title

    return JobResponse(
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
        progress=progress if progress and progress["total"] > 0 else None,
    )


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

    # Build query
    query = db.query(VintedJob)

    if status_filter:
        try:
            job_status = JobStatus(status_filter)
            query = query.filter(VintedJob.status == job_status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}",
            )

    if batch_id:
        query = query.filter(VintedJob.batch_id == batch_id)

    # Get counts
    total = query.count()
    pending = query.filter(VintedJob.status == JobStatus.PENDING).count()
    running = query.filter(VintedJob.status == JobStatus.RUNNING).count()
    completed = query.filter(VintedJob.status == JobStatus.COMPLETED).count()
    failed = query.filter(VintedJob.status == JobStatus.FAILED).count()

    # Get jobs
    jobs = (
        query.order_by(VintedJob.priority, VintedJob.created_at.desc())
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


@router.get("/interrupted", response_model=InterruptedJobsResponse)
async def get_interrupted_jobs(user_db: tuple = Depends(get_user_db)):
    """
    Check for interrupted jobs that need user attention.

    Returns jobs that were running when the plugin was closed
    and need confirmation to resume.
    """
    db, current_user = user_db
    service = VintedJobService(db)

    interrupted = service.get_interrupted_jobs()

    job_responses = [build_job_response(job, service, db, include_progress=False) for job in interrupted]

    return InterruptedJobsResponse(
        has_interrupted=len(interrupted) > 0,
        count=len(interrupted),
        jobs=job_responses,
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


@router.get("/stats", response_model=StatsResponse)
async def get_job_stats(
    user_db: tuple = Depends(get_user_db),
    days: int = Query(7, ge=1, le=30, description="Number of days to look back"),
):
    """
    Get job statistics for the last N days.

    Returns daily stats grouped by action type.
    """
    db, current_user = user_db
    service = VintedJobService(db)

    stats = service.get_stats(days=days)

    return StatsResponse(stats=stats, period_days=days)


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

    Used when publishing multiple products at once.
    Returns the batch_id and list of created jobs.
    """
    db, current_user = user_db
    service = VintedJobService(db)

    if not request.product_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="product_ids cannot be empty",
        )

    try:
        batch_id, jobs = service.create_batch_jobs(
            action_code=request.action_code,
            product_ids=request.product_ids,
            priority=request.priority,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    job_responses = [build_job_response(job, service, db, include_progress=False) for job in jobs]

    return BatchCreateResponse(
        batch_id=batch_id,
        jobs_created=len(jobs),
        jobs=job_responses,
    )


@router.post("/{job_id}/pause", response_model=JobActionResponse)
async def pause_job(
    job_id: int,
    user_db: tuple = Depends(get_user_db),
):
    """
    Pause a running or pending job.

    The job can be resumed later with POST /{job_id}/resume.
    """
    db, current_user = user_db
    service = VintedJobService(db)

    job = service.pause_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot pause job {job_id} (not found or not pausable)",
        )

    return JobActionResponse(
        success=True,
        job_id=job_id,
        new_status=job.status.value,
        message=f"Job {job_id} paused",
    )


@router.post("/{job_id}/resume", response_model=JobActionResponse)
async def resume_job(
    job_id: int,
    user_db: tuple = Depends(get_user_db),
):
    """
    Resume a paused job.

    The job will be added back to the processing queue.
    """
    db, current_user = user_db
    service = VintedJobService(db)

    job = service.resume_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot resume job {job_id} (not found or not paused)",
        )

    return JobActionResponse(
        success=True,
        job_id=job_id,
        new_status=job.status.value,
        message=f"Job {job_id} resumed",
    )


@router.post("/{job_id}/cancel", response_model=JobActionResponse)
async def cancel_job(
    job_id: int,
    user_db: tuple = Depends(get_user_db),
):
    """
    Cancel a job.

    This will also cancel all pending tasks associated with the job.
    """
    db, current_user = user_db
    service = VintedJobService(db)

    job = service.cancel_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel job {job_id} (not found or already terminal)",
        )

    return JobActionResponse(
        success=True,
        job_id=job_id,
        new_status=job.status.value,
        message=f"Job {job_id} cancelled",
    )


@router.post("/batch/{batch_id}/cancel", response_model=dict)
async def cancel_batch(
    batch_id: str,
    user_db: tuple = Depends(get_user_db),
):
    """
    Cancel all jobs in a batch.

    Returns the number of jobs cancelled.
    """
    db, current_user = user_db
    service = VintedJobService(db)

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


@router.post("/batch/{batch_id}/resume", response_model=dict)
async def resume_batch(
    batch_id: str,
    user_db: tuple = Depends(get_user_db),
):
    """
    Resume all paused jobs in a batch.

    Returns the number of jobs resumed.
    """
    db, current_user = user_db
    service = VintedJobService(db)

    jobs = service.get_batch_jobs(batch_id)
    if not jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch not found: {batch_id}",
        )

    resumed_count = 0
    for job in jobs:
        if service.resume_job(job.id):
            resumed_count += 1

    return {
        "success": True,
        "batch_id": batch_id,
        "resumed_count": resumed_count,
        "total_jobs": len(jobs),
        "message": f"Resumed {resumed_count}/{len(jobs)} jobs in batch",
    }


# =============================================================================
# PROCESSING ENDPOINTS
# =============================================================================


@router.post("/process/next", response_model=dict)
async def process_next_job(
    user_db: tuple = Depends(get_user_db),
):
    """
    Process the next pending job in the queue.

    Gets the highest priority pending job and executes it.
    Returns None if no pending jobs.
    """
    db, current_user = user_db

    try:
        connection = get_active_vinted_connection(db, current_user.id)
        processor = VintedJobProcessor(db, shop_id=connection.vinted_user_id)
        result = await processor.process_next_job()

        if result is None:
            return {"success": True, "message": "No pending jobs", "result": None}

        return {"success": True, "result": result}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing job: {str(e)}",
        )


@router.post("/process/all", response_model=dict)
async def process_all_pending_jobs(
    user_db: tuple = Depends(get_user_db),
    max_jobs: int = Query(10, ge=1, le=100, description="Maximum jobs to process"),
    stop_on_error: bool = Query(False, description="Stop on first error"),
):
    """
    Process all pending jobs in priority order.

    Args:
        max_jobs: Maximum number of jobs to process (default: 10, max: 100)
        stop_on_error: If True, stop processing on first error

    Returns:
        List of job results with summary.
    """
    db, current_user = user_db

    try:
        connection = get_active_vinted_connection(db, current_user.id)
        processor = VintedJobProcessor(db, shop_id=connection.vinted_user_id)
        results = await processor.process_all_pending_jobs(
            max_jobs=max_jobs,
            stop_on_error=stop_on_error
        )

        success_count = sum(1 for r in results if r.get("success"))
        failed_count = len(results) - success_count

        return {
            "success": True,
            "processed_count": len(results),
            "success_count": success_count,
            "failed_count": failed_count,
            "results": results,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing jobs: {str(e)}",
        )


@router.post("/process/{job_id}", response_model=dict)
async def process_single_job(
    job_id: int,
    user_db: tuple = Depends(get_user_db),
):
    """
    Process a specific job by ID.

    The job must be in PENDING status to be processed.
    """
    db, current_user = user_db
    service = VintedJobService(db)

    job = service.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {job_id}",
        )

    if job.status != JobStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job {job_id} is not pending (status: {job.status.value})",
        )

    try:
        connection = get_active_vinted_connection(db, current_user.id)
        processor = VintedJobProcessor(db, shop_id=connection.vinted_user_id)
        result = await processor._execute_job(job)

        return {"success": True, "result": result}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing job: {str(e)}",
        )


@router.get("/queue/status", response_model=dict)
async def get_queue_status(
    user_db: tuple = Depends(get_user_db),
):
    """
    Get current job queue status.

    Returns pending job counts by action type and next job info.
    """
    db, current_user = user_db

    try:
        connection = get_active_vinted_connection(db, current_user.id)
        processor = VintedJobProcessor(db, shop_id=connection.vinted_user_id)
        queue_status = processor.get_queue_status()

        return {"success": True, **queue_status}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting queue status: {str(e)}",
        )
