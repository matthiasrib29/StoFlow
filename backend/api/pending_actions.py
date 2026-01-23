"""
Pending Actions API Routes

Endpoints for managing pending actions (confirmation queue).
Users must confirm or reject actions detected by sync workflows.

Endpoints:
- GET /api/pending-actions: List pending actions
- GET /api/pending-actions/count: Get pending count (for badge)
- POST /api/pending-actions/{id}/confirm: Confirm an action
- POST /api/pending-actions/{id}/reject: Reject (restore) an action
- POST /api/pending-actions/bulk-confirm: Bulk confirm
- POST /api/pending-actions/bulk-reject: Bulk reject

Author: Claude
Date: 2026-01-22
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from api.dependencies import get_user_db
from models.public.user import User
from services.pending_action_service import PendingActionService

router = APIRouter(prefix="/pending-actions", tags=["Pending Actions"])


# =============================================================================
# SCHEMAS
# =============================================================================


class PendingActionProductResponse(BaseModel):
    """Minimal product info for pending action list."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    price: float
    brand: str | None = None
    status: str


class PendingActionResponse(BaseModel):
    """Response schema for a pending action."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    action_type: str
    marketplace: str
    reason: str | None = None
    context_data: dict[str, Any] | None = None
    previous_status: str | None = None
    detected_at: datetime
    confirmed_at: datetime | None = None
    confirmed_by: str | None = None
    is_confirmed: bool | None = None
    product: PendingActionProductResponse | None = None


class PendingActionCountResponse(BaseModel):
    """Response schema for pending action count."""
    count: int


class BulkActionRequest(BaseModel):
    """Request schema for bulk confirm/reject."""
    action_ids: list[int] = Field(..., min_length=1, max_length=500)


class BulkActionResponse(BaseModel):
    """Response schema for bulk operations."""
    processed: int
    total: int


class ActionResultResponse(BaseModel):
    """Response schema for single confirm/reject."""
    success: bool
    product_id: int
    new_status: str


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.get("", response_model=list[PendingActionResponse])
def list_pending_actions(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user_db: tuple = Depends(get_user_db),
):
    """List pending actions awaiting user confirmation."""
    db, user = user_db
    service = PendingActionService(db)
    actions = service.get_pending_actions(limit=limit, offset=offset)
    return actions


@router.get("/count", response_model=PendingActionCountResponse)
def get_pending_count(
    user_db: tuple = Depends(get_user_db),
):
    """Get the number of pending actions (for badge display)."""
    db, user = user_db
    service = PendingActionService(db)
    count = service.get_pending_count()
    return PendingActionCountResponse(count=count)


@router.post("/{action_id}/confirm", response_model=ActionResultResponse)
def confirm_action(
    action_id: int,
    user_db: tuple = Depends(get_user_db),
):
    """Confirm a pending action (apply the status change)."""
    db, user = user_db
    service = PendingActionService(db)
    product = service.confirm_action(action_id, confirmed_by=str(user.id))

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pending action {action_id} not found or already processed"
        )

    db.commit()
    return ActionResultResponse(
        success=True,
        product_id=product.id,
        new_status=product.status.value,
    )


@router.post("/{action_id}/reject", response_model=ActionResultResponse)
def reject_action(
    action_id: int,
    user_db: tuple = Depends(get_user_db),
):
    """Reject a pending action (restore product to previous status)."""
    db, user = user_db
    service = PendingActionService(db)
    product = service.reject_action(action_id, restored_by=str(user.id))

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pending action {action_id} not found or already processed"
        )

    db.commit()
    return ActionResultResponse(
        success=True,
        product_id=product.id,
        new_status=product.status.value,
    )


@router.post("/bulk-confirm", response_model=BulkActionResponse)
def bulk_confirm_actions(
    request: BulkActionRequest,
    user_db: tuple = Depends(get_user_db),
):
    """Confirm multiple pending actions at once."""
    db, user = user_db
    service = PendingActionService(db)
    processed = service.bulk_confirm(request.action_ids, confirmed_by=str(user.id))
    db.commit()
    return BulkActionResponse(processed=processed, total=len(request.action_ids))


@router.post("/bulk-reject", response_model=BulkActionResponse)
def bulk_reject_actions(
    request: BulkActionRequest,
    user_db: tuple = Depends(get_user_db),
):
    """Reject multiple pending actions at once (restore products)."""
    db, user = user_db
    service = PendingActionService(db)
    processed = service.bulk_reject(request.action_ids, restored_by=str(user.id))
    db.commit()
    return BulkActionResponse(processed=processed, total=len(request.action_ids))
