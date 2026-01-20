"""
API Routes eBay INR Inquiries.

Endpoints for eBay INR (Item Not Received) inquiry management.

Features:
- Synchronization from eBay Post-Order API
- List with pagination and filters
- Inquiry details
- Actions: provide shipment info, refund, send message, escalate
- Statistics

Author: Claude
Date: 2026-01-14
Refactored: 2026-01-20
"""

from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from api.dependencies.ebay_dependencies import get_inquiry_service
from schemas.ebay_inquiry_schemas import (
    EbayInquiryResponse,
    EscalateInquiryRequest,
    InquiryActionResponse,
    InquiryListResponse,
    InquirySendMessageRequest,
    InquiryStatisticsResponse,
    ProvideRefundRequest,
    ProvideShipmentInfoRequest,
    SyncInquiriesRequest,
    SyncInquiriesResponse,
)
from services.ebay.ebay_inquiry_service import EbayInquiryService
from shared.logging import get_logger
from shared.route_utils import handle_service_errors, handle_service_errors_sync

logger = get_logger(__name__)
router = APIRouter(prefix="/ebay", tags=["eBay Inquiries"])


# =============================================================================
# SYNC ENDPOINT
# =============================================================================


@router.post("/inquiries/sync", response_model=SyncInquiriesResponse)
@handle_service_errors
async def sync_inquiries(
    request: SyncInquiriesRequest = Body(default=SyncInquiriesRequest()),
    service: EbayInquiryService = Depends(get_inquiry_service),
):
    """Synchronize INR inquiries from eBay Post-Order API to local database."""
    stats = service.sync_inquiries(state=request.inquiry_state)
    logger.info(
        f"[sync_inquiries] created={stats['created']}, updated={stats['updated']}"
    )
    return SyncInquiriesResponse(**stats)


# =============================================================================
# LIST & GET ENDPOINTS
# =============================================================================


@router.get("/inquiries", response_model=InquiryListResponse)
@handle_service_errors_sync
def list_inquiries(
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
        description="Filter by status (INR_WAITING_FOR_SELLER, etc.)",
    ),
    order_id: Optional[str] = Query(None, description="Filter by eBay order ID"),
    service: EbayInquiryService = Depends(get_inquiry_service),
):
    """List eBay INR inquiries with pagination and filters."""
    skip = (page - 1) * page_size
    inquiries, total = service.list_inquiries(
        skip=skip,
        limit=page_size,
        state=state,
        status=status_filter,
        order_id=order_id,
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    items = [EbayInquiryResponse.model_validate(i) for i in inquiries]

    return InquiryListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/inquiries/statistics", response_model=InquiryStatisticsResponse)
@handle_service_errors_sync
def get_inquiry_statistics(
    service: EbayInquiryService = Depends(get_inquiry_service),
):
    """Get inquiry statistics."""
    stats = service.get_inquiry_statistics()
    return InquiryStatisticsResponse(**stats)


@router.get("/inquiries/needs-action", response_model=InquiryListResponse)
@handle_service_errors_sync
def list_inquiries_needing_action(
    limit: int = Query(100, ge=1, le=200, description="Max results"),
    service: EbayInquiryService = Depends(get_inquiry_service),
):
    """List INR inquiries requiring seller action."""
    inquiries = service.get_inquiries_needing_action(limit=limit)
    items = [EbayInquiryResponse.model_validate(i) for i in inquiries]
    return InquiryListResponse(
        items=items,
        total=len(items),
        page=1,
        page_size=limit,
        total_pages=1,
    )


@router.get("/inquiries/past-deadline", response_model=InquiryListResponse)
@handle_service_errors_sync
def list_inquiries_past_deadline(
    limit: int = Query(100, ge=1, le=200, description="Max results"),
    service: EbayInquiryService = Depends(get_inquiry_service),
):
    """List INR inquiries past their response deadline (urgent)."""
    inquiries = service.get_inquiries_past_deadline(limit=limit)
    items = [EbayInquiryResponse.model_validate(i) for i in inquiries]
    return InquiryListResponse(
        items=items,
        total=len(items),
        page=1,
        page_size=limit,
        total_pages=1,
    )


@router.get("/inquiries/{inquiry_id}", response_model=EbayInquiryResponse)
@handle_service_errors_sync
def get_inquiry(
    inquiry_id: int,
    service: EbayInquiryService = Depends(get_inquiry_service),
):
    """Get detailed information about a specific INR inquiry."""
    inquiry_obj = service.get_inquiry(inquiry_id)
    if not inquiry_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inquiry {inquiry_id} not found",
        )
    return EbayInquiryResponse.model_validate(inquiry_obj)


# =============================================================================
# ACTION ENDPOINTS
# =============================================================================


@router.post("/inquiries/{inquiry_id}/shipment-info", response_model=InquiryActionResponse)
@handle_service_errors_sync
def provide_shipment_info(
    inquiry_id: int,
    request: ProvideShipmentInfoRequest,
    service: EbayInquiryService = Depends(get_inquiry_service),
):
    """Provide shipment tracking information for an INR inquiry."""
    result = service.provide_shipment_info(
        inquiry_pk=inquiry_id,
        tracking_number=request.tracking_number,
        carrier=request.carrier,
        shipped_date=request.shipped_date,
        comments=request.comments,
    )
    return InquiryActionResponse(**result)


@router.post("/inquiries/{inquiry_id}/refund", response_model=InquiryActionResponse)
@handle_service_errors_sync
def provide_refund(
    inquiry_id: int,
    request: ProvideRefundRequest = Body(default=ProvideRefundRequest()),
    service: EbayInquiryService = Depends(get_inquiry_service),
):
    """Provide refund for an INR inquiry. Omit amount for full refund."""
    result = service.provide_refund(
        inquiry_pk=inquiry_id,
        refund_amount=request.refund_amount,
        currency=request.currency,
        comments=request.comments,
    )
    return InquiryActionResponse(**result)


@router.post("/inquiries/{inquiry_id}/message", response_model=InquiryActionResponse)
@handle_service_errors_sync
def send_message(
    inquiry_id: int,
    request: InquirySendMessageRequest,
    service: EbayInquiryService = Depends(get_inquiry_service),
):
    """Send message to buyer about an INR inquiry."""
    result = service.send_message(
        inquiry_pk=inquiry_id,
        message=request.message,
    )
    return InquiryActionResponse(**result)


@router.post("/inquiries/{inquiry_id}/escalate", response_model=InquiryActionResponse)
@handle_service_errors_sync
def escalate_inquiry(
    inquiry_id: int,
    request: EscalateInquiryRequest = Body(default=EscalateInquiryRequest()),
    service: EbayInquiryService = Depends(get_inquiry_service),
):
    """Escalate an INR inquiry to an eBay case. Warning: May impact seller metrics."""
    result = service.escalate_inquiry(
        inquiry_pk=inquiry_id,
        comments=request.comments,
    )
    return InquiryActionResponse(**result)
