"""
Celery Tasks API Routes

Endpoints for managing and monitoring Celery tasks.

Endpoints:
- GET /api/tasks: List tasks for current user
- GET /api/tasks/{task_id}: Get task details
- POST /api/tasks/{task_id}/revoke: Cancel a task
- GET /api/tasks/stats: Get task statistics
- POST /api/tasks/publish: Create a publish task

Author: Claude
Date: 2026-01-20
"""
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from api.dependencies import get_user_db, get_current_user
from models.public.user import User
from models.public.celery_task_record import CeleryTaskRecord
from services.celery.task_tracking_service import TaskTrackingService
from shared.database import get_db

router = APIRouter(prefix="/tasks", tags=["Tasks"])


# =============================================================================
# SCHEMAS
# =============================================================================


class TaskResponse(BaseModel):
    """Response schema for a task."""

    id: str
    name: str
    status: str
    marketplace: Optional[str] = None
    action_code: Optional[str] = None
    product_id: Optional[int] = None
    result: Optional[dict] = None
    error: Optional[str] = None
    retries: int = 0
    max_retries: int = 3
    worker: Optional[str] = None
    queue: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    runtime_seconds: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class TaskListResponse(BaseModel):
    """Response schema for task list."""

    tasks: list[TaskResponse]
    total: int
    limit: int
    offset: int


class TaskStatsResponse(BaseModel):
    """Response schema for task statistics."""

    period_days: int
    by_status: dict[str, int]
    by_marketplace: dict[str, int]
    avg_runtime_seconds: Optional[float]
    total: int


class PublishTaskRequest(BaseModel):
    """Request schema for creating a publish task."""

    product_id: int = Field(..., description="Product ID to publish")
    marketplace: str = Field(..., description="Target marketplace (vinted, ebay, etsy)")
    shop_id: Optional[int] = Field(None, description="Shop ID (required for Vinted)")
    marketplace_id: Optional[str] = Field(
        None, description="Marketplace ID (e.g., EBAY_FR for eBay)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "product_id": 123,
                "marketplace": "vinted",
                "shop_id": 456,
            }
        }
    )


class TaskCreateResponse(BaseModel):
    """Response schema for task creation."""

    task_id: str
    status: str
    message: str


class BatchPublishRequest(BaseModel):
    """Request schema for batch publish."""

    product_ids: list[int] = Field(..., min_length=1, description="Product IDs to publish")
    marketplace: str = Field(..., description="Target marketplace (vinted, ebay, etsy)")
    shop_id: Optional[int] = Field(None, description="Shop ID (required for Vinted)")
    marketplace_id: Optional[str] = Field(
        None, description="Marketplace ID (e.g., EBAY_FR for eBay)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "product_ids": [123, 456, 789],
                "marketplace": "ebay",
                "marketplace_id": "EBAY_FR",
            }
        }
    )


class BatchTaskCreateResponse(BaseModel):
    """Response schema for batch task creation."""

    task_ids: list[str]
    count: int
    status: str
    message: str


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.get("", response_model=TaskListResponse)
def list_tasks(
    status: Optional[str] = Query(None, description="Filter by status"),
    marketplace: Optional[str] = Query(None, description="Filter by marketplace"),
    action_code: Optional[str] = Query(None, description="Filter by action"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List Celery tasks for the current user.

    Returns paginated list of tasks with optional filters.
    """
    service = TaskTrackingService(db)

    tasks = service.get_tasks_for_user(
        user_id=current_user.id,
        status=status,
        marketplace=marketplace,
        action_code=action_code,
        limit=limit,
        offset=offset,
    )

    total = service.get_task_count_for_user(
        user_id=current_user.id,
        status=status,
    )

    return TaskListResponse(
        tasks=[TaskResponse.model_validate(t) for t in tasks],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/stats", response_model=TaskStatsResponse)
def get_task_stats(
    days: int = Query(7, ge=1, le=90, description="Number of days to include"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get task statistics for the current user.

    Returns aggregated statistics for the specified time period.
    """
    service = TaskTrackingService(db)
    stats = service.get_task_stats(user_id=current_user.id, days=days)
    return TaskStatsResponse(**stats)


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get details of a specific task.

    Only returns tasks belonging to the current user.
    """
    service = TaskTrackingService(db)
    task = service.get_task_record(task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )

    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this task",
        )

    return TaskResponse.model_validate(task)


@router.post("/{task_id}/revoke", response_model=TaskCreateResponse)
def revoke_task(
    task_id: str,
    terminate: bool = Query(False, description="Force terminate running task"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Revoke (cancel) a pending or running task.

    Args:
        task_id: Celery task ID to revoke
        terminate: If True, terminates a running task immediately

    Returns:
        Task revocation result
    """
    from celery_app import celery_app

    service = TaskTrackingService(db)
    task = service.get_task_record(task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )

    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this task",
        )

    if task.status in ["SUCCESS", "FAILURE", "REVOKED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot revoke task with status {task.status}",
        )

    # Revoke the task via Celery
    celery_app.control.revoke(task_id, terminate=terminate)

    # Update the record
    service.update_task_revoked(task_id)

    return TaskCreateResponse(
        task_id=task_id,
        status="REVOKED",
        message=f"Task {task_id} has been revoked",
    )


@router.post("/publish", response_model=TaskCreateResponse)
def create_publish_task(
    request: PublishTaskRequest,
    db_user: tuple = Depends(get_user_db),
):
    """
    Create a task to publish a product to a marketplace.

    This queues the product for publication via Celery.
    """
    from tasks.marketplace_tasks import publish_product

    db, current_user = db_user

    # Validate marketplace
    if request.marketplace not in ["vinted", "ebay", "etsy"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid marketplace: {request.marketplace}",
        )

    # Validate shop_id for Vinted
    if request.marketplace == "vinted" and not request.shop_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="shop_id is required for Vinted",
        )

    # Queue the task
    task = publish_product.delay(
        product_id=request.product_id,
        user_id=current_user.id,
        marketplace=request.marketplace,
        shop_id=request.shop_id,
        marketplace_id=request.marketplace_id,
    )

    return TaskCreateResponse(
        task_id=task.id,
        status="PENDING",
        message=f"Publish task queued for product {request.product_id}",
    )


@router.post("/publish/batch", response_model=BatchTaskCreateResponse)
def create_batch_publish_tasks(
    request: BatchPublishRequest,
    db_user: tuple = Depends(get_user_db),
):
    """
    Create multiple publish tasks for a batch of products.

    This queues all products for publication via Celery.
    """
    from tasks.marketplace_tasks import publish_product

    db, current_user = db_user

    # Validate marketplace
    if request.marketplace not in ["vinted", "ebay", "etsy"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid marketplace: {request.marketplace}",
        )

    # Validate shop_id for Vinted
    if request.marketplace == "vinted" and not request.shop_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="shop_id is required for Vinted",
        )

    # Queue all tasks
    task_ids = []
    for product_id in request.product_ids:
        task = publish_product.delay(
            product_id=product_id,
            user_id=current_user.id,
            marketplace=request.marketplace,
            shop_id=request.shop_id,
            marketplace_id=request.marketplace_id,
        )
        task_ids.append(task.id)

    return BatchTaskCreateResponse(
        task_ids=task_ids,
        count=len(task_ids),
        status="PENDING",
        message=f"{len(task_ids)} publish tasks queued for {request.marketplace}",
    )


@router.post("/sync", response_model=TaskCreateResponse)
def create_sync_task(
    marketplace: str = Query(..., description="Marketplace to sync"),
    sync_type: str = Query("inventory", description="Sync type: inventory or orders"),
    shop_id: Optional[int] = Query(None, description="Shop ID for Vinted"),
    db_user: tuple = Depends(get_user_db),
):
    """
    Create a sync task to synchronize inventory or orders from a marketplace.
    """
    from tasks.marketplace_tasks import sync_inventory, sync_orders

    db, current_user = db_user

    # Validate marketplace
    if marketplace not in ["vinted", "ebay", "etsy"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid marketplace: {marketplace}",
        )

    # Validate shop_id for Vinted
    if marketplace == "vinted" and not shop_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="shop_id is required for Vinted",
        )

    # Queue the appropriate task
    if sync_type == "inventory":
        task = sync_inventory.delay(
            user_id=current_user.id,
            marketplace=marketplace,
            shop_id=shop_id,
        )
    elif sync_type == "orders":
        task = sync_orders.delay(
            user_id=current_user.id,
            marketplace=marketplace,
            shop_id=shop_id,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid sync_type: {sync_type}. Must be 'inventory' or 'orders'",
        )

    return TaskCreateResponse(
        task_id=task.id,
        status="PENDING",
        message=f"{sync_type.capitalize()} sync task queued for {marketplace}",
    )
