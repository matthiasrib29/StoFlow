"""
API Routes eBay Refunds.

Endpoints for eBay refund management with local DB synchronization.

Features:
- Synchronization from eBay order payment summaries
- List with pagination and filters
- Refund details
- Issue new refunds via Fulfillment API
- Statistics

Note: eBay doesn't have a dedicated refund search API. Refunds are
extracted from order payment summaries via the Fulfillment API.

Author: Claude
Date: 2026-01-14
Refactored: 2026-01-20
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.dependencies.ebay_dependencies import get_refund_service
from schemas.ebay_refund_schemas import (
    EbayRefundResponse,
    IssueRefundRequest,
    IssueRefundResponse,
    RefundListResponse,
    RefundStatisticsResponse,
    SyncRefundsFromOrderRequest,
    SyncRefundsRequest,
    SyncRefundsResponse,
)
from services.ebay.ebay_refund_service import EbayRefundService
from shared.logging import get_logger
from shared.route_utils import handle_service_errors, handle_service_errors_sync

logger = get_logger(__name__)
router = APIRouter(prefix="/ebay", tags=["eBay Refunds"])


# =============================================================================
# SYNC ENDPOINTS
# =============================================================================


@router.post("/refunds/sync", response_model=SyncRefundsResponse)
@handle_service_errors
async def sync_refunds(
    request: SyncRefundsRequest = None,
    service: EbayRefundService = Depends(get_refund_service),
):
    """Synchronize refunds from eBay orders to local database."""
    if request is None:
        request = SyncRefundsRequest()

    stats = service.sync_refunds_from_recent_orders(days_back=request.days_back)
    logger.info(
        f"[sync_refunds] created={stats['created']}, updated={stats['updated']}, "
        f"skipped={stats['skipped']}"
    )
    return SyncRefundsResponse(**stats)


@router.post("/refunds/sync-order", response_model=SyncRefundsResponse)
@handle_service_errors
async def sync_refunds_from_order(
    request: SyncRefundsFromOrderRequest,
    service: EbayRefundService = Depends(get_refund_service),
):
    """Synchronize refunds from a specific eBay order."""
    stats = service.sync_refunds_from_order(order_id=request.order_id)
    logger.info(
        f"[sync_refunds_from_order] order={request.order_id}, "
        f"created={stats['created']}, updated={stats['updated']}"
    )
    return SyncRefundsResponse(**stats)


# =============================================================================
# LIST & GET ENDPOINTS
# =============================================================================


@router.get("/refunds", response_model=RefundListResponse)
@handle_service_errors_sync
def list_refunds(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    status_filter: Optional[str] = Query(
        None,
        alias="status",
        pattern="^(PENDING|REFUNDED|FAILED)$",
        description="Filter by refund status",
    ),
    source: Optional[str] = Query(
        None,
        pattern="^(RETURN|CANCELLATION|MANUAL|OTHER)$",
        description="Filter by refund source",
    ),
    order_id: Optional[str] = Query(None, description="Filter by eBay order ID"),
    service: EbayRefundService = Depends(get_refund_service),
):
    """List eBay refunds with pagination and filters."""
    result = service.list_refunds(
        page=page,
        page_size=page_size,
        status=status_filter,
        source=source,
        order_id=order_id,
    )
    items = [EbayRefundResponse.model_validate(r) for r in result["items"]]

    return RefundListResponse(
        items=items,
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        total_pages=result["total_pages"],
    )


@router.get("/refunds/statistics", response_model=RefundStatisticsResponse)
@handle_service_errors_sync
def get_refund_statistics(
    service: EbayRefundService = Depends(get_refund_service),
):
    """Get refund statistics."""
    stats = service.get_statistics()
    return RefundStatisticsResponse(
        pending=stats["pending"],
        completed=stats["completed"],
        failed=stats["failed"],
        total_refunded=stats["total_refunded"],
        by_source=stats["by_source"],
    )


@router.get("/refunds/pending", response_model=RefundListResponse)
@handle_service_errors_sync
def list_pending_refunds(
    limit: int = Query(100, ge=1, le=200, description="Max results"),
    service: EbayRefundService = Depends(get_refund_service),
):
    """List pending refunds."""
    refunds = service.list_pending_refunds(limit=limit)
    items = [EbayRefundResponse.model_validate(r) for r in refunds]
    return RefundListResponse(
        items=items,
        total=len(items),
        page=1,
        page_size=limit,
        total_pages=1,
    )


@router.get("/refunds/failed", response_model=RefundListResponse)
@handle_service_errors_sync
def list_failed_refunds(
    limit: int = Query(100, ge=1, le=200, description="Max results"),
    service: EbayRefundService = Depends(get_refund_service),
):
    """List failed refunds."""
    refunds = service.list_failed_refunds(limit=limit)
    items = [EbayRefundResponse.model_validate(r) for r in refunds]
    return RefundListResponse(
        items=items,
        total=len(items),
        page=1,
        page_size=limit,
        total_pages=1,
    )


@router.get("/refunds/{refund_id}", response_model=EbayRefundResponse)
@handle_service_errors_sync
def get_refund(
    refund_id: int,
    service: EbayRefundService = Depends(get_refund_service),
):
    """Get detailed information about a specific refund."""
    refund = service.get_refund_by_id(refund_id)
    if not refund:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Refund {refund_id} not found",
        )
    return EbayRefundResponse.model_validate(refund)


# =============================================================================
# ACTION ENDPOINTS
# =============================================================================


@router.post("/refunds/issue", response_model=IssueRefundResponse)
@handle_service_errors_sync
def issue_refund(
    request: IssueRefundRequest,
    service: EbayRefundService = Depends(get_refund_service),
):
    """Issue a new refund for an eBay order."""
    result = service.issue_refund(
        order_id=request.order_id,
        reason=request.reason,
        amount=request.amount,
        currency=request.currency,
        line_item_id=request.line_item_id,
        comment=request.comment,
    )
    return IssueRefundResponse(**result)
