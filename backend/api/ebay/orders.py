"""
API Routes eBay Orders.

Endpoints pour la gestion complète des commandes eBay avec synchronisation DB locale.

Fonctionnalités:
- Synchronisation depuis eBay Fulfillment API
- Liste avec pagination et filtres
- Détails d'une commande
- Mise à jour du statut de fulfillment
- Ajout de tracking

Architecture:
- Repository pour accès données
- Services pour logique métier
- DB locale pour cache et historique

Author: Claude
Date: 2026-01-07
"""

from datetime import datetime
from typing import Optional, Tuple

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.dependencies import get_user_db
from models.public.user import User
from repositories.ebay_order_repository import EbayOrderRepository
from schemas.ebay_order_schemas import (
    AddTrackingRequest,
    AddTrackingResponse,
    EbayOrderDetailResponse,
    OrderListResponse,
    SyncOrdersRequest,
    SyncOrdersResponse,
    UpdateFulfillmentRequest,
)
from services.ebay.ebay_order_fulfillment_service import (
    EbayOrderFulfillmentService,
)
from services.ebay.ebay_order_sync_service import EbayOrderSyncService
from shared.logging_setup import get_logger

logger = get_logger(__name__)

router = APIRouter()


# =============================================================================
# SYNC ENDPOINT
# =============================================================================


@router.post("/orders/sync", response_model=SyncOrdersResponse)
async def sync_orders(
    request: SyncOrdersRequest = Body(default=SyncOrdersRequest()),
    process_now: bool = Query(True, description="Exécuter immédiatement ou créer job uniquement"),
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    Synchronize orders from eBay Fulfillment API to local database.

    **Workflow:**
    1. Create a marketplace job for tracking
    2. If process_now=True (default), execute immediately
    3. Return statistics (created, updated, errors)

    **Default behavior:**
    - Syncs orders modified in the last 24 hours
    - All fulfillment statuses (NOT_STARTED, IN_PROGRESS, FULFILLED)
    - Executes immediately (process_now=True)

    **Request Body:**
    ```json
    {
        "hours": 24,
        "status_filter": null
    }
    ```

    **Query Parameters:**
    - process_now: bool (default: True) - Execute immediately or queue for later

    **Example:**
    ```bash
    # Sync last 24 hours (immediate execution)
    curl -X POST "http://localhost:8000/api/ebay/orders/sync?process_now=true" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{}'

    # Create job without executing (for batch processing)
    curl -X POST "http://localhost:8000/api/ebay/orders/sync?process_now=false" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{"hours": 168}'
    ```

    Args:
        request: Sync request with hours and optional status filter
        process_now: Execute immediately or create job only
        db_user: DB session and authenticated user

    Returns:
        Statistics about sync operation (created, updated, errors)

    Raises:
        400: Invalid request parameters
        500: Sync operation failed
    """
    db, current_user = db_user

    logger.info(
        f"[POST /orders/sync] user_id={current_user.id}, "
        f"hours={request.hours}, status_filter={request.status_filter}, "
        f"process_now={process_now}"
    )

    try:
        # Create marketplace job for tracking
        from services.marketplace.marketplace_job_service import MarketplaceJobService
        job_service = MarketplaceJobService(db)

        job = job_service.create_job(
            marketplace="ebay",
            action_code="sync_orders_ebay",
            product_id=None,  # Operation-level job (not product-specific)
            input_data={
                "hours": request.hours,
                "status_filter": request.status_filter
            },
        )
        db.commit()

        logger.info(
            f"[POST /orders/sync] Created job #{job.id} for user {current_user.id}"
        )

        # Execute immediately if requested
        if process_now:
            from services.marketplace.marketplace_job_processor import MarketplaceJobProcessor
            processor = MarketplaceJobProcessor(db, user_id=current_user.id, shop_id=current_user.id, marketplace="ebay")
            result = await processor._execute_job(job)

            if result.get("success"):
                job_result = result.get("result", {})
                stats = {
                    "created": job_result.get("created", 0),
                    "updated": job_result.get("updated", 0),
                    "skipped": job_result.get("skipped", 0),
                    "errors": job_result.get("errors", 0),
                    "total_fetched": job_result.get("total_fetched", 0),
                    "details": job_result.get("details", [])
                }

                logger.info(
                    f"[POST /orders/sync] Job #{job.id} completed: "
                    f"created={stats['created']}, updated={stats['updated']}, "
                    f"errors={stats['errors']}"
                )

                return SyncOrdersResponse(**stats)
            else:
                error = result.get("error", "Job execution failed")
                logger.error(
                    f"[POST /orders/sync] Job #{job.id} failed: {error}"
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Sync job failed: {error}",
                )
        else:
            # Job created but not executed yet
            logger.info(
                f"[POST /orders/sync] Job #{job.id} queued for later processing"
            )
            return SyncOrdersResponse(
                created=0,
                updated=0,
                skipped=0,
                errors=0,
                total_fetched=0,
                details=[]
            )

    except ValueError as e:
        logger.error(
            f"[POST /orders/sync] Validation error for user {current_user.id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(
            f"[POST /orders/sync] Sync failed for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync operation failed: {str(e)}",
        )


# =============================================================================
# LIST & GET ENDPOINTS
# =============================================================================


@router.get("/orders", response_model=OrderListResponse)
def list_orders(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    status: Optional[str] = Query(
        None,
        description="Filter by fulfillment status (NOT_STARTED, IN_PROGRESS, FULFILLED)",
    ),
    marketplace_id: Optional[str] = Query(
        None, description="Filter by marketplace (EBAY_FR, EBAY_GB, etc.)"
    ),
    date_from: Optional[datetime] = Query(
        None, description="Filter orders created after this date (ISO 8601)"
    ),
    date_to: Optional[datetime] = Query(
        None, description="Filter orders created before this date (ISO 8601)"
    ),
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    List eBay orders with pagination and filters.

    **Features:**
    - Pagination (default: 50 items per page, max 200)
    - Filter by fulfillment status
    - Filter by marketplace
    - Filter by date range
    - Orders sorted by creation date (newest first)

    **Example:**
    ```bash
    # List all orders (page 1)
    curl "http://localhost:8000/api/ebay/orders" \\
      -H "Authorization: Bearer YOUR_TOKEN"

    # Filter by status
    curl "http://localhost:8000/api/ebay/orders?status=NOT_STARTED" \\
      -H "Authorization: Bearer YOUR_TOKEN"

    # Filter by marketplace and date
    curl "http://localhost:8000/api/ebay/orders?marketplace_id=EBAY_FR&date_from=2024-12-01T00:00:00Z" \\
      -H "Authorization: Bearer YOUR_TOKEN"

    # Pagination
    curl "http://localhost:8000/api/ebay/orders?page=2&page_size=20" \\
      -H "Authorization: Bearer YOUR_TOKEN"
    ```

    Args:
        page: Page number (1-indexed)
        page_size: Items per page (1-200)
        status: Optional fulfillment status filter
        marketplace_id: Optional marketplace filter
        date_from: Optional start date filter
        date_to: Optional end date filter
        db_user: DB session and authenticated user

    Returns:
        Paginated list of orders with total count and page info

    Raises:
        400: Invalid query parameters
    """
    db, current_user = db_user

    logger.debug(
        f"[GET /orders] user_id={current_user.id}, page={page}, "
        f"page_size={page_size}, status={status}, marketplace_id={marketplace_id}"
    )

    try:
        # Calculate skip for pagination
        skip = (page - 1) * page_size

        # Query orders with filters
        orders, total = EbayOrderRepository.list_orders(
            db=db,
            skip=skip,
            limit=page_size,
            marketplace_id=marketplace_id,
            fulfillment_status=status,
            date_from=date_from,
            date_to=date_to,
        )

        # Calculate total pages
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        # Convert to response models
        items = [EbayOrderDetailResponse.model_validate(order) for order in orders]

        logger.debug(
            f"[GET /orders] Returned {len(items)} orders for user {current_user.id} "
            f"(page {page}/{total_pages})"
        )

        return OrderListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    except Exception as e:
        logger.error(
            f"[GET /orders] Failed to list orders for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list orders: {str(e)}",
        )


@router.get("/orders/{order_id}", response_model=EbayOrderDetailResponse)
def get_order(
    order_id: int,
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    Get detailed information about a specific order.

    **Returns:**
    - Complete order information
    - Buyer details
    - Shipping address
    - Pricing breakdown
    - All line items (products)
    - Fulfillment and payment status
    - Tracking information (if added)

    **Example:**
    ```bash
    curl "http://localhost:8000/api/ebay/orders/123" \\
      -H "Authorization: Bearer YOUR_TOKEN"
    ```

    Args:
        order_id: Internal order ID
        db_user: DB session and authenticated user

    Returns:
        Complete order details with nested products

    Raises:
        404: Order not found
    """
    db, current_user = db_user

    logger.debug(f"[GET /orders/{order_id}] user_id={current_user.id}")

    try:
        # Get order by internal ID
        order = EbayOrderRepository.get_by_id(db, order_id)

        if not order:
            logger.warning(
                f"[GET /orders/{order_id}] Order not found for user {current_user.id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order {order_id} not found",
            )

        # Convert to response model
        response = EbayOrderDetailResponse.model_validate(order)

        logger.debug(
            f"[GET /orders/{order_id}] Returned order {order.order_id} "
            f"for user {current_user.id}"
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"[GET /orders/{order_id}] Failed for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get order: {str(e)}",
        )


# =============================================================================
# FULFILLMENT & TRACKING ENDPOINTS
# =============================================================================


@router.patch("/orders/{order_id}/fulfillment", response_model=EbayOrderDetailResponse)
def update_fulfillment(
    order_id: int,
    request: UpdateFulfillmentRequest,
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    Update order fulfillment status (local DB only).

    **Status transitions:**
    - NOT_STARTED → IN_PROGRESS
    - IN_PROGRESS → FULFILLED
    - FULFILLED → (immutable)

    **Note:** This only updates the local database. It does NOT call eBay API.
    Use the tracking endpoint to update eBay's fulfillment status.

    **Example:**
    ```bash
    curl -X PATCH "http://localhost:8000/api/ebay/orders/123/fulfillment" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{"new_status": "IN_PROGRESS"}'
    ```

    Args:
        order_id: Internal order ID
        request: Update request with new status
        db_user: DB session and authenticated user

    Returns:
        Updated order details

    Raises:
        400: Invalid status value
        404: Order not found
    """
    db, current_user = db_user

    logger.info(
        f"[PATCH /orders/{order_id}/fulfillment] user_id={current_user.id}, "
        f"new_status={request.new_status}"
    )

    try:
        # Initialize fulfillment service
        fulfillment_service = EbayOrderFulfillmentService(db, current_user.id)

        # Update fulfillment status
        updated_order = fulfillment_service.update_fulfillment_status(
            order_id=order_id,
            new_status=request.new_status,
        )

        logger.info(
            f"[PATCH /orders/{order_id}/fulfillment] Updated order {updated_order.order_id} "
            f"status to {request.new_status}"
        )

        return EbayOrderDetailResponse.model_validate(updated_order)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"[PATCH /orders/{order_id}/fulfillment] Failed for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update fulfillment status: {str(e)}",
        )


@router.post("/orders/{order_id}/tracking", response_model=AddTrackingResponse)
def add_tracking(
    order_id: int,
    request: AddTrackingRequest,
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    Add tracking information to order (calls eBay API + updates DB).

    **Workflow:**
    1. Validate order exists and is PAID
    2. Call eBay API: POST /order/{orderId}/shipping_fulfillment
    3. Update local DB with tracking info

    **Important:**
    - Order must have status "PAID" to add tracking
    - Tracking number must be alphanumeric only (no spaces, dashes, special chars)
    - This will mark the order as shipped on eBay

    **Example:**
    ```bash
    curl -X POST "http://localhost:8000/api/ebay/orders/123/tracking" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{
        "tracking_number": "1234567890",
        "carrier_code": "COLISSIMO",
        "shipped_date": "2024-12-10T10:00:00Z"
      }'
    ```

    Args:
        order_id: Internal order ID
        request: Tracking information (number, carrier, date)
        db_user: DB session and authenticated user

    Returns:
        Success response with fulfillment ID from eBay

    Raises:
        400: Order not paid or invalid tracking number
        404: Order not found
        500: eBay API call failed
    """
    db, current_user = db_user

    logger.info(
        f"[POST /orders/{order_id}/tracking] user_id={current_user.id}, "
        f"tracking_number={request.tracking_number}, carrier={request.carrier_code}"
    )

    try:
        # Initialize fulfillment service
        fulfillment_service = EbayOrderFulfillmentService(db, current_user.id)

        # Add tracking (calls eBay API + updates DB)
        result = fulfillment_service.add_tracking(
            order_id=order_id,
            tracking_number=request.tracking_number,
            carrier_code=request.carrier_code,
            shipped_date=request.shipped_date,
        )

        logger.info(
            f"[POST /orders/{order_id}/tracking] Tracking added successfully: "
            f"fulfillment_id={result['fulfillment_id']}"
        )

        return AddTrackingResponse(**result)

    except ValueError as e:
        logger.warning(
            f"[POST /orders/{order_id}/tracking] Validation error: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except RuntimeError as e:
        logger.error(
            f"[POST /orders/{order_id}/tracking] eBay API error: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"[POST /orders/{order_id}/tracking] Failed for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add tracking: {str(e)}",
        )
