"""
API Routes eBay Returns.

Endpoints for eBay returns management with local DB synchronization.

Features:
- Synchronization from eBay Post-Order API
- List with pagination and filters
- Return details
- Actions: accept, decline, refund, mark received, send message
- Statistics

Author: Claude
Date: 2026-01-13
Refactored: 2026-01-20
"""

from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from api.dependencies.ebay_dependencies import get_return_service, get_db_and_user
from schemas.ebay_return_schemas import (
    AcceptReturnRequest,
    DeclineReturnRequest,
    EbayReturnResponse,
    IssueRefundRequest,
    MarkAsReceivedRequest,
    ReturnActionResponse,
    ReturnListResponse,
    ReturnStatisticsResponse,
    SendMessageRequest,
    SyncReturnsRequest,
    SyncReturnsResponse,
)
from services.ebay.ebay_return_service import EbayReturnService
from services.ebay.ebay_return_sync_service import EbayReturnSyncService
from shared.logging import get_logger
from shared.route_utils import handle_service_errors, handle_service_errors_sync

logger = get_logger(__name__)
router = APIRouter(prefix="/ebay", tags=["eBay Returns"])


# =============================================================================
# SYNC ENDPOINT
# =============================================================================


@router.post("/returns/sync", response_model=SyncReturnsResponse)
@handle_service_errors
async def sync_returns(
    request: SyncReturnsRequest = Body(default=SyncReturnsRequest()),
    db_and_user=Depends(get_db_and_user),
):
    """Synchronize returns from eBay Post-Order API to local database."""
    db, current_user = db_and_user
    sync_service = EbayReturnSyncService(db, current_user.id)

    stats = sync_service.sync_returns(
        return_state=request.return_state,
        days_back=request.days_back,
    )
    logger.info(
        f"[sync_returns] created={stats['created']}, updated={stats['updated']}"
    )
    return SyncReturnsResponse(**stats)


# =============================================================================
# LIST & GET ENDPOINTS
# =============================================================================


@router.get("/returns", response_model=ReturnListResponse)
@handle_service_errors_sync
def list_returns(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    state: Optional[str] = Query(
        None,
        pattern="^(OPEN|CLOSED)$",
        description="Filter by state (OPEN, CLOSED)",
    ),
    status_filter: Optional[str] = Query(
        None,
        alias="status",
        description="Filter by status (RETURN_REQUESTED, etc.)",
    ),
    order_id: Optional[str] = Query(None, description="Filter by eBay order ID"),
    service: EbayReturnService = Depends(get_return_service),
):
    """List eBay returns with pagination and filters."""
    skip = (page - 1) * page_size
    returns, total = service.list_returns(
        skip=skip,
        limit=page_size,
        state=state,
        status=status_filter,
        order_id=order_id,
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    items = [EbayReturnResponse.model_validate(r) for r in returns]

    return ReturnListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/returns/statistics", response_model=ReturnStatisticsResponse)
@handle_service_errors_sync
def get_return_statistics(
    service: EbayReturnService = Depends(get_return_service),
):
    """Get return statistics."""
    stats = service.get_return_statistics()
    return ReturnStatisticsResponse(**stats)


@router.get("/returns/needs-action", response_model=ReturnListResponse)
@handle_service_errors_sync
def list_returns_needing_action(
    limit: int = Query(100, ge=1, le=200, description="Max results"),
    service: EbayReturnService = Depends(get_return_service),
):
    """List returns requiring seller action."""
    returns = service.get_returns_needing_action(limit=limit)
    items = [EbayReturnResponse.model_validate(r) for r in returns]
    return ReturnListResponse(
        items=items,
        total=len(items),
        page=1,
        page_size=limit,
        total_pages=1,
    )


@router.get("/returns/past-deadline", response_model=ReturnListResponse)
@handle_service_errors_sync
def list_returns_past_deadline(
    limit: int = Query(100, ge=1, le=200, description="Max results"),
    service: EbayReturnService = Depends(get_return_service),
):
    """List returns past their deadline (urgent)."""
    returns = service.get_returns_past_deadline(limit=limit)
    items = [EbayReturnResponse.model_validate(r) for r in returns]
    return ReturnListResponse(
        items=items,
        total=len(items),
        page=1,
        page_size=limit,
        total_pages=1,
    )


@router.get("/returns/{return_id}", response_model=EbayReturnResponse)
@handle_service_errors_sync
def get_return(
    return_id: int,
    service: EbayReturnService = Depends(get_return_service),
):
    """Get detailed information about a specific return."""
    return_obj = service.get_return(return_id)
    if not return_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Return {return_id} not found",
        )
    return EbayReturnResponse.model_validate(return_obj)


# =============================================================================
# ACTION ENDPOINTS
# =============================================================================


@router.post("/returns/{return_id}/accept", response_model=ReturnActionResponse)
@handle_service_errors_sync
def accept_return(
    return_id: int,
    request: AcceptReturnRequest = Body(default=AcceptReturnRequest()),
    service: EbayReturnService = Depends(get_return_service),
):
    """Accept a return request."""
    result = service.accept_return(
        return_id=return_id,
        comments=request.comments,
        rma_number=request.rma_number,
    )
    return ReturnActionResponse(**result)


@router.post("/returns/{return_id}/decline", response_model=ReturnActionResponse)
@handle_service_errors_sync
def decline_return(
    return_id: int,
    request: DeclineReturnRequest,
    service: EbayReturnService = Depends(get_return_service),
):
    """Decline a return request. Warning: May impact seller metrics."""
    result = service.decline_return(
        return_id=return_id,
        comments=request.comments,
    )
    return ReturnActionResponse(**result)


@router.post("/returns/{return_id}/refund", response_model=ReturnActionResponse)
@handle_service_errors_sync
def issue_refund(
    return_id: int,
    request: IssueRefundRequest = Body(default=IssueRefundRequest()),
    service: EbayReturnService = Depends(get_return_service),
):
    """Issue refund for a return. Omit amount for full refund."""
    result = service.issue_refund(
        return_id=return_id,
        refund_amount=request.refund_amount,
        currency=request.currency,
        comments=request.comments,
    )
    return ReturnActionResponse(**result)


@router.post("/returns/{return_id}/received", response_model=ReturnActionResponse)
@handle_service_errors_sync
def mark_as_received(
    return_id: int,
    request: MarkAsReceivedRequest = Body(default=MarkAsReceivedRequest()),
    service: EbayReturnService = Depends(get_return_service),
):
    """Mark return item as received by seller."""
    result = service.mark_as_received(
        return_id=return_id,
        comments=request.comments,
    )
    return ReturnActionResponse(**result)


@router.post("/returns/{return_id}/message", response_model=ReturnActionResponse)
@handle_service_errors_sync
def send_message(
    return_id: int,
    request: SendMessageRequest,
    service: EbayReturnService = Depends(get_return_service),
):
    """Send message to buyer about return."""
    result = service.send_message(
        return_id=return_id,
        message=request.message,
    )
    return ReturnActionResponse(**result)
