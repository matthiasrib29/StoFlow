"""
API Routes eBay Cancellations.

Endpoints for eBay cancellation management with local DB synchronization.

Features:
- Synchronization from eBay Post-Order API
- List with pagination and filters
- Cancellation details
- Actions: approve, reject, create (seller-initiated)
- Eligibility check
- Statistics

Author: Claude
Date: 2026-01-14
Refactored: 2026-01-20
"""

from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from api.dependencies.ebay_dependencies import get_cancellation_service, get_db_and_user
from schemas.ebay_cancellation_schemas import (
    ApproveCancellationRequest,
    CancellationActionResponse,
    CancellationListResponse,
    CancellationStatisticsResponse,
    CheckEligibilityRequest,
    CreateCancellationRequest,
    EbayCancellationResponse,
    EligibilityResponse,
    RejectCancellationRequest,
    SyncCancellationsRequest,
    SyncCancellationsResponse,
)
from services.ebay.ebay_cancellation_service import EbayCancellationService
from services.ebay.ebay_cancellation_sync_service import EbayCancellationSyncService
from shared.logging import get_logger
from shared.route_utils import handle_service_errors, handle_service_errors_sync

logger = get_logger(__name__)
router = APIRouter(prefix="/ebay", tags=["eBay Cancellations"])


# =============================================================================
# SYNC ENDPOINT
# =============================================================================


@router.post("/cancellations/sync", response_model=SyncCancellationsResponse)
@handle_service_errors
async def sync_cancellations(
    request: SyncCancellationsRequest = Body(default=SyncCancellationsRequest()),
    db_and_user=Depends(get_db_and_user),
):
    """Synchronize cancellations from eBay Post-Order API to local database."""
    db, current_user = db_and_user
    sync_service = EbayCancellationSyncService(db, current_user.id)

    stats = sync_service.sync_cancellations(
        cancel_state=request.cancel_state,
        days_back=request.days_back,
    )
    logger.info(
        f"[sync_cancellations] created={stats['created']}, updated={stats['updated']}"
    )
    return SyncCancellationsResponse(**stats)


# =============================================================================
# LIST & GET ENDPOINTS
# =============================================================================


@router.get("/cancellations", response_model=CancellationListResponse)
@handle_service_errors_sync
def list_cancellations(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    state: Optional[str] = Query(
        None,
        pattern="^CLOSED$",
        description="Filter by state (CLOSED)",
    ),
    status_filter: Optional[str] = Query(
        None,
        alias="status",
        description="Filter by status (CANCEL_REQUESTED, CANCEL_PENDING, etc.)",
    ),
    order_id: Optional[str] = Query(None, description="Filter by eBay order ID"),
    service: EbayCancellationService = Depends(get_cancellation_service),
):
    """List eBay cancellations with pagination and filters."""
    skip = (page - 1) * page_size
    cancellations, total = service.list_cancellations(
        skip=skip,
        limit=page_size,
        cancel_state=state,
        cancel_status=status_filter,
        order_id=order_id,
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    items = [EbayCancellationResponse.model_validate(c) for c in cancellations]

    return CancellationListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/cancellations/statistics", response_model=CancellationStatisticsResponse)
@handle_service_errors_sync
def get_cancellation_statistics(
    service: EbayCancellationService = Depends(get_cancellation_service),
):
    """Get cancellation statistics."""
    stats = service.get_cancellation_statistics()
    return CancellationStatisticsResponse(**stats)


@router.get("/cancellations/needs-action", response_model=CancellationListResponse)
@handle_service_errors_sync
def list_cancellations_needing_action(
    limit: int = Query(100, ge=1, le=200, description="Max results"),
    service: EbayCancellationService = Depends(get_cancellation_service),
):
    """List cancellations requiring seller action."""
    cancellations = service.get_cancellations_needing_action(limit=limit)
    items = [EbayCancellationResponse.model_validate(c) for c in cancellations]
    return CancellationListResponse(
        items=items,
        total=len(items),
        page=1,
        page_size=limit,
        total_pages=1,
    )


@router.get("/cancellations/past-due", response_model=CancellationListResponse)
@handle_service_errors_sync
def list_cancellations_past_due(
    limit: int = Query(100, ge=1, le=200, description="Max results"),
    service: EbayCancellationService = Depends(get_cancellation_service),
):
    """List cancellations past their response deadline (urgent)."""
    cancellations = service.get_cancellations_past_due(limit=limit)
    items = [EbayCancellationResponse.model_validate(c) for c in cancellations]
    return CancellationListResponse(
        items=items,
        total=len(items),
        page=1,
        page_size=limit,
        total_pages=1,
    )


@router.get("/cancellations/{cancellation_id}", response_model=EbayCancellationResponse)
@handle_service_errors_sync
def get_cancellation(
    cancellation_id: int,
    service: EbayCancellationService = Depends(get_cancellation_service),
):
    """Get detailed information about a specific cancellation."""
    cancel_obj = service.get_cancellation(cancellation_id)
    if not cancel_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cancellation {cancellation_id} not found",
        )
    return EbayCancellationResponse.model_validate(cancel_obj)


# =============================================================================
# ACTION ENDPOINTS
# =============================================================================


@router.post("/cancellations/check-eligibility", response_model=EligibilityResponse)
@handle_service_errors_sync
def check_eligibility(
    request: CheckEligibilityRequest,
    service: EbayCancellationService = Depends(get_cancellation_service),
):
    """Check if an order is eligible for seller-initiated cancellation."""
    result = service.check_eligibility(request.order_id)

    eligible = result.get("eligible", False)
    eligibility_status = result.get("eligibilityStatus")
    reasons = result.get("failureReason", [])
    if isinstance(reasons, str):
        reasons = [reasons]

    return EligibilityResponse(
        eligible=eligible,
        eligibility_status=eligibility_status,
        order_id=request.order_id,
        reasons=reasons,
    )


@router.post("/cancellations/create", response_model=CancellationActionResponse)
@handle_service_errors_sync
def create_cancellation(
    request: CreateCancellationRequest,
    service: EbayCancellationService = Depends(get_cancellation_service),
):
    """Create a seller-initiated cancellation request."""
    result = service.create_cancellation(
        order_id=request.order_id,
        reason=request.reason,
        comments=request.comments,
    )
    return CancellationActionResponse(
        success=result.get("success", False),
        cancel_id=result.get("cancel_id", ""),
        new_status=result.get("status"),
        message="Cancellation created successfully",
    )


@router.post(
    "/cancellations/{cancellation_id}/approve", response_model=CancellationActionResponse
)
@handle_service_errors_sync
def approve_cancellation(
    cancellation_id: int,
    request: ApproveCancellationRequest = Body(default=ApproveCancellationRequest()),
    service: EbayCancellationService = Depends(get_cancellation_service),
):
    """Approve a buyer's cancellation request."""
    result = service.approve_cancellation(
        cancellation_id=cancellation_id,
        comments=request.comments,
    )
    return CancellationActionResponse(
        success=result.get("success", False),
        cancel_id=result.get("cancel_id", ""),
        new_status=result.get("new_status"),
        message="Cancellation approved successfully",
    )


@router.post(
    "/cancellations/{cancellation_id}/reject", response_model=CancellationActionResponse
)
@handle_service_errors_sync
def reject_cancellation(
    cancellation_id: int,
    request: RejectCancellationRequest,
    service: EbayCancellationService = Depends(get_cancellation_service),
):
    """Reject a buyer's cancellation request."""
    result = service.reject_cancellation(
        cancellation_id=cancellation_id,
        reason=request.reason,
        tracking_number=request.tracking_number,
        carrier=request.carrier,
        comments=request.comments,
    )
    return CancellationActionResponse(
        success=result.get("success", False),
        cancel_id=result.get("cancel_id", ""),
        new_status=result.get("new_status"),
        message="Cancellation rejected successfully",
    )
