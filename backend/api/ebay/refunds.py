"""
API Routes eBay Refunds.

Endpoints for eBay refund management with local DB synchronization.

Features:
- Synchronization from eBay order payment summaries
- List with pagination and filters
- Refund details
- Issue new refunds via Fulfillment API
- Statistics

Architecture:
- Repository for data access
- Service for business logic
- Local DB for cache and history

Note: eBay doesn't have a dedicated refund search API. Refunds are
extracted from order payment summaries via the Fulfillment API.

Author: Claude
Date: 2026-01-14
"""

from typing import Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.dependencies import get_user_db
from models.public.user import User
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
from shared.logging_setup import get_logger

logger = get_logger(__name__)

router = APIRouter()


# =============================================================================
# SYNC ENDPOINTS
# =============================================================================


@router.post("/refunds/sync", response_model=SyncRefundsResponse)
async def sync_refunds(
    request: SyncRefundsRequest = None,
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    Synchronize refunds from eBay orders to local database.

    **Workflow:**
    1. Fetch orders from the last N days (default: 30)
    2. Extract refunds from order payment summaries
    3. Create or update refunds in local DB
    4. Return statistics (created, updated, skipped, errors)

    **Note:** eBay doesn't have a dedicated refund search API.
    Refunds are embedded in order payment summaries.

    **Default behavior:**
    - Syncs refunds from orders modified in the last 30 days

    **Request Body:**
    ```json
    {
        "days_back": 30
    }
    ```

    **Example:**
    ```bash
    # Sync last 30 days
    curl -X POST "http://localhost:8000/api/ebay/refunds/sync" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{}'

    # Sync last 90 days
    curl -X POST "http://localhost:8000/api/ebay/refunds/sync" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{"days_back": 90}'
    ```

    Args:
        request: Sync request with days_back parameter
        db_user: DB session and authenticated user

    Returns:
        Statistics about sync operation

    Raises:
        400: Invalid request parameters
        500: Sync operation failed
    """
    db, current_user = db_user

    if request is None:
        request = SyncRefundsRequest()

    logger.info(
        f"[POST /refunds/sync] user_id={current_user.id}, "
        f"days_back={request.days_back}"
    )

    try:
        refund_service = EbayRefundService(db, current_user.id)

        stats = refund_service.sync_refunds_from_recent_orders(
            days_back=request.days_back
        )

        logger.info(
            f"[POST /refunds/sync] Completed: user_id={current_user.id}, "
            f"created={stats['created']}, updated={stats['updated']}, "
            f"skipped={stats['skipped']}, errors={stats['errors']}"
        )

        return SyncRefundsResponse(**stats)

    except ValueError as e:
        logger.error(
            f"[POST /refunds/sync] Validation error for user {current_user.id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(
            f"[POST /refunds/sync] Sync failed for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync operation failed: {str(e)}",
        )


@router.post("/refunds/sync-order", response_model=SyncRefundsResponse)
async def sync_refunds_from_order(
    request: SyncRefundsFromOrderRequest,
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    Synchronize refunds from a specific eBay order.

    **Workflow:**
    1. Fetch order details from eBay
    2. Extract refunds from order payment summary
    3. Create or update refunds in local DB
    4. Return statistics

    **Example:**
    ```bash
    curl -X POST "http://localhost:8000/api/ebay/refunds/sync-order" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{"order_id": "12-34567-89012"}'
    ```

    Args:
        request: Sync request with order_id
        db_user: DB session and authenticated user

    Returns:
        Statistics about sync operation

    Raises:
        400: Invalid order_id
        500: Sync operation failed
    """
    db, current_user = db_user

    logger.info(
        f"[POST /refunds/sync-order] user_id={current_user.id}, "
        f"order_id={request.order_id}"
    )

    try:
        refund_service = EbayRefundService(db, current_user.id)

        stats = refund_service.sync_refunds_from_order(order_id=request.order_id)

        logger.info(
            f"[POST /refunds/sync-order] Completed: user_id={current_user.id}, "
            f"order_id={request.order_id}, created={stats['created']}, "
            f"updated={stats['updated']}, skipped={stats['skipped']}"
        )

        return SyncRefundsResponse(**stats)

    except ValueError as e:
        logger.error(
            f"[POST /refunds/sync-order] Validation error for user {current_user.id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(
            f"[POST /refunds/sync-order] Sync failed for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync operation failed: {str(e)}",
        )


# =============================================================================
# LIST & GET ENDPOINTS
# =============================================================================


@router.get("/refunds", response_model=RefundListResponse)
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
    order_id: Optional[str] = Query(
        None,
        description="Filter by eBay order ID",
    ),
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    List eBay refunds with pagination and filters.

    **Features:**
    - Pagination (default: 50 items per page, max 200)
    - Filter by status (PENDING, REFUNDED, FAILED)
    - Filter by source (RETURN, CANCELLATION, MANUAL, OTHER)
    - Filter by order ID
    - Sorted by refund date (newest first)

    **Example:**
    ```bash
    # List all refunds
    curl "http://localhost:8000/api/ebay/refunds" \\
      -H "Authorization: Bearer YOUR_TOKEN"

    # Filter by status
    curl "http://localhost:8000/api/ebay/refunds?status=PENDING" \\
      -H "Authorization: Bearer YOUR_TOKEN"

    # Filter by source
    curl "http://localhost:8000/api/ebay/refunds?source=RETURN" \\
      -H "Authorization: Bearer YOUR_TOKEN"

    # Filter by order
    curl "http://localhost:8000/api/ebay/refunds?order_id=12-34567-89012" \\
      -H "Authorization: Bearer YOUR_TOKEN"
    ```

    Args:
        page: Page number (1-indexed)
        page_size: Items per page (1-200)
        status_filter: Optional status filter
        source: Optional source filter
        order_id: Optional order ID filter
        db_user: DB session and authenticated user

    Returns:
        Paginated list of refunds

    Raises:
        400: Invalid query parameters
    """
    db, current_user = db_user

    logger.debug(
        f"[GET /refunds] user_id={current_user.id}, page={page}, "
        f"page_size={page_size}, status={status_filter}, source={source}"
    )

    try:
        refund_service = EbayRefundService(db, current_user.id)

        result = refund_service.list_refunds(
            page=page,
            page_size=page_size,
            status=status_filter,
            source=source,
            order_id=order_id,
        )

        items = [EbayRefundResponse.model_validate(r) for r in result["items"]]

        logger.debug(
            f"[GET /refunds] Returned {len(items)} refunds for user {current_user.id} "
            f"(page {page}/{result['total_pages']})"
        )

        return RefundListResponse(
            items=items,
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"],
        )

    except Exception as e:
        logger.error(
            f"[GET /refunds] Failed for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list refunds: {str(e)}",
        )


@router.get("/refunds/statistics", response_model=RefundStatisticsResponse)
def get_refund_statistics(
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    Get refund statistics.

    **Returns:**
    - pending: Number of pending refunds
    - completed: Number of completed refunds
    - failed: Number of failed refunds
    - total_refunded: Total amount refunded
    - by_source: Breakdown by refund source

    **Example:**
    ```bash
    curl "http://localhost:8000/api/ebay/refunds/statistics" \\
      -H "Authorization: Bearer YOUR_TOKEN"
    ```

    Args:
        db_user: DB session and authenticated user

    Returns:
        Refund statistics
    """
    db, current_user = db_user

    logger.debug(f"[GET /refunds/statistics] user_id={current_user.id}")

    try:
        refund_service = EbayRefundService(db, current_user.id)
        stats = refund_service.get_statistics()

        return RefundStatisticsResponse(
            pending=stats["pending"],
            completed=stats["completed"],
            failed=stats["failed"],
            total_refunded=stats["total_refunded"],
            by_source=stats["by_source"],
        )

    except Exception as e:
        logger.error(
            f"[GET /refunds/statistics] Failed for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}",
        )


@router.get("/refunds/pending", response_model=RefundListResponse)
def list_pending_refunds(
    limit: int = Query(100, ge=1, le=200, description="Max results"),
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    List pending refunds.

    **Example:**
    ```bash
    curl "http://localhost:8000/api/ebay/refunds/pending" \\
      -H "Authorization: Bearer YOUR_TOKEN"
    ```

    Args:
        limit: Max results (default 100)
        db_user: DB session and authenticated user

    Returns:
        List of pending refunds
    """
    db, current_user = db_user

    logger.debug(f"[GET /refunds/pending] user_id={current_user.id}")

    try:
        refund_service = EbayRefundService(db, current_user.id)
        refunds = refund_service.list_pending_refunds(limit=limit)

        items = [EbayRefundResponse.model_validate(r) for r in refunds]

        return RefundListResponse(
            items=items,
            total=len(items),
            page=1,
            page_size=limit,
            total_pages=1,
        )

    except Exception as e:
        logger.error(
            f"[GET /refunds/pending] Failed for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list pending refunds: {str(e)}",
        )


@router.get("/refunds/failed", response_model=RefundListResponse)
def list_failed_refunds(
    limit: int = Query(100, ge=1, le=200, description="Max results"),
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    List failed refunds.

    **Example:**
    ```bash
    curl "http://localhost:8000/api/ebay/refunds/failed" \\
      -H "Authorization: Bearer YOUR_TOKEN"
    ```

    Args:
        limit: Max results (default 100)
        db_user: DB session and authenticated user

    Returns:
        List of failed refunds
    """
    db, current_user = db_user

    logger.debug(f"[GET /refunds/failed] user_id={current_user.id}")

    try:
        refund_service = EbayRefundService(db, current_user.id)
        refunds = refund_service.list_failed_refunds(limit=limit)

        items = [EbayRefundResponse.model_validate(r) for r in refunds]

        return RefundListResponse(
            items=items,
            total=len(items),
            page=1,
            page_size=limit,
            total_pages=1,
        )

    except Exception as e:
        logger.error(
            f"[GET /refunds/failed] Failed for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list failed refunds: {str(e)}",
        )


@router.get("/refunds/{refund_id}", response_model=EbayRefundResponse)
def get_refund(
    refund_id: int,
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    Get detailed information about a specific refund.

    **Example:**
    ```bash
    curl "http://localhost:8000/api/ebay/refunds/123" \\
      -H "Authorization: Bearer YOUR_TOKEN"
    ```

    Args:
        refund_id: Internal refund ID
        db_user: DB session and authenticated user

    Returns:
        Refund details

    Raises:
        404: Refund not found
    """
    db, current_user = db_user

    logger.debug(f"[GET /refunds/{refund_id}] user_id={current_user.id}")

    try:
        refund_service = EbayRefundService(db, current_user.id)
        refund = refund_service.get_refund_by_id(refund_id)

        if not refund:
            logger.warning(
                f"[GET /refunds/{refund_id}] Not found for user {current_user.id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Refund {refund_id} not found",
            )

        return EbayRefundResponse.model_validate(refund)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"[GET /refunds/{refund_id}] Failed for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get refund: {str(e)}",
        )


# =============================================================================
# ACTION ENDPOINTS
# =============================================================================


@router.post("/refunds/issue", response_model=IssueRefundResponse)
def issue_refund(
    request: IssueRefundRequest,
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    Issue a new refund for an eBay order.

    **Workflow:**
    1. Call eBay Fulfillment API to issue refund
    2. Create refund record in local DB
    3. Return result with refund_id

    **Valid reasons:**
    - BUYER_CANCEL: Buyer cancelled the order
    - BUYER_RETURN: Buyer returned the item
    - ITEM_NOT_RECEIVED: Item was not received
    - SELLER_WRONG_ITEM: Wrong item sent
    - SELLER_OUT_OF_STOCK: Item out of stock
    - SELLER_FOUND_ISSUE: Seller found issue with item
    - OTHER: Other reason

    **Example:**
    ```bash
    # Full refund
    curl -X POST "http://localhost:8000/api/ebay/refunds/issue" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{
        "order_id": "12-34567-89012",
        "reason": "BUYER_CANCEL",
        "amount": 29.99,
        "currency": "EUR",
        "comment": "Refund at buyer request"
      }'

    # Partial refund for specific item
    curl -X POST "http://localhost:8000/api/ebay/refunds/issue" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{
        "order_id": "12-34567-89012",
        "reason": "SELLER_WRONG_ITEM",
        "amount": 15.00,
        "currency": "EUR",
        "line_item_id": "12-34567-89012-1",
        "comment": "Partial refund for wrong item"
      }'
    ```

    Args:
        request: Issue refund request
        db_user: DB session and authenticated user

    Returns:
        Issue refund result

    Raises:
        400: Invalid request (invalid amount, reason, etc.)
        500: eBay API call failed
    """
    db, current_user = db_user

    logger.info(
        f"[POST /refunds/issue] user_id={current_user.id}, "
        f"order_id={request.order_id}, reason={request.reason}, "
        f"amount={request.amount} {request.currency}"
    )

    try:
        refund_service = EbayRefundService(db, current_user.id)

        result = refund_service.issue_refund(
            order_id=request.order_id,
            reason=request.reason,
            amount=request.amount,
            currency=request.currency,
            line_item_id=request.line_item_id,
            comment=request.comment,
        )

        if result["success"]:
            logger.info(
                f"[POST /refunds/issue] Success: user_id={current_user.id}, "
                f"refund_id={result['refund_id']}, status={result['refund_status']}"
            )
        else:
            logger.warning(
                f"[POST /refunds/issue] Failed: user_id={current_user.id}, "
                f"message={result['message']}"
            )

        return IssueRefundResponse(**result)

    except ValueError as e:
        logger.warning(f"[POST /refunds/issue] Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(
            f"[POST /refunds/issue] Failed for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to issue refund: {str(e)}",
        )
