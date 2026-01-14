"""
API Routes eBay Payment Disputes.

Endpoints for eBay payment dispute management.

Features:
- Synchronization from eBay Fulfillment API
- List with pagination and filters
- Dispute details
- Accept disputes (concede to buyer)
- Contest disputes (fight buyer's claim)
- Add evidence before contesting
- Statistics and urgent alerts

Architecture:
- Repository for data access
- Service for business logic
- Local DB for cache and history

Documentation:
- https://developer.ebay.com/api-docs/sell/fulfillment/resources/payment_dispute/

Author: Claude
Date: 2026-01-14
"""

from typing import Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.dependencies import get_user_db
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
    SyncDisputeRequest,
    SyncDisputesRequest,
    SyncDisputesResponse,
    UrgentDisputeResponse,
)
from services.ebay.ebay_payment_dispute_service import EbayPaymentDisputeService
from shared.logging_setup import get_logger

logger = get_logger(__name__)

router = APIRouter()


# =============================================================================
# SYNC ENDPOINTS
# =============================================================================


@router.post("/payment-disputes/sync", response_model=SyncDisputesResponse)
async def sync_disputes(
    request: SyncDisputesRequest = None,
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    Synchronize payment disputes from eBay API to local database.

    **Workflow:**
    1. Fetch disputes from the last N days (default: 90, max: 90)
    2. Create or update disputes in local DB
    3. Return statistics (created, updated, total_fetched, errors)

    **Default behavior:**
    - Syncs disputes opened in the last 90 days

    **Request Body:**
    ```json
    {
        "days_back": 90
    }
    ```

    **Example:**
    ```bash
    # Sync last 90 days
    curl -X POST "http://localhost:8000/api/ebay/payment-disputes/sync" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{}'

    # Sync last 30 days
    curl -X POST "http://localhost:8000/api/ebay/payment-disputes/sync" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{"days_back": 30}'
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
        request = SyncDisputesRequest()

    logger.info(
        f"[POST /payment-disputes/sync] user_id={current_user.id}, "
        f"days_back={request.days_back}"
    )

    try:
        service = EbayPaymentDisputeService(db, current_user.id)

        stats = service.sync_disputes(days_back=request.days_back)

        logger.info(
            f"[POST /payment-disputes/sync] Completed: user_id={current_user.id}, "
            f"fetched={stats['total_fetched']}, created={stats['created']}, "
            f"updated={stats['updated']}, errors={stats['errors']}"
        )

        return SyncDisputesResponse(**stats)

    except ValueError as e:
        logger.error(
            f"[POST /payment-disputes/sync] Validation error for user {current_user.id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(
            f"[POST /payment-disputes/sync] Sync failed for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync operation failed: {str(e)}",
        )


@router.post(
    "/payment-disputes/sync/{payment_dispute_id}",
    response_model=EbayPaymentDisputeResponse,
)
async def sync_single_dispute(
    payment_dispute_id: str,
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    Synchronize a single payment dispute from eBay API.

    **Workflow:**
    1. Fetch dispute details from eBay
    2. Create or update in local DB
    3. Return updated dispute

    **Example:**
    ```bash
    curl -X POST "http://localhost:8000/api/ebay/payment-disputes/sync/5********0" \\
      -H "Authorization: Bearer YOUR_TOKEN"
    ```

    Args:
        payment_dispute_id: eBay payment dispute ID
        db_user: DB session and authenticated user

    Returns:
        Updated dispute details

    Raises:
        404: Dispute not found on eBay
        500: Sync operation failed
    """
    db, current_user = db_user

    logger.info(
        f"[POST /payment-disputes/sync/{payment_dispute_id}] "
        f"user_id={current_user.id}"
    )

    try:
        service = EbayPaymentDisputeService(db, current_user.id)

        dispute = service.sync_dispute(payment_dispute_id)

        if not dispute:
            logger.warning(
                f"[POST /payment-disputes/sync/{payment_dispute_id}] "
                f"Not found for user {current_user.id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dispute {payment_dispute_id} not found",
            )

        logger.info(
            f"[POST /payment-disputes/sync/{payment_dispute_id}] "
            f"Synced for user {current_user.id}"
        )

        return EbayPaymentDisputeResponse.model_validate(dispute)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"[POST /payment-disputes/sync/{payment_dispute_id}] "
            f"Failed for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync operation failed: {str(e)}",
        )


# =============================================================================
# LIST & GET ENDPOINTS
# =============================================================================


@router.get("/payment-disputes", response_model=DisputeListResponse)
def list_disputes(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    state: Optional[str] = Query(
        None,
        pattern="^(OPEN|ACTION_NEEDED|CLOSED)$",
        description="Filter by dispute state",
    ),
    reason: Optional[str] = Query(
        None,
        description="Filter by dispute reason",
    ),
    order_id: Optional[str] = Query(
        None,
        description="Filter by eBay order ID",
    ),
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    List eBay payment disputes with pagination and filters.

    **Features:**
    - Pagination (default: 50 items per page, max 200)
    - Filter by state (OPEN, ACTION_NEEDED, CLOSED)
    - Filter by reason (ITEM_NOT_RECEIVED, FRAUD, etc.)
    - Filter by order ID
    - Sorted by open date (newest first)

    **Example:**
    ```bash
    # List all disputes
    curl "http://localhost:8000/api/ebay/payment-disputes" \\
      -H "Authorization: Bearer YOUR_TOKEN"

    # Filter by state
    curl "http://localhost:8000/api/ebay/payment-disputes?state=ACTION_NEEDED" \\
      -H "Authorization: Bearer YOUR_TOKEN"

    # Filter by reason
    curl "http://localhost:8000/api/ebay/payment-disputes?reason=ITEM_NOT_RECEIVED" \\
      -H "Authorization: Bearer YOUR_TOKEN"
    ```

    Args:
        page: Page number (1-indexed)
        page_size: Items per page (1-200)
        state: Optional state filter
        reason: Optional reason filter
        order_id: Optional order ID filter
        db_user: DB session and authenticated user

    Returns:
        Paginated list of disputes

    Raises:
        400: Invalid query parameters
    """
    db, current_user = db_user

    logger.debug(
        f"[GET /payment-disputes] user_id={current_user.id}, page={page}, "
        f"page_size={page_size}, state={state}, reason={reason}"
    )

    try:
        service = EbayPaymentDisputeService(db, current_user.id)

        result = service.list_disputes(
            page=page,
            page_size=page_size,
            state=state,
            reason=reason,
            order_id=order_id,
        )

        items = [
            EbayPaymentDisputeResponse.model_validate(d) for d in result["items"]
        ]

        logger.debug(
            f"[GET /payment-disputes] Returned {len(items)} disputes for user "
            f"{current_user.id} (page {page}/{result['total_pages']})"
        )

        return DisputeListResponse(
            items=items,
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"],
        )

    except Exception as e:
        logger.error(
            f"[GET /payment-disputes] Failed for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list disputes: {str(e)}",
        )


@router.get("/payment-disputes/statistics", response_model=DisputeStatisticsResponse)
def get_dispute_statistics(
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    Get payment dispute statistics.

    **Returns:**
    - open: Number of open disputes
    - action_needed: Number of disputes requiring action
    - closed: Number of closed disputes
    - past_deadline: Number past response deadline
    - total_amount: Total amount in dispute (open disputes)
    - by_reason: Breakdown by dispute reason

    **Example:**
    ```bash
    curl "http://localhost:8000/api/ebay/payment-disputes/statistics" \\
      -H "Authorization: Bearer YOUR_TOKEN"
    ```

    Args:
        db_user: DB session and authenticated user

    Returns:
        Dispute statistics
    """
    db, current_user = db_user

    logger.debug(f"[GET /payment-disputes/statistics] user_id={current_user.id}")

    try:
        service = EbayPaymentDisputeService(db, current_user.id)
        stats = service.get_statistics()

        return DisputeStatisticsResponse(
            open=stats["open"],
            action_needed=stats["action_needed"],
            closed=stats["closed"],
            past_deadline=stats["past_deadline"],
            total_amount=stats["total_amount"],
            by_reason=stats["by_reason"],
        )

    except Exception as e:
        logger.error(
            f"[GET /payment-disputes/statistics] Failed for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}",
        )


@router.get("/payment-disputes/urgent", response_model=UrgentDisputeResponse)
def list_urgent_disputes(
    days_threshold: int = Query(
        3, ge=1, le=14, description="Days until deadline to consider urgent"
    ),
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    List urgent payment disputes requiring immediate attention.

    **Returns disputes that:**
    - Are ACTION_NEEDED and deadline is within N days
    - Are past deadline but not closed

    **Example:**
    ```bash
    # Get disputes due within 3 days
    curl "http://localhost:8000/api/ebay/payment-disputes/urgent" \\
      -H "Authorization: Bearer YOUR_TOKEN"

    # Get disputes due within 7 days
    curl "http://localhost:8000/api/ebay/payment-disputes/urgent?days_threshold=7" \\
      -H "Authorization: Bearer YOUR_TOKEN"
    ```

    Args:
        days_threshold: Number of days to consider urgent (default: 3)
        db_user: DB session and authenticated user

    Returns:
        List of urgent disputes
    """
    db, current_user = db_user

    logger.debug(
        f"[GET /payment-disputes/urgent] user_id={current_user.id}, "
        f"days_threshold={days_threshold}"
    )

    try:
        service = EbayPaymentDisputeService(db, current_user.id)
        disputes = service.get_urgent_disputes(days_threshold=days_threshold)

        items = [EbayPaymentDisputeResponse.model_validate(d) for d in disputes]

        return UrgentDisputeResponse(
            disputes=items,
            count=len(items),
        )

    except Exception as e:
        logger.error(
            f"[GET /payment-disputes/urgent] Failed for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list urgent disputes: {str(e)}",
        )


@router.get("/payment-disputes/action-needed", response_model=DisputeListResponse)
def list_action_needed_disputes(
    limit: int = Query(100, ge=1, le=200, description="Max results"),
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    List disputes requiring seller action.

    **Example:**
    ```bash
    curl "http://localhost:8000/api/ebay/payment-disputes/action-needed" \\
      -H "Authorization: Bearer YOUR_TOKEN"
    ```

    Args:
        limit: Max results (default 100)
        db_user: DB session and authenticated user

    Returns:
        List of disputes needing action
    """
    db, current_user = db_user

    logger.debug(
        f"[GET /payment-disputes/action-needed] user_id={current_user.id}"
    )

    try:
        service = EbayPaymentDisputeService(db, current_user.id)
        disputes = service.get_action_needed_disputes(limit=limit)

        items = [EbayPaymentDisputeResponse.model_validate(d) for d in disputes]

        return DisputeListResponse(
            items=items,
            total=len(items),
            page=1,
            page_size=limit,
            total_pages=1,
        )

    except Exception as e:
        logger.error(
            f"[GET /payment-disputes/action-needed] Failed for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list action-needed disputes: {str(e)}",
        )


@router.get("/payment-disputes/open", response_model=DisputeListResponse)
def list_open_disputes(
    limit: int = Query(100, ge=1, le=200, description="Max results"),
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    List open disputes (OPEN or ACTION_NEEDED).

    **Example:**
    ```bash
    curl "http://localhost:8000/api/ebay/payment-disputes/open" \\
      -H "Authorization: Bearer YOUR_TOKEN"
    ```

    Args:
        limit: Max results (default 100)
        db_user: DB session and authenticated user

    Returns:
        List of open disputes
    """
    db, current_user = db_user

    logger.debug(f"[GET /payment-disputes/open] user_id={current_user.id}")

    try:
        service = EbayPaymentDisputeService(db, current_user.id)
        disputes = service.get_open_disputes(limit=limit)

        items = [EbayPaymentDisputeResponse.model_validate(d) for d in disputes]

        return DisputeListResponse(
            items=items,
            total=len(items),
            page=1,
            page_size=limit,
            total_pages=1,
        )

    except Exception as e:
        logger.error(
            f"[GET /payment-disputes/open] Failed for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list open disputes: {str(e)}",
        )


@router.get(
    "/payment-disputes/{payment_dispute_id}",
    response_model=EbayPaymentDisputeResponse,
)
def get_dispute(
    payment_dispute_id: str,
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    Get detailed information about a specific payment dispute.

    **Example:**
    ```bash
    curl "http://localhost:8000/api/ebay/payment-disputes/5********0" \\
      -H "Authorization: Bearer YOUR_TOKEN"
    ```

    Args:
        payment_dispute_id: eBay payment dispute ID
        db_user: DB session and authenticated user

    Returns:
        Dispute details

    Raises:
        404: Dispute not found
    """
    db, current_user = db_user

    logger.debug(
        f"[GET /payment-disputes/{payment_dispute_id}] user_id={current_user.id}"
    )

    try:
        service = EbayPaymentDisputeService(db, current_user.id)
        dispute = service.get_dispute(payment_dispute_id)

        if not dispute:
            logger.warning(
                f"[GET /payment-disputes/{payment_dispute_id}] "
                f"Not found for user {current_user.id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dispute {payment_dispute_id} not found",
            )

        return EbayPaymentDisputeResponse.model_validate(dispute)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"[GET /payment-disputes/{payment_dispute_id}] "
            f"Failed for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dispute: {str(e)}",
        )


# =============================================================================
# ACTION ENDPOINTS
# =============================================================================


@router.post(
    "/payment-disputes/{payment_dispute_id}/accept",
    response_model=DisputeActionResponse,
)
def accept_dispute(
    payment_dispute_id: str,
    request: AcceptDisputeRequest = None,
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    Accept a payment dispute (concede to buyer).

    **Effect:**
    - Seller agrees the buyer's claim is valid
    - A refund will be issued to the buyer
    - Dispute will be closed

    **When to accept:**
    - Buyer claim is legitimate
    - Evidence doesn't support seller's case
    - Cost of fighting exceeds dispute amount

    **Example:**
    ```bash
    # Accept dispute
    curl -X POST "http://localhost:8000/api/ebay/payment-disputes/5********0/accept" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{}'

    # Accept with return address
    curl -X POST "http://localhost:8000/api/ebay/payment-disputes/5********0/accept" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{
        "return_address": {
          "addressLine1": "123 Main St",
          "city": "Paris",
          "postalCode": "75001",
          "countryCode": "FR"
        }
      }'
    ```

    Args:
        payment_dispute_id: eBay payment dispute ID
        request: Optional return address
        db_user: DB session and authenticated user

    Returns:
        Accept result with updated dispute

    Raises:
        400: Dispute cannot be accepted (closed or ACCEPT not available)
        404: Dispute not found
        500: eBay API call failed
    """
    db, current_user = db_user

    logger.info(
        f"[POST /payment-disputes/{payment_dispute_id}/accept] "
        f"user_id={current_user.id}"
    )

    return_address = None
    if request and request.return_address:
        return_address = request.return_address

    try:
        service = EbayPaymentDisputeService(db, current_user.id)

        result = service.accept_dispute(
            payment_dispute_id=payment_dispute_id,
            return_address=return_address,
        )

        if result["success"]:
            logger.info(
                f"[POST /payment-disputes/{payment_dispute_id}/accept] "
                f"Success for user {current_user.id}"
            )
        else:
            logger.warning(
                f"[POST /payment-disputes/{payment_dispute_id}/accept] "
                f"Failed for user {current_user.id}: {result['message']}"
            )

        dispute_response = None
        if result.get("dispute"):
            dispute_response = EbayPaymentDisputeResponse.model_validate(
                result["dispute"]
            )

        return DisputeActionResponse(
            success=result["success"],
            message=result.get("message"),
            dispute=dispute_response,
        )

    except Exception as e:
        logger.error(
            f"[POST /payment-disputes/{payment_dispute_id}/accept] "
            f"Failed for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to accept dispute: {str(e)}",
        )


@router.post(
    "/payment-disputes/{payment_dispute_id}/contest",
    response_model=DisputeActionResponse,
)
def contest_dispute(
    payment_dispute_id: str,
    request: ContestDisputeRequest = None,
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    Contest a payment dispute (fight buyer's claim).

    **IMPORTANT:** Add evidence BEFORE contesting!
    Once contested, no more evidence can be added.

    **Effect:**
    - Seller disputes the buyer's claim
    - eBay reviews the evidence
    - Dispute resolved based on evidence

    **When to contest:**
    - Buyer claim is not legitimate
    - You have evidence to support your case
    - Tracking shows delivery
    - Item was as described

    **Example:**
    ```bash
    # Contest without note
    curl -X POST "http://localhost:8000/api/ebay/payment-disputes/5********0/contest" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{}'

    # Contest with note
    curl -X POST "http://localhost:8000/api/ebay/payment-disputes/5********0/contest" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{
        "note": "Item was delivered to buyer address on 01/10/2026. Tracking attached as evidence."
      }'
    ```

    Args:
        payment_dispute_id: eBay payment dispute ID
        request: Optional note and return address
        db_user: DB session and authenticated user

    Returns:
        Contest result with updated dispute

    Raises:
        400: Dispute cannot be contested (closed or CONTEST not available)
        404: Dispute not found
        500: eBay API call failed
    """
    db, current_user = db_user

    logger.info(
        f"[POST /payment-disputes/{payment_dispute_id}/contest] "
        f"user_id={current_user.id}"
    )

    note = None
    return_address = None
    if request:
        note = request.note
        return_address = request.return_address

    try:
        service = EbayPaymentDisputeService(db, current_user.id)

        result = service.contest_dispute(
            payment_dispute_id=payment_dispute_id,
            note=note,
            return_address=return_address,
        )

        if result["success"]:
            logger.info(
                f"[POST /payment-disputes/{payment_dispute_id}/contest] "
                f"Success for user {current_user.id}"
            )
        else:
            logger.warning(
                f"[POST /payment-disputes/{payment_dispute_id}/contest] "
                f"Failed for user {current_user.id}: {result['message']}"
            )

        dispute_response = None
        if result.get("dispute"):
            dispute_response = EbayPaymentDisputeResponse.model_validate(
                result["dispute"]
            )

        return DisputeActionResponse(
            success=result["success"],
            message=result.get("message"),
            dispute=dispute_response,
        )

    except Exception as e:
        logger.error(
            f"[POST /payment-disputes/{payment_dispute_id}/contest] "
            f"Failed for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to contest dispute: {str(e)}",
        )


@router.post(
    "/payment-disputes/{payment_dispute_id}/add-evidence",
    response_model=AddEvidenceResponse,
)
def add_evidence(
    payment_dispute_id: str,
    request: AddEvidenceRequest,
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    Add evidence to a payment dispute.

    **IMPORTANT:** Evidence must be added BEFORE contesting!
    Once the dispute is contested, no more evidence can be added.

    **Evidence Types:**
    - PROOF_OF_DELIVERY: Delivery confirmation
    - PROOF_OF_AUTHENTICITY: Item authenticity proof
    - PROOF_OF_ITEM_AS_DESCRIBED: Item matches description
    - PROOF_OF_PICKUP: Buyer picked up item
    - TRACKING_INFORMATION: Shipping tracking info

    **Workflow:**
    1. Upload files via eBay File Upload API (get file IDs)
    2. Call this endpoint with file IDs and evidence type
    3. Repeat for additional evidence
    4. Contest the dispute when ready

    **Example:**
    ```bash
    # Add tracking evidence
    curl -X POST "http://localhost:8000/api/ebay/payment-disputes/5********0/add-evidence" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{
        "evidence_type": "TRACKING_INFORMATION",
        "files": [
          {"file_id": "ABC123", "content_type": "application/pdf"}
        ]
      }'

    # Add proof of delivery
    curl -X POST "http://localhost:8000/api/ebay/payment-disputes/5********0/add-evidence" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{
        "evidence_type": "PROOF_OF_DELIVERY",
        "files": [
          {"file_id": "DEF456", "content_type": "image/png"}
        ]
      }'
    ```

    Args:
        payment_dispute_id: eBay payment dispute ID
        request: Evidence type and files
        db_user: DB session and authenticated user

    Returns:
        Add evidence result with evidence ID

    Raises:
        400: Cannot add evidence (closed or already contested)
        404: Dispute not found
        500: eBay API call failed
    """
    db, current_user = db_user

    logger.info(
        f"[POST /payment-disputes/{payment_dispute_id}/add-evidence] "
        f"user_id={current_user.id}, type={request.evidence_type}"
    )

    files = None
    if request.files:
        files = [
            {"fileId": f.file_id, "contentType": f.content_type}
            for f in request.files
        ]

    try:
        service = EbayPaymentDisputeService(db, current_user.id)

        result = service.add_evidence(
            payment_dispute_id=payment_dispute_id,
            evidence_type=request.evidence_type,
            files=files,
            line_items=request.line_items,
        )

        if result["success"]:
            logger.info(
                f"[POST /payment-disputes/{payment_dispute_id}/add-evidence] "
                f"Success for user {current_user.id}: evidence_id={result['evidence_id']}"
            )
        else:
            logger.warning(
                f"[POST /payment-disputes/{payment_dispute_id}/add-evidence] "
                f"Failed for user {current_user.id}: {result['message']}"
            )

        return AddEvidenceResponse(**result)

    except Exception as e:
        logger.error(
            f"[POST /payment-disputes/{payment_dispute_id}/add-evidence] "
            f"Failed for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add evidence: {str(e)}",
        )
