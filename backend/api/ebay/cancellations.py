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
from shared.logging_setup import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/ebay", tags=["eBay Cancellations"])


# =============================================================================
# SYNC ENDPOINT
# =============================================================================


@router.post("/cancellations/sync", response_model=SyncCancellationsResponse)
async def sync_cancellations(
    request: SyncCancellationsRequest = Body(default=SyncCancellationsRequest()),
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    Synchronize cancellations from eBay Post-Order API to local database.

    **Workflow:**
    1. Fetch cancellations from eBay API (with date range)
    2. Create or update cancellations in local DB
    3. Return statistics (created, updated, errors)

    **Default behavior:**
    - Syncs cancellations from the last 30 days
    - All states

    **Request Body:**
    ```json
    {
        "days_back": 30,
        "cancel_state": null
    }
    ```

    **Example:**
    ```bash
    # Sync last 30 days
    curl -X POST "http://localhost:8000/api/ebay/cancellations/sync" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{}'

    # Sync only closed cancellations
    curl -X POST "http://localhost:8000/api/ebay/cancellations/sync" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{"cancel_state": "CLOSED", "days_back": 90}'
    ```

    Args:
        request: Sync request with days_back and optional state filter
        db_user: DB session and authenticated user

    Returns:
        Statistics about sync operation

    Raises:
        400: Invalid request parameters
        500: Sync operation failed
    """
    db, current_user = db_user

    logger.info(
        f"[POST /cancellations/sync] user_id={current_user.id}, "
        f"days_back={request.days_back}, cancel_state={request.cancel_state}"
    )

    try:
        sync_service = EbayCancellationSyncService(db, current_user.id)

        stats = sync_service.sync_cancellations(
            cancel_state=request.cancel_state,
            days_back=request.days_back,
        )

        logger.info(
            f"[POST /cancellations/sync] Completed: user_id={current_user.id}, "
            f"created={stats['created']}, updated={stats['updated']}, "
            f"errors={stats['errors']}"
        )

        return SyncCancellationsResponse(**stats)

    except ValueError as e:
        logger.error(
            f"[POST /cancellations/sync] Validation error for user {current_user.id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(
            f"[POST /cancellations/sync] Sync failed for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync operation failed: {str(e)}",
        )


# =============================================================================
# LIST & GET ENDPOINTS
# =============================================================================


@router.get("/cancellations", response_model=CancellationListResponse)
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
    order_id: Optional[str] = Query(
        None,
        description="Filter by eBay order ID",
    ),
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    List eBay cancellations with pagination and filters.

    **Features:**
    - Pagination (default: 50 items per page, max 200)
    - Filter by state (CLOSED)
    - Filter by status
    - Filter by order ID
    - Sorted by creation date (newest first)

    **Example:**
    ```bash
    # List all cancellations
    curl "http://localhost:8000/api/ebay/cancellations" \\
      -H "Authorization: Bearer YOUR_TOKEN"

    # Filter by status
    curl "http://localhost:8000/api/ebay/cancellations?status=CANCEL_REQUESTED" \\
      -H "Authorization: Bearer YOUR_TOKEN"

    # Filter by order
    curl "http://localhost:8000/api/ebay/cancellations?order_id=12-34567-89012" \\
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
        Paginated list of cancellations

    Raises:
        400: Invalid query parameters
    """
    db, current_user = db_user

    logger.debug(
        f"[GET /cancellations] user_id={current_user.id}, page={page}, "
        f"page_size={page_size}, state={state}, status={status_filter}"
    )

    try:
        cancel_service = EbayCancellationService(db, current_user.id)

        skip = (page - 1) * page_size

        cancellations, total = cancel_service.list_cancellations(
            skip=skip,
            limit=page_size,
            cancel_state=state,
            cancel_status=status_filter,
            order_id=order_id,
        )

        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        items = [EbayCancellationResponse.model_validate(c) for c in cancellations]

        logger.debug(
            f"[GET /cancellations] Returned {len(items)} cancellations for user {current_user.id} "
            f"(page {page}/{total_pages})"
        )

        return CancellationListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    except Exception as e:
        logger.error(
            f"[GET /cancellations] Failed for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list cancellations: {str(e)}",
        )


@router.get("/cancellations/statistics", response_model=CancellationStatisticsResponse)
def get_cancellation_statistics(
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    Get cancellation statistics.

    **Returns:**
    - pending: Number of pending cancellations
    - closed: Number of closed cancellations
    - needs_action: Number of cancellations needing seller action
    - past_due: Number of cancellations past response deadline

    **Example:**
    ```bash
    curl "http://localhost:8000/api/ebay/cancellations/statistics" \\
      -H "Authorization: Bearer YOUR_TOKEN"
    ```

    Args:
        db_user: DB session and authenticated user

    Returns:
        Cancellation statistics
    """
    db, current_user = db_user

    logger.debug(f"[GET /cancellations/statistics] user_id={current_user.id}")

    try:
        cancel_service = EbayCancellationService(db, current_user.id)
        stats = cancel_service.get_cancellation_statistics()

        return CancellationStatisticsResponse(**stats)

    except Exception as e:
        logger.error(
            f"[GET /cancellations/statistics] Failed for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}",
        )


@router.get("/cancellations/needs-action", response_model=CancellationListResponse)
def list_cancellations_needing_action(
    limit: int = Query(100, ge=1, le=200, description="Max results"),
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    List cancellations requiring seller action.

    **Action-needed:** Buyer-initiated cancellations that are pending.

    **Example:**
    ```bash
    curl "http://localhost:8000/api/ebay/cancellations/needs-action" \\
      -H "Authorization: Bearer YOUR_TOKEN"
    ```

    Args:
        limit: Max results (default 100)
        db_user: DB session and authenticated user

    Returns:
        List of cancellations needing action (sorted by deadline)
    """
    db, current_user = db_user

    logger.debug(f"[GET /cancellations/needs-action] user_id={current_user.id}")

    try:
        cancel_service = EbayCancellationService(db, current_user.id)
        cancellations = cancel_service.get_cancellations_needing_action(limit=limit)

        items = [EbayCancellationResponse.model_validate(c) for c in cancellations]

        return CancellationListResponse(
            items=items,
            total=len(items),
            page=1,
            page_size=limit,
            total_pages=1,
        )

    except Exception as e:
        logger.error(
            f"[GET /cancellations/needs-action] Failed for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list cancellations: {str(e)}",
        )


@router.get("/cancellations/past-due", response_model=CancellationListResponse)
def list_cancellations_past_due(
    limit: int = Query(100, ge=1, le=200, description="Max results"),
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    List cancellations past their response deadline (urgent).

    **Example:**
    ```bash
    curl "http://localhost:8000/api/ebay/cancellations/past-due" \\
      -H "Authorization: Bearer YOUR_TOKEN"
    ```

    Args:
        limit: Max results (default 100)
        db_user: DB session and authenticated user

    Returns:
        List of cancellations past deadline
    """
    db, current_user = db_user

    logger.debug(f"[GET /cancellations/past-due] user_id={current_user.id}")

    try:
        cancel_service = EbayCancellationService(db, current_user.id)
        cancellations = cancel_service.get_cancellations_past_due(limit=limit)

        items = [EbayCancellationResponse.model_validate(c) for c in cancellations]

        return CancellationListResponse(
            items=items,
            total=len(items),
            page=1,
            page_size=limit,
            total_pages=1,
        )

    except Exception as e:
        logger.error(
            f"[GET /cancellations/past-due] Failed for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list cancellations: {str(e)}",
        )


@router.get("/cancellations/{cancellation_id}", response_model=EbayCancellationResponse)
def get_cancellation(
    cancellation_id: int,
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    Get detailed information about a specific cancellation.

    **Example:**
    ```bash
    curl "http://localhost:8000/api/ebay/cancellations/123" \\
      -H "Authorization: Bearer YOUR_TOKEN"
    ```

    Args:
        cancellation_id: Internal cancellation ID
        db_user: DB session and authenticated user

    Returns:
        Cancellation details

    Raises:
        404: Cancellation not found
    """
    db, current_user = db_user

    logger.debug(f"[GET /cancellations/{cancellation_id}] user_id={current_user.id}")

    try:
        cancel_service = EbayCancellationService(db, current_user.id)
        cancel_obj = cancel_service.get_cancellation(cancellation_id)

        if not cancel_obj:
            logger.warning(
                f"[GET /cancellations/{cancellation_id}] Not found for user {current_user.id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cancellation {cancellation_id} not found",
            )

        return EbayCancellationResponse.model_validate(cancel_obj)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"[GET /cancellations/{cancellation_id}] Failed for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cancellation: {str(e)}",
        )


# =============================================================================
# ACTION ENDPOINTS
# =============================================================================


@router.post("/cancellations/check-eligibility", response_model=EligibilityResponse)
def check_eligibility(
    request: CheckEligibilityRequest,
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    Check if an order is eligible for seller-initiated cancellation.

    **Example:**
    ```bash
    curl -X POST "http://localhost:8000/api/ebay/cancellations/check-eligibility" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{"order_id": "12-34567-89012"}'
    ```

    Args:
        request: Check eligibility request with order_id
        db_user: DB session and authenticated user

    Returns:
        Eligibility result

    Raises:
        500: eBay API call failed
    """
    db, current_user = db_user

    logger.info(
        f"[POST /cancellations/check-eligibility] user_id={current_user.id}, "
        f"order_id={request.order_id}"
    )

    try:
        cancel_service = EbayCancellationService(db, current_user.id)
        result = cancel_service.check_eligibility(request.order_id)

        # Parse eBay response
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

    except Exception as e:
        logger.error(
            f"[POST /cancellations/check-eligibility] Failed for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check eligibility: {str(e)}",
        )


@router.post("/cancellations/create", response_model=CancellationActionResponse)
def create_cancellation(
    request: CreateCancellationRequest,
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    Create a seller-initiated cancellation request.

    **Valid reasons:**
    - OUT_OF_STOCK: Item is out of stock
    - ADDRESS_ISSUES: Problems with shipping address
    - BUYER_ASKED_CANCEL: Buyer requested cancellation
    - ORDER_UNPAID: Order was not paid
    - OTHER_SELLER_CANCEL_REASON: Other reason

    **Example:**
    ```bash
    curl -X POST "http://localhost:8000/api/ebay/cancellations/create" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{
        "order_id": "12-34567-89012",
        "reason": "OUT_OF_STOCK",
        "comments": "Item sold on another platform"
      }'
    ```

    Args:
        request: Create cancellation request
        db_user: DB session and authenticated user

    Returns:
        Action result with cancel_id

    Raises:
        400: Invalid request or order not eligible
        500: eBay API call failed
    """
    db, current_user = db_user

    logger.info(
        f"[POST /cancellations/create] user_id={current_user.id}, "
        f"order_id={request.order_id}, reason={request.reason}"
    )

    try:
        cancel_service = EbayCancellationService(db, current_user.id)

        result = cancel_service.create_cancellation(
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

    except ValueError as e:
        logger.warning(f"[POST /cancellations/create] Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except RuntimeError as e:
        logger.error(f"[POST /cancellations/create] API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/cancellations/{cancellation_id}/approve", response_model=CancellationActionResponse
)
def approve_cancellation(
    cancellation_id: int,
    request: ApproveCancellationRequest = Body(default=ApproveCancellationRequest()),
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    Approve a buyer's cancellation request.

    **Workflow:**
    1. Call eBay API to approve cancellation
    2. Update local DB status
    3. Refund is processed automatically by eBay

    **Example:**
    ```bash
    curl -X POST "http://localhost:8000/api/ebay/cancellations/123/approve" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{"comments": "Approved at buyer request"}'
    ```

    Args:
        cancellation_id: Internal cancellation ID
        request: Approve request with optional comments
        db_user: DB session and authenticated user

    Returns:
        Action result

    Raises:
        404: Cancellation not found
        500: eBay API call failed
    """
    db, current_user = db_user

    logger.info(
        f"[POST /cancellations/{cancellation_id}/approve] user_id={current_user.id}"
    )

    try:
        cancel_service = EbayCancellationService(db, current_user.id)

        result = cancel_service.approve_cancellation(
            cancellation_id=cancellation_id,
            comments=request.comments,
        )

        return CancellationActionResponse(
            success=result.get("success", False),
            cancel_id=result.get("cancel_id", ""),
            new_status=result.get("new_status"),
            message="Cancellation approved successfully",
        )

    except ValueError as e:
        logger.warning(f"[POST /cancellations/{cancellation_id}/approve] Not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except RuntimeError as e:
        logger.error(f"[POST /cancellations/{cancellation_id}/approve] API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/cancellations/{cancellation_id}/reject", response_model=CancellationActionResponse
)
def reject_cancellation(
    cancellation_id: int,
    request: RejectCancellationRequest,
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    Reject a buyer's cancellation request.

    **Valid reasons:**
    - ALREADY_SHIPPED: Item was already shipped (requires tracking_number)
    - OTHER_SELLER_REJECT_REASON: Other reason

    **Note:** If reason is ALREADY_SHIPPED, tracking_number is required.

    **Example:**
    ```bash
    # Reject because already shipped
    curl -X POST "http://localhost:8000/api/ebay/cancellations/123/reject" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{
        "reason": "ALREADY_SHIPPED",
        "tracking_number": "1Z999AA10123456784",
        "carrier": "UPS",
        "comments": "Item shipped before cancellation request"
      }'

    # Reject for other reason
    curl -X POST "http://localhost:8000/api/ebay/cancellations/123/reject" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{
        "reason": "OTHER_SELLER_REJECT_REASON",
        "comments": "Processing already started"
      }'
    ```

    Args:
        cancellation_id: Internal cancellation ID
        request: Reject request with reason and optional tracking
        db_user: DB session and authenticated user

    Returns:
        Action result

    Raises:
        400: Invalid request (missing tracking for ALREADY_SHIPPED)
        404: Cancellation not found
        500: eBay API call failed
    """
    db, current_user = db_user

    logger.info(
        f"[POST /cancellations/{cancellation_id}/reject] user_id={current_user.id}, "
        f"reason={request.reason}"
    )

    try:
        cancel_service = EbayCancellationService(db, current_user.id)

        result = cancel_service.reject_cancellation(
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

    except ValueError as e:
        error_msg = str(e).lower()
        if "not found" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except RuntimeError as e:
        logger.error(f"[POST /cancellations/{cancellation_id}/reject] API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
