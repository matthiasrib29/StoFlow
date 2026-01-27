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
from models.user.pending_action import PendingAction, PendingActionType
from services.pending_action_service import PendingActionService
from shared.logging import get_logger
from temporal.config import get_temporal_config

logger = get_logger(__name__)

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
    image_url: str | None = None


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
# HELPERS
# =============================================================================


async def _trigger_cleanup_workflow(db: Session, action: PendingAction, user_id: int) -> None:
    """
    Start cleanup workflow for a SINGLE confirmed action.

    Used by the single-confirm endpoint.
    Fire-and-forget: logs a warning on failure but never raises.
    """
    config = get_temporal_config()
    if not config.temporal_enabled:
        return

    if action.action_type == PendingActionType.DELETE_VINTED_LISTING:
        try:
            from temporal.client import get_temporal_client
            from temporal.workflows.vinted.cleanup_workflow import (
                VintedCleanupWorkflow,
                VintedCleanupParams,
            )

            client = await get_temporal_client()
            await client.start_workflow(
                VintedCleanupWorkflow.run,
                VintedCleanupParams(user_id=user_id, product_id=action.product_id),
                id=f"vinted-cleanup-product-{action.product_id}",
                task_queue=config.temporal_vinted_task_queue,
            )
            logger.info(f"Started Vinted cleanup workflow for product #{action.product_id}")
        except Exception as e:
            logger.warning(f"Failed to start Vinted cleanup for product #{action.product_id}: {e}")

    elif action.action_type == PendingActionType.DELETE_EBAY_LISTING:
        try:
            from temporal.client import get_temporal_client
            from temporal.workflows.ebay.cleanup_workflow import (
                EbayCleanupWorkflow,
                EbayCleanupParams,
            )

            client = await get_temporal_client()
            await client.start_workflow(
                EbayCleanupWorkflow.run,
                EbayCleanupParams(user_id=user_id, product_id=action.product_id),
                id=f"ebay-cleanup-product-{action.product_id}",
                task_queue=config.temporal_task_queue,
            )
            logger.info(f"Started eBay cleanup workflow for product #{action.product_id}")
        except Exception as e:
            logger.warning(f"Failed to start eBay cleanup for product #{action.product_id}: {e}")


async def _trigger_batch_cleanup_workflows(actions: list[PendingAction], user_id: int) -> None:
    """
    Start cleanup workflows for MULTIPLE confirmed actions.

    Groups by marketplace:
    - Vinted → ONE VintedBatchCleanupWorkflow (sequential, no parallel plugin calls)
    - eBay → Individual EbayCleanupWorkflow per product (direct API, parallel OK)

    Fire-and-forget: logs warnings on failure but never raises.
    """
    config = get_temporal_config()
    if not config.temporal_enabled or not actions:
        return

    # Group by type
    vinted_product_ids = [
        a.product_id for a in actions
        if a.action_type == PendingActionType.DELETE_VINTED_LISTING
    ]
    ebay_product_ids = [
        a.product_id for a in actions
        if a.action_type == PendingActionType.DELETE_EBAY_LISTING
    ]

    # Vinted: ONE batch workflow (sequential execution)
    if vinted_product_ids:
        try:
            from temporal.client import get_temporal_client
            from temporal.workflows.vinted.cleanup_workflow import (
                VintedBatchCleanupWorkflow,
                VintedBatchCleanupParams,
            )

            client = await get_temporal_client()
            await client.start_workflow(
                VintedBatchCleanupWorkflow.run,
                VintedBatchCleanupParams(user_id=user_id, product_ids=vinted_product_ids),
                id=f"vinted-batch-cleanup-user-{user_id}-{len(vinted_product_ids)}p",
                task_queue=config.temporal_vinted_task_queue,
            )
            logger.info(
                f"Started Vinted batch cleanup workflow for {len(vinted_product_ids)} products"
            )
        except Exception as e:
            logger.warning(f"Failed to start Vinted batch cleanup: {e}")

    # eBay: individual workflows (direct API, parallel OK)
    if ebay_product_ids:
        try:
            from temporal.client import get_temporal_client
            from temporal.workflows.ebay.cleanup_workflow import (
                EbayCleanupWorkflow,
                EbayCleanupParams,
            )

            client = await get_temporal_client()
            for product_id in ebay_product_ids:
                try:
                    await client.start_workflow(
                        EbayCleanupWorkflow.run,
                        EbayCleanupParams(user_id=user_id, product_id=product_id),
                        id=f"ebay-cleanup-product-{product_id}",
                        task_queue=config.temporal_task_queue,
                    )
                except Exception as e:
                    logger.warning(f"Failed to start eBay cleanup for product #{product_id}: {e}")

            logger.info(f"Started eBay cleanup workflows for {len(ebay_product_ids)} products")
        except Exception as e:
            logger.warning(f"Failed to start eBay cleanup workflows: {e}")


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
async def confirm_action(
    action_id: int,
    user_db: tuple = Depends(get_user_db),
):
    """Confirm a pending action (apply the status change)."""
    db, user = user_db

    # Load action before confirm to check its type
    action = db.get(PendingAction, action_id)

    service = PendingActionService(db)
    product = service.confirm_action(action_id, confirmed_by=str(user.id))

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pending action {action_id} not found or already processed"
        )

    db.commit()

    # Trigger marketplace cleanup workflow if applicable (fire-and-forget)
    if action:
        await _trigger_cleanup_workflow(db, action, user.id)

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
async def bulk_confirm_actions(
    request: BulkActionRequest,
    user_db: tuple = Depends(get_user_db),
):
    """Confirm multiple pending actions at once."""
    db, user = user_db

    # Load actions before confirm to check their types
    _CLEANUP_TYPES = {PendingActionType.DELETE_VINTED_LISTING, PendingActionType.DELETE_EBAY_LISTING}
    actions_to_cleanup = []
    for action_id in request.action_ids:
        action = db.get(PendingAction, action_id)
        if action and action.action_type in _CLEANUP_TYPES and action.confirmed_at is None:
            actions_to_cleanup.append(action)

    service = PendingActionService(db)
    processed = service.bulk_confirm(request.action_ids, confirmed_by=str(user.id))
    db.commit()

    # Trigger cleanup: batch for Vinted (sequential), individual for eBay
    await _trigger_batch_cleanup_workflows(actions_to_cleanup, user.id)

    return BulkActionResponse(processed=processed, total=len(request.action_ids))


@router.post("/confirm-all", response_model=BulkActionResponse)
async def confirm_all_actions(
    user_db: tuple = Depends(get_user_db),
):
    """Confirm ALL pending actions at once (no IDs needed)."""
    db, user = user_db
    service = PendingActionService(db)

    # Get all unconfirmed action IDs
    all_actions = service.get_pending_actions(limit=10000, offset=0)
    if not all_actions:
        return BulkActionResponse(processed=0, total=0)

    # Identify cleanup actions before confirming
    _CLEANUP_TYPES = {PendingActionType.DELETE_VINTED_LISTING, PendingActionType.DELETE_EBAY_LISTING}
    actions_to_cleanup = [a for a in all_actions if a.action_type in _CLEANUP_TYPES]

    # Confirm all
    action_ids = [a.id for a in all_actions]
    processed = service.bulk_confirm(action_ids, confirmed_by=str(user.id))
    db.commit()

    # Trigger cleanup: batch for Vinted (sequential), individual for eBay
    await _trigger_batch_cleanup_workflows(actions_to_cleanup, user.id)

    return BulkActionResponse(processed=processed, total=len(action_ids))


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
