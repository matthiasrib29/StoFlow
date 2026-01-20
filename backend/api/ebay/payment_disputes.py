"""
API Routes eBay Payment Disputes.

Endpoints for eBay payment dispute management:
- Synchronization from eBay Fulfillment API
- List with pagination and filters
- Dispute details
- Accept/Contest disputes
- Add evidence
- Statistics and urgent alerts

Author: Claude
Date: 2026-01-14
Refactored: 2026-01-20
"""

from typing import Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.dependencies import get_user_db
from api.dependencies.ebay_dependencies import get_payment_dispute_service
from models.public.user import User
from schemas.ebay_payment_dispute_schemas import (
    AcceptDisputeRequest,
    AddEvidenceRequest,
    AddEvidenceResponse,
    ContestDisputeRequest,
    DisputeActionResponse,
    DisputeListResponse,
    DisputeStatisticsResponse,
    EbayPaymentDisputeResponse,
    SyncDisputesRequest,
    SyncDisputesResponse,
    UrgentDisputeResponse,
)
from services.ebay.ebay_payment_dispute_service import EbayPaymentDisputeService
from shared.logging import get_logger
from shared.route_utils import handle_service_errors, handle_service_errors_sync

logger = get_logger(__name__)
router = APIRouter(prefix="/ebay", tags=["eBay Payment Disputes"])


# =============================================================================
# SYNC ENDPOINTS
# =============================================================================


@router.post("/payment-disputes/sync", response_model=SyncDisputesResponse)
@handle_service_errors
async def sync_disputes(
    request: SyncDisputesRequest = None,
    service: EbayPaymentDisputeService = Depends(get_payment_dispute_service),
):
    """Synchronize payment disputes from eBay API to local database."""
    if request is None:
        request = SyncDisputesRequest()

    stats = service.sync_disputes(days_back=request.days_back)
    logger.info(
        f"[sync_disputes] fetched={stats['total_fetched']}, "
        f"created={stats['created']}, updated={stats['updated']}"
    )
    return SyncDisputesResponse(**stats)


@router.post(
    "/payment-disputes/sync/{payment_dispute_id}",
    response_model=EbayPaymentDisputeResponse,
)
@handle_service_errors
async def sync_single_dispute(
    payment_dispute_id: str,
    service: EbayPaymentDisputeService = Depends(get_payment_dispute_service),
):
    """Synchronize a single payment dispute from eBay API."""
    dispute = service.sync_dispute(payment_dispute_id)
    if not dispute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dispute {payment_dispute_id} not found",
        )
    return EbayPaymentDisputeResponse.model_validate(dispute)


# =============================================================================
# LIST & GET ENDPOINTS
# =============================================================================


@router.get("/payment-disputes", response_model=DisputeListResponse)
@handle_service_errors_sync
def list_disputes(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    state: Optional[str] = Query(
        None,
        pattern="^(OPEN|ACTION_NEEDED|CLOSED)$",
        description="Filter by dispute state",
    ),
    reason: Optional[str] = Query(None, description="Filter by dispute reason"),
    order_id: Optional[str] = Query(None, description="Filter by eBay order ID"),
    service: EbayPaymentDisputeService = Depends(get_payment_dispute_service),
):
    """List eBay payment disputes with pagination and filters."""
    result = service.list_disputes(
        page=page,
        page_size=page_size,
        state=state,
        reason=reason,
        order_id=order_id,
    )
    items = [EbayPaymentDisputeResponse.model_validate(d) for d in result["items"]]
    return DisputeListResponse(
        items=items,
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        total_pages=result["total_pages"],
    )


@router.get("/payment-disputes/statistics", response_model=DisputeStatisticsResponse)
@handle_service_errors_sync
def get_dispute_statistics(
    service: EbayPaymentDisputeService = Depends(get_payment_dispute_service),
):
    """Get payment dispute statistics."""
    stats = service.get_statistics()
    return DisputeStatisticsResponse(
        open=stats["open"],
        action_needed=stats["action_needed"],
        closed=stats["closed"],
        past_deadline=stats["past_deadline"],
        total_amount=stats["total_amount"],
        by_reason=stats["by_reason"],
    )


@router.get("/payment-disputes/urgent", response_model=UrgentDisputeResponse)
@handle_service_errors_sync
def list_urgent_disputes(
    days_threshold: int = Query(
        3, ge=1, le=14, description="Days until deadline to consider urgent"
    ),
    service: EbayPaymentDisputeService = Depends(get_payment_dispute_service),
):
    """List urgent disputes requiring immediate attention."""
    disputes = service.get_urgent_disputes(days_threshold=days_threshold)
    items = [EbayPaymentDisputeResponse.model_validate(d) for d in disputes]
    return UrgentDisputeResponse(disputes=items, count=len(items))


@router.get("/payment-disputes/action-needed", response_model=DisputeListResponse)
@handle_service_errors_sync
def list_action_needed_disputes(
    limit: int = Query(100, ge=1, le=200, description="Max results"),
    service: EbayPaymentDisputeService = Depends(get_payment_dispute_service),
):
    """List disputes requiring seller action."""
    disputes = service.get_action_needed_disputes(limit=limit)
    items = [EbayPaymentDisputeResponse.model_validate(d) for d in disputes]
    return DisputeListResponse(
        items=items,
        total=len(items),
        page=1,
        page_size=limit,
        total_pages=1,
    )


@router.get("/payment-disputes/open", response_model=DisputeListResponse)
@handle_service_errors_sync
def list_open_disputes(
    limit: int = Query(100, ge=1, le=200, description="Max results"),
    service: EbayPaymentDisputeService = Depends(get_payment_dispute_service),
):
    """List open disputes (OPEN or ACTION_NEEDED)."""
    disputes = service.get_open_disputes(limit=limit)
    items = [EbayPaymentDisputeResponse.model_validate(d) for d in disputes]
    return DisputeListResponse(
        items=items,
        total=len(items),
        page=1,
        page_size=limit,
        total_pages=1,
    )


@router.get(
    "/payment-disputes/{payment_dispute_id}",
    response_model=EbayPaymentDisputeResponse,
)
@handle_service_errors_sync
def get_dispute(
    payment_dispute_id: str,
    service: EbayPaymentDisputeService = Depends(get_payment_dispute_service),
):
    """Get detailed information about a specific payment dispute."""
    dispute = service.get_dispute(payment_dispute_id)
    if not dispute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dispute {payment_dispute_id} not found",
        )
    return EbayPaymentDisputeResponse.model_validate(dispute)


# =============================================================================
# ACTION ENDPOINTS
# =============================================================================


@router.post(
    "/payment-disputes/{payment_dispute_id}/accept",
    response_model=DisputeActionResponse,
)
@handle_service_errors_sync
def accept_dispute(
    payment_dispute_id: str,
    request: AcceptDisputeRequest = None,
    service: EbayPaymentDisputeService = Depends(get_payment_dispute_service),
):
    """
    Accept a payment dispute (concede to buyer).

    Effect: Seller agrees the buyer's claim is valid, refund will be issued.
    """
    return_address = request.return_address if request else None

    result = service.accept_dispute(
        payment_dispute_id=payment_dispute_id,
        return_address=return_address,
    )

    dispute_response = None
    if result.get("dispute"):
        dispute_response = EbayPaymentDisputeResponse.model_validate(result["dispute"])

    return DisputeActionResponse(
        success=result["success"],
        message=result.get("message"),
        dispute=dispute_response,
    )


@router.post(
    "/payment-disputes/{payment_dispute_id}/contest",
    response_model=DisputeActionResponse,
)
@handle_service_errors_sync
def contest_dispute(
    payment_dispute_id: str,
    request: ContestDisputeRequest = None,
    service: EbayPaymentDisputeService = Depends(get_payment_dispute_service),
):
    """
    Contest a payment dispute (fight buyer's claim).

    IMPORTANT: Add evidence BEFORE contesting! Once contested, no more evidence can be added.
    """
    note = request.note if request else None
    return_address = request.return_address if request else None

    result = service.contest_dispute(
        payment_dispute_id=payment_dispute_id,
        note=note,
        return_address=return_address,
    )

    dispute_response = None
    if result.get("dispute"):
        dispute_response = EbayPaymentDisputeResponse.model_validate(result["dispute"])

    return DisputeActionResponse(
        success=result["success"],
        message=result.get("message"),
        dispute=dispute_response,
    )


@router.post(
    "/payment-disputes/{payment_dispute_id}/add-evidence",
    response_model=AddEvidenceResponse,
)
@handle_service_errors_sync
def add_evidence(
    payment_dispute_id: str,
    request: AddEvidenceRequest,
    service: EbayPaymentDisputeService = Depends(get_payment_dispute_service),
):
    """
    Add evidence to a payment dispute.

    IMPORTANT: Evidence must be added BEFORE contesting!
    Once the dispute is contested, no more evidence can be added.
    """
    files = None
    if request.files:
        files = [
            {"fileId": f.file_id, "contentType": f.content_type}
            for f in request.files
        ]

    result = service.add_evidence(
        payment_dispute_id=payment_dispute_id,
        evidence_type=request.evidence_type,
        files=files,
        line_items=request.line_items,
    )

    return AddEvidenceResponse(**result)
