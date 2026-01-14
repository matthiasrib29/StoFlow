"""
API Routes eBay INR Inquiries.

Endpoints for eBay INR (Item Not Received) inquiry management.

Features:
- Synchronization from eBay Post-Order API
- List with pagination and filters
- Inquiry details
- Actions: provide shipment info, refund, send message, escalate
- Statistics

Architecture:
- Repository for data access
- Services for business logic
- Local DB for cache and history

Author: Claude
Date: 2026-01-14
"""

from typing import Optional, Tuple

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.dependencies import get_user_db
from models.public.user import User
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
from shared.logging_setup import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/ebay", tags=["eBay Inquiries"])


# =============================================================================
# SYNC ENDPOINT
# =============================================================================


@router.post("/inquiries/sync", response_model=SyncInquiriesResponse)
async def sync_inquiries(
    request: SyncInquiriesRequest = Body(default=SyncInquiriesRequest()),
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    Synchronize INR inquiries from eBay Post-Order API to local database.

    **Workflow:**
    1. Fetch inquiries from eBay API
    2. Create or update inquiries in local DB
    3. Return statistics (created, updated, errors)

    **Example:**
    ```bash
    # Sync all inquiries
    curl -X POST "http://localhost:8000/api/ebay/inquiries/sync" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{}'

    # Sync only open inquiries
    curl -X POST "http://localhost:8000/api/ebay/inquiries/sync" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{"inquiry_state": "OPEN"}'
    ```

    Args:
        request: Sync request with optional state filter
        db_user: DB session and authenticated user

    Returns:
        Statistics about sync operation

    Raises:
        400: Invalid request parameters
        500: Sync operation failed
    """
    db, current_user = db_user

    logger.info(
        f"[POST /inquiries/sync] user_id={current_user.id}, "
        f"inquiry_state={request.inquiry_state}"
    )

    try:
        inquiry_service = EbayInquiryService(db, current_user.id)

        stats = inquiry_service.sync_inquiries(
            state=request.inquiry_state,
        )

        logger.info(
            f"[POST /inquiries/sync] Completed: user_id={current_user.id}, "
            f"created={stats['created']}, updated={stats['updated']}"
        )

        return SyncInquiriesResponse(**stats)

    except ValueError as e:
        logger.error(
            f"[POST /inquiries/sync] Validation error for user {current_user.id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(
            f"[POST /inquiries/sync] Sync failed for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync operation failed: {str(e)}",
        )


# =============================================================================
# LIST & GET ENDPOINTS
# =============================================================================


@router.get("/inquiries", response_model=InquiryListResponse)
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
    order_id: Optional[str] = Query(
        None,
        description="Filter by eBay order ID",
    ),
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    List eBay INR inquiries with pagination and filters.

    **Features:**
    - Pagination (default: 50 items per page, max 200)
    - Filter by state (OPEN, CLOSED)
    - Filter by status
    - Filter by order ID
    - Sorted by creation date (newest first)

    **Example:**
    ```bash
    # List all inquiries
    curl "http://localhost:8000/api/ebay/inquiries" \\
      -H "Authorization: Bearer YOUR_TOKEN"

    # Filter by state
    curl "http://localhost:8000/api/ebay/inquiries?state=OPEN" \\
      -H "Authorization: Bearer YOUR_TOKEN"
    ```

    Args:
        page: Page number (1-indexed)
        page_size: Items per page (1-200)
        state: Optional state filter
        status_filter: Optional status filter
        order_id: Optional order ID filter
        db_user: DB session and authenticated user

    Returns:
        Paginated list of inquiries

    Raises:
        400: Invalid query parameters
    """
    db, current_user = db_user

    logger.debug(
        f"[GET /inquiries] user_id={current_user.id}, page={page}, "
        f"page_size={page_size}, state={state}, status={status_filter}"
    )

    try:
        inquiry_service = EbayInquiryService(db, current_user.id)

        skip = (page - 1) * page_size

        inquiries, total = inquiry_service.list_inquiries(
            skip=skip,
            limit=page_size,
            state=state,
            status=status_filter,
            order_id=order_id,
        )

        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        items = [EbayInquiryResponse.model_validate(i) for i in inquiries]

        logger.debug(
            f"[GET /inquiries] Returned {len(items)} inquiries for user {current_user.id} "
            f"(page {page}/{total_pages})"
        )

        return InquiryListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    except Exception as e:
        logger.error(
            f"[GET /inquiries] Failed for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list inquiries: {str(e)}",
        )


@router.get("/inquiries/statistics", response_model=InquiryStatisticsResponse)
def get_inquiry_statistics(
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    Get inquiry statistics.

    **Returns:**
    - open: Number of open inquiries
    - closed: Number of closed inquiries
    - needs_action: Number of inquiries needing seller action
    - past_deadline: Number of inquiries past deadline

    **Example:**
    ```bash
    curl "http://localhost:8000/api/ebay/inquiries/statistics" \\
      -H "Authorization: Bearer YOUR_TOKEN"
    ```

    Args:
        db_user: DB session and authenticated user

    Returns:
        Inquiry statistics
    """
    db, current_user = db_user

    logger.debug(f"[GET /inquiries/statistics] user_id={current_user.id}")

    try:
        inquiry_service = EbayInquiryService(db, current_user.id)
        stats = inquiry_service.get_inquiry_statistics()

        return InquiryStatisticsResponse(**stats)

    except Exception as e:
        logger.error(
            f"[GET /inquiries/statistics] Failed for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}",
        )


@router.get("/inquiries/needs-action", response_model=InquiryListResponse)
def list_inquiries_needing_action(
    limit: int = Query(100, ge=1, le=200, description="Max results"),
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    List INR inquiries requiring seller action.

    **Action-needed statuses:**
    - INR_WAITING_FOR_SELLER: Awaiting seller response

    **Example:**
    ```bash
    curl "http://localhost:8000/api/ebay/inquiries/needs-action" \\
      -H "Authorization: Bearer YOUR_TOKEN"
    ```

    Args:
        limit: Max results (default 100)
        db_user: DB session and authenticated user

    Returns:
        List of inquiries needing action (sorted by deadline)
    """
    db, current_user = db_user

    logger.debug(f"[GET /inquiries/needs-action] user_id={current_user.id}")

    try:
        inquiry_service = EbayInquiryService(db, current_user.id)
        inquiries = inquiry_service.get_inquiries_needing_action(limit=limit)

        items = [EbayInquiryResponse.model_validate(i) for i in inquiries]

        return InquiryListResponse(
            items=items,
            total=len(items),
            page=1,
            page_size=limit,
            total_pages=1,
        )

    except Exception as e:
        logger.error(
            f"[GET /inquiries/needs-action] Failed for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list inquiries: {str(e)}",
        )


@router.get("/inquiries/past-deadline", response_model=InquiryListResponse)
def list_inquiries_past_deadline(
    limit: int = Query(100, ge=1, le=200, description="Max results"),
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    List INR inquiries past their response deadline (urgent).

    **Example:**
    ```bash
    curl "http://localhost:8000/api/ebay/inquiries/past-deadline" \\
      -H "Authorization: Bearer YOUR_TOKEN"
    ```

    Args:
        limit: Max results (default 100)
        db_user: DB session and authenticated user

    Returns:
        List of inquiries past deadline
    """
    db, current_user = db_user

    logger.debug(f"[GET /inquiries/past-deadline] user_id={current_user.id}")

    try:
        inquiry_service = EbayInquiryService(db, current_user.id)
        inquiries = inquiry_service.get_inquiries_past_deadline(limit=limit)

        items = [EbayInquiryResponse.model_validate(i) for i in inquiries]

        return InquiryListResponse(
            items=items,
            total=len(items),
            page=1,
            page_size=limit,
            total_pages=1,
        )

    except Exception as e:
        logger.error(
            f"[GET /inquiries/past-deadline] Failed for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list inquiries: {str(e)}",
        )


@router.get("/inquiries/{inquiry_id}", response_model=EbayInquiryResponse)
def get_inquiry(
    inquiry_id: int,
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    Get detailed information about a specific INR inquiry.

    **Example:**
    ```bash
    curl "http://localhost:8000/api/ebay/inquiries/123" \\
      -H "Authorization: Bearer YOUR_TOKEN"
    ```

    Args:
        inquiry_id: Internal inquiry ID
        db_user: DB session and authenticated user

    Returns:
        Inquiry details

    Raises:
        404: Inquiry not found
    """
    db, current_user = db_user

    logger.debug(f"[GET /inquiries/{inquiry_id}] user_id={current_user.id}")

    try:
        inquiry_service = EbayInquiryService(db, current_user.id)
        inquiry_obj = inquiry_service.get_inquiry(inquiry_id)

        if not inquiry_obj:
            logger.warning(
                f"[GET /inquiries/{inquiry_id}] Not found for user {current_user.id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inquiry {inquiry_id} not found",
            )

        return EbayInquiryResponse.model_validate(inquiry_obj)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"[GET /inquiries/{inquiry_id}] Failed for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get inquiry: {str(e)}",
        )


# =============================================================================
# ACTION ENDPOINTS
# =============================================================================


@router.post("/inquiries/{inquiry_id}/shipment-info", response_model=InquiryActionResponse)
def provide_shipment_info(
    inquiry_id: int,
    request: ProvideShipmentInfoRequest,
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    Provide shipment tracking information for an INR inquiry.

    This is the primary response when the item has been shipped.

    **Example:**
    ```bash
    curl -X POST "http://localhost:8000/api/ebay/inquiries/123/shipment-info" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{"tracking_number": "1Z999AA10123456784", "carrier": "UPS"}'
    ```

    Args:
        inquiry_id: Internal inquiry ID
        request: Shipment info request
        db_user: DB session and authenticated user

    Returns:
        Action result

    Raises:
        404: Inquiry not found
        500: eBay API call failed
    """
    db, current_user = db_user

    logger.info(
        f"[POST /inquiries/{inquiry_id}/shipment-info] user_id={current_user.id}, "
        f"tracking={request.tracking_number}"
    )

    try:
        inquiry_service = EbayInquiryService(db, current_user.id)

        result = inquiry_service.provide_shipment_info(
            inquiry_pk=inquiry_id,
            tracking_number=request.tracking_number,
            carrier=request.carrier,
            shipped_date=request.shipped_date,
            comments=request.comments,
        )

        return InquiryActionResponse(**result)

    except ValueError as e:
        logger.warning(f"[POST /inquiries/{inquiry_id}/shipment-info] Not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except RuntimeError as e:
        logger.error(f"[POST /inquiries/{inquiry_id}/shipment-info] API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/inquiries/{inquiry_id}/refund", response_model=InquiryActionResponse)
def provide_refund(
    inquiry_id: int,
    request: ProvideRefundRequest = Body(default=ProvideRefundRequest()),
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    Provide refund for an INR inquiry.

    Use this when the item was not shipped or cannot be delivered.

    **Example:**
    ```bash
    # Full refund
    curl -X POST "http://localhost:8000/api/ebay/inquiries/123/refund" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{}'

    # Partial refund
    curl -X POST "http://localhost:8000/api/ebay/inquiries/123/refund" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{"refund_amount": 25.00, "currency": "EUR"}'
    ```

    Args:
        inquiry_id: Internal inquiry ID
        request: Refund request with optional amount
        db_user: DB session and authenticated user

    Returns:
        Action result

    Raises:
        404: Inquiry not found
        500: eBay API call failed
    """
    db, current_user = db_user

    logger.info(
        f"[POST /inquiries/{inquiry_id}/refund] user_id={current_user.id}, "
        f"amount={request.refund_amount}"
    )

    try:
        inquiry_service = EbayInquiryService(db, current_user.id)

        result = inquiry_service.provide_refund(
            inquiry_pk=inquiry_id,
            refund_amount=request.refund_amount,
            currency=request.currency,
            comments=request.comments,
        )

        return InquiryActionResponse(**result)

    except ValueError as e:
        logger.warning(f"[POST /inquiries/{inquiry_id}/refund] Not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except RuntimeError as e:
        logger.error(f"[POST /inquiries/{inquiry_id}/refund] API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/inquiries/{inquiry_id}/message", response_model=InquiryActionResponse)
def send_message(
    inquiry_id: int,
    request: InquirySendMessageRequest,
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    Send message to buyer about an INR inquiry.

    **Example:**
    ```bash
    curl -X POST "http://localhost:8000/api/ebay/inquiries/123/message" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{"message": "Your package is on its way"}'
    ```

    Args:
        inquiry_id: Internal inquiry ID
        request: Message request
        db_user: DB session and authenticated user

    Returns:
        Action result

    Raises:
        400: Message required
        404: Inquiry not found
        500: eBay API call failed
    """
    db, current_user = db_user

    logger.info(
        f"[POST /inquiries/{inquiry_id}/message] user_id={current_user.id}"
    )

    try:
        inquiry_service = EbayInquiryService(db, current_user.id)

        result = inquiry_service.send_message(
            inquiry_pk=inquiry_id,
            message=request.message,
        )

        return InquiryActionResponse(**result)

    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except RuntimeError as e:
        logger.error(f"[POST /inquiries/{inquiry_id}/message] API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/inquiries/{inquiry_id}/escalate", response_model=InquiryActionResponse)
def escalate_inquiry(
    inquiry_id: int,
    request: EscalateInquiryRequest = Body(default=EscalateInquiryRequest()),
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    Escalate an INR inquiry to an eBay case.

    **Warning:** Escalation may impact seller metrics.

    **Example:**
    ```bash
    curl -X POST "http://localhost:8000/api/ebay/inquiries/123/escalate" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{"comments": "Buyer is not responding"}'
    ```

    Args:
        inquiry_id: Internal inquiry ID
        request: Escalate request with optional comments
        db_user: DB session and authenticated user

    Returns:
        Action result

    Raises:
        404: Inquiry not found
        500: eBay API call failed
    """
    db, current_user = db_user

    logger.info(
        f"[POST /inquiries/{inquiry_id}/escalate] user_id={current_user.id}"
    )

    try:
        inquiry_service = EbayInquiryService(db, current_user.id)

        result = inquiry_service.escalate_inquiry(
            inquiry_pk=inquiry_id,
            comments=request.comments,
        )

        return InquiryActionResponse(**result)

    except ValueError as e:
        logger.warning(f"[POST /inquiries/{inquiry_id}/escalate] Not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except RuntimeError as e:
        logger.error(f"[POST /inquiries/{inquiry_id}/escalate] API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
