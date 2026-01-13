"""
API Routes eBay Returns.

Endpoints for eBay returns management with local DB synchronization.

Features:
- Synchronization from eBay Post-Order API
- List with pagination and filters
- Return details
- Actions: accept, decline, refund, mark received, send message
- Statistics

Architecture:
- Repository for data access
- Services for business logic
- Local DB for cache and history

Author: Claude
Date: 2026-01-13
"""

from typing import Optional, Tuple

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.dependencies import get_user_db
from models.public.user import User
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
from shared.logging_setup import get_logger

logger = get_logger(__name__)

router = APIRouter()


# =============================================================================
# SYNC ENDPOINT
# =============================================================================


@router.post("/returns/sync", response_model=SyncReturnsResponse)
async def sync_returns(
    request: SyncReturnsRequest = Body(default=SyncReturnsRequest()),
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    Synchronize returns from eBay Post-Order API to local database.

    **Workflow:**
    1. Fetch returns from eBay API (with date range)
    2. Create or update returns in local DB
    3. Return statistics (created, updated, errors)

    **Default behavior:**
    - Syncs returns from the last 30 days
    - All states (OPEN and CLOSED)

    **Request Body:**
    ```json
    {
        "days_back": 30,
        "return_state": null
    }
    ```

    **Example:**
    ```bash
    # Sync last 30 days
    curl -X POST "http://localhost:8000/api/ebay/returns/sync" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{}'

    # Sync only open returns
    curl -X POST "http://localhost:8000/api/ebay/returns/sync" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{"return_state": "OPEN", "days_back": 90}'
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
        f"[POST /returns/sync] user_id={current_user.id}, "
        f"days_back={request.days_back}, return_state={request.return_state}"
    )

    try:
        sync_service = EbayReturnSyncService(db, current_user.id)

        stats = sync_service.sync_returns(
            return_state=request.return_state,
            days_back=request.days_back,
        )

        logger.info(
            f"[POST /returns/sync] Completed: user_id={current_user.id}, "
            f"created={stats['created']}, updated={stats['updated']}, "
            f"errors={stats['errors']}"
        )

        return SyncReturnsResponse(**stats)

    except ValueError as e:
        logger.error(
            f"[POST /returns/sync] Validation error for user {current_user.id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(
            f"[POST /returns/sync] Sync failed for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync operation failed: {str(e)}",
        )


# =============================================================================
# LIST & GET ENDPOINTS
# =============================================================================


@router.get("/returns", response_model=ReturnListResponse)
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
    order_id: Optional[str] = Query(
        None,
        description="Filter by eBay order ID",
    ),
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    List eBay returns with pagination and filters.

    **Features:**
    - Pagination (default: 50 items per page, max 200)
    - Filter by state (OPEN, CLOSED)
    - Filter by status
    - Filter by order ID
    - Sorted by creation date (newest first)

    **Example:**
    ```bash
    # List all returns
    curl "http://localhost:8000/api/ebay/returns" \\
      -H "Authorization: Bearer YOUR_TOKEN"

    # Filter by state
    curl "http://localhost:8000/api/ebay/returns?state=OPEN" \\
      -H "Authorization: Bearer YOUR_TOKEN"

    # Filter by order
    curl "http://localhost:8000/api/ebay/returns?order_id=12-34567-89012" \\
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
        Paginated list of returns

    Raises:
        400: Invalid query parameters
    """
    db, current_user = db_user

    logger.debug(
        f"[GET /returns] user_id={current_user.id}, page={page}, "
        f"page_size={page_size}, state={state}, status={status_filter}"
    )

    try:
        return_service = EbayReturnService(db, current_user.id)

        skip = (page - 1) * page_size

        returns, total = return_service.list_returns(
            skip=skip,
            limit=page_size,
            state=state,
            status=status_filter,
            order_id=order_id,
        )

        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        items = [EbayReturnResponse.model_validate(r) for r in returns]

        logger.debug(
            f"[GET /returns] Returned {len(items)} returns for user {current_user.id} "
            f"(page {page}/{total_pages})"
        )

        return ReturnListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    except Exception as e:
        logger.error(
            f"[GET /returns] Failed for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list returns: {str(e)}",
        )


@router.get("/returns/statistics", response_model=ReturnStatisticsResponse)
def get_return_statistics(
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    Get return statistics.

    **Returns:**
    - open: Number of open returns
    - closed: Number of closed returns
    - needs_action: Number of returns needing seller action
    - past_deadline: Number of returns past deadline

    **Example:**
    ```bash
    curl "http://localhost:8000/api/ebay/returns/statistics" \\
      -H "Authorization: Bearer YOUR_TOKEN"
    ```

    Args:
        db_user: DB session and authenticated user

    Returns:
        Return statistics
    """
    db, current_user = db_user

    logger.debug(f"[GET /returns/statistics] user_id={current_user.id}")

    try:
        return_service = EbayReturnService(db, current_user.id)
        stats = return_service.get_return_statistics()

        return ReturnStatisticsResponse(**stats)

    except Exception as e:
        logger.error(
            f"[GET /returns/statistics] Failed for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}",
        )


@router.get("/returns/needs-action", response_model=ReturnListResponse)
def list_returns_needing_action(
    limit: int = Query(100, ge=1, le=200, description="Max results"),
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    List returns requiring seller action.

    **Action-needed statuses:**
    - RETURN_REQUESTED: Buyer requested return, awaiting decision
    - RETURN_WAITING_FOR_RMA: Awaiting RMA number
    - RETURN_ITEM_DELIVERED: Item received, awaiting refund

    **Example:**
    ```bash
    curl "http://localhost:8000/api/ebay/returns/needs-action" \\
      -H "Authorization: Bearer YOUR_TOKEN"
    ```

    Args:
        limit: Max results (default 100)
        db_user: DB session and authenticated user

    Returns:
        List of returns needing action (sorted by deadline)
    """
    db, current_user = db_user

    logger.debug(f"[GET /returns/needs-action] user_id={current_user.id}")

    try:
        return_service = EbayReturnService(db, current_user.id)
        returns = return_service.get_returns_needing_action(limit=limit)

        items = [EbayReturnResponse.model_validate(r) for r in returns]

        return ReturnListResponse(
            items=items,
            total=len(items),
            page=1,
            page_size=limit,
            total_pages=1,
        )

    except Exception as e:
        logger.error(
            f"[GET /returns/needs-action] Failed for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list returns: {str(e)}",
        )


@router.get("/returns/past-deadline", response_model=ReturnListResponse)
def list_returns_past_deadline(
    limit: int = Query(100, ge=1, le=200, description="Max results"),
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    List returns past their deadline (urgent).

    **Example:**
    ```bash
    curl "http://localhost:8000/api/ebay/returns/past-deadline" \\
      -H "Authorization: Bearer YOUR_TOKEN"
    ```

    Args:
        limit: Max results (default 100)
        db_user: DB session and authenticated user

    Returns:
        List of returns past deadline
    """
    db, current_user = db_user

    logger.debug(f"[GET /returns/past-deadline] user_id={current_user.id}")

    try:
        return_service = EbayReturnService(db, current_user.id)
        returns = return_service.get_returns_past_deadline(limit=limit)

        items = [EbayReturnResponse.model_validate(r) for r in returns]

        return ReturnListResponse(
            items=items,
            total=len(items),
            page=1,
            page_size=limit,
            total_pages=1,
        )

    except Exception as e:
        logger.error(
            f"[GET /returns/past-deadline] Failed for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list returns: {str(e)}",
        )


@router.get("/returns/{return_id}", response_model=EbayReturnResponse)
def get_return(
    return_id: int,
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    Get detailed information about a specific return.

    **Example:**
    ```bash
    curl "http://localhost:8000/api/ebay/returns/123" \\
      -H "Authorization: Bearer YOUR_TOKEN"
    ```

    Args:
        return_id: Internal return ID
        db_user: DB session and authenticated user

    Returns:
        Return details

    Raises:
        404: Return not found
    """
    db, current_user = db_user

    logger.debug(f"[GET /returns/{return_id}] user_id={current_user.id}")

    try:
        return_service = EbayReturnService(db, current_user.id)
        return_obj = return_service.get_return(return_id)

        if not return_obj:
            logger.warning(
                f"[GET /returns/{return_id}] Not found for user {current_user.id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Return {return_id} not found",
            )

        return EbayReturnResponse.model_validate(return_obj)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"[GET /returns/{return_id}] Failed for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get return: {str(e)}",
        )


# =============================================================================
# ACTION ENDPOINTS
# =============================================================================


@router.post("/returns/{return_id}/accept", response_model=ReturnActionResponse)
def accept_return(
    return_id: int,
    request: AcceptReturnRequest = Body(default=AcceptReturnRequest()),
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    Accept a return request.

    **Workflow:**
    1. Call eBay API to accept return
    2. Update local DB status
    3. Optionally send RMA number

    **Example:**
    ```bash
    curl -X POST "http://localhost:8000/api/ebay/returns/123/accept" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{"comments": "Please ship the item back", "rma_number": "RMA-001"}'
    ```

    Args:
        return_id: Internal return ID
        request: Accept request with optional comments and RMA
        db_user: DB session and authenticated user

    Returns:
        Action result

    Raises:
        404: Return not found
        500: eBay API call failed
    """
    db, current_user = db_user

    logger.info(
        f"[POST /returns/{return_id}/accept] user_id={current_user.id}"
    )

    try:
        return_service = EbayReturnService(db, current_user.id)

        result = return_service.accept_return(
            return_id=return_id,
            comments=request.comments,
            rma_number=request.rma_number,
        )

        return ReturnActionResponse(**result)

    except ValueError as e:
        logger.warning(f"[POST /returns/{return_id}/accept] Not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except RuntimeError as e:
        logger.error(f"[POST /returns/{return_id}/accept] API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/returns/{return_id}/decline", response_model=ReturnActionResponse)
def decline_return(
    return_id: int,
    request: DeclineReturnRequest,
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    Decline a return request.

    **Warning:** Declining returns can negatively impact seller metrics.

    **Example:**
    ```bash
    curl -X POST "http://localhost:8000/api/ebay/returns/123/decline" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{"comments": "Item was as described"}'
    ```

    Args:
        return_id: Internal return ID
        request: Decline request with required comments
        db_user: DB session and authenticated user

    Returns:
        Action result

    Raises:
        400: Comments required
        404: Return not found
        500: eBay API call failed
    """
    db, current_user = db_user

    logger.info(
        f"[POST /returns/{return_id}/decline] user_id={current_user.id}"
    )

    try:
        return_service = EbayReturnService(db, current_user.id)

        result = return_service.decline_return(
            return_id=return_id,
            comments=request.comments,
        )

        return ReturnActionResponse(**result)

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
        logger.error(f"[POST /returns/{return_id}/decline] API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/returns/{return_id}/refund", response_model=ReturnActionResponse)
def issue_refund(
    return_id: int,
    request: IssueRefundRequest = Body(default=IssueRefundRequest()),
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    Issue refund for a return.

    **Options:**
    - Full refund: Omit refund_amount
    - Partial refund: Specify refund_amount and currency

    **Example:**
    ```bash
    # Full refund
    curl -X POST "http://localhost:8000/api/ebay/returns/123/refund" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{}'

    # Partial refund
    curl -X POST "http://localhost:8000/api/ebay/returns/123/refund" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{"refund_amount": 25.00, "currency": "EUR"}'
    ```

    Args:
        return_id: Internal return ID
        request: Refund request with optional amount
        db_user: DB session and authenticated user

    Returns:
        Action result

    Raises:
        404: Return not found
        500: eBay API call failed
    """
    db, current_user = db_user

    logger.info(
        f"[POST /returns/{return_id}/refund] user_id={current_user.id}, "
        f"amount={request.refund_amount}"
    )

    try:
        return_service = EbayReturnService(db, current_user.id)

        result = return_service.issue_refund(
            return_id=return_id,
            refund_amount=request.refund_amount,
            currency=request.currency,
            comments=request.comments,
        )

        return ReturnActionResponse(**result)

    except ValueError as e:
        logger.warning(f"[POST /returns/{return_id}/refund] Not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except RuntimeError as e:
        logger.error(f"[POST /returns/{return_id}/refund] API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/returns/{return_id}/received", response_model=ReturnActionResponse)
def mark_as_received(
    return_id: int,
    request: MarkAsReceivedRequest = Body(default=MarkAsReceivedRequest()),
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    Mark return item as received by seller.

    **Example:**
    ```bash
    curl -X POST "http://localhost:8000/api/ebay/returns/123/received" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{"comments": "Item received in good condition"}'
    ```

    Args:
        return_id: Internal return ID
        request: Mark received request with optional comments
        db_user: DB session and authenticated user

    Returns:
        Action result

    Raises:
        404: Return not found
        500: eBay API call failed
    """
    db, current_user = db_user

    logger.info(
        f"[POST /returns/{return_id}/received] user_id={current_user.id}"
    )

    try:
        return_service = EbayReturnService(db, current_user.id)

        result = return_service.mark_as_received(
            return_id=return_id,
            comments=request.comments,
        )

        return ReturnActionResponse(**result)

    except ValueError as e:
        logger.warning(f"[POST /returns/{return_id}/received] Not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except RuntimeError as e:
        logger.error(f"[POST /returns/{return_id}/received] API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/returns/{return_id}/message", response_model=ReturnActionResponse)
def send_message(
    return_id: int,
    request: SendMessageRequest,
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    Send message to buyer about return.

    **Example:**
    ```bash
    curl -X POST "http://localhost:8000/api/ebay/returns/123/message" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{"message": "Please ship the item back"}'
    ```

    Args:
        return_id: Internal return ID
        request: Message request with message text
        db_user: DB session and authenticated user

    Returns:
        Action result

    Raises:
        400: Message required
        404: Return not found
        500: eBay API call failed
    """
    db, current_user = db_user

    logger.info(
        f"[POST /returns/{return_id}/message] user_id={current_user.id}"
    )

    try:
        return_service = EbayReturnService(db, current_user.id)

        result = return_service.send_message(
            return_id=return_id,
            message=request.message,
        )

        return ReturnActionResponse(**result)

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
        logger.error(f"[POST /returns/{return_id}/message] API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
