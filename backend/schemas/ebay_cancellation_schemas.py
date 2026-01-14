"""
eBay Cancellation Schemas

Pydantic schemas for eBay cancellations API (request/response).

Schemas:
- Request: SyncCancellationsRequest, ApproveCancellationRequest,
           RejectCancellationRequest, CreateCancellationRequest, CheckEligibilityRequest
- Response: EbayCancellationResponse, CancellationListResponse, SyncCancellationsResponse,
            CancellationActionResponse, CancellationStatisticsResponse, EligibilityResponse

Created: 2026-01-14
Author: Claude
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, computed_field


# =============================================================================
# REQUEST SCHEMAS
# =============================================================================


class SyncCancellationsRequest(BaseModel):
    """
    Request to synchronize cancellations from eBay.

    Attributes:
        days_back: Number of days to look back (default 30, max 120)
        cancel_state: Optional filter by state (CLOSED)
    """

    days_back: int = Field(
        default=30,
        ge=1,
        le=120,
        description="Number of days to look back (1-120)",
    )
    cancel_state: Optional[str] = Field(
        default=None,
        pattern="^CLOSED$",
        description="Filter by state: CLOSED (only closed supported by eBay API)",
    )


class CheckEligibilityRequest(BaseModel):
    """
    Request to check if an order is eligible for cancellation.

    Attributes:
        order_id: eBay order ID to check
    """

    order_id: str = Field(
        ...,
        min_length=1,
        description="eBay order ID to check for cancellation eligibility",
    )


class CreateCancellationRequest(BaseModel):
    """
    Request to create a seller-initiated cancellation.

    Attributes:
        order_id: eBay order ID
        reason: Cancellation reason code
        comments: Optional seller comments
    """

    order_id: str = Field(
        ...,
        min_length=1,
        description="eBay order ID to cancel",
    )
    reason: str = Field(
        ...,
        pattern="^(OUT_OF_STOCK|ADDRESS_ISSUES|BUYER_ASKED_CANCEL|ORDER_UNPAID|OTHER_SELLER_CANCEL_REASON)$",
        description="Cancellation reason code",
    )
    comments: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Optional seller comments",
    )


class ApproveCancellationRequest(BaseModel):
    """
    Request to approve a buyer's cancellation request.

    Attributes:
        comments: Optional seller comments
    """

    comments: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Optional seller comments to buyer",
    )


class RejectCancellationRequest(BaseModel):
    """
    Request to reject a buyer's cancellation request.

    Attributes:
        reason: Rejection reason code
        tracking_number: Required if reason is ALREADY_SHIPPED
        carrier: Shipping carrier
        comments: Optional comments
    """

    reason: str = Field(
        ...,
        pattern="^(ALREADY_SHIPPED|OTHER_SELLER_REJECT_REASON)$",
        description="Rejection reason code",
    )
    tracking_number: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Required if reason is ALREADY_SHIPPED",
    )
    carrier: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Shipping carrier (e.g., 'UPS', 'La Poste')",
    )
    comments: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Optional comments",
    )


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================


class EbayCancellationResponse(BaseModel):
    """
    Response for a single eBay cancellation.

    Attributes:
        id: Internal cancellation ID
        cancel_id: eBay cancel ID
        order_id: eBay order ID
        cancel_state: Cancellation state (CLOSED)
        cancel_status: Cancellation status
        cancel_reason: Reason for cancellation
        requestor_role: Who initiated (BUYER, SELLER)
        request_date: When cancellation was requested
        response_due_date: Deadline for seller response
        refund_amount: Refund amount
        refund_currency: Currency code
        refund_status: Refund status
        buyer_username: Buyer's eBay username
        buyer_comments: Buyer's comments
        seller_comments: Seller's comments
        reject_reason: Reason for rejection
        tracking_number: Shipment tracking number
        carrier: Shipping carrier
        shipped_date: When item was shipped
        creation_date: When cancellation was created
        closed_date: When cancellation was closed
        created_at: Record creation timestamp
        updated_at: Record update timestamp
    """

    id: int
    cancel_id: str
    order_id: Optional[str] = None
    cancel_state: Optional[str] = None
    cancel_status: Optional[str] = None
    cancel_reason: Optional[str] = None
    requestor_role: Optional[str] = None
    request_date: Optional[datetime] = None
    response_due_date: Optional[datetime] = None
    refund_amount: Optional[float] = None
    refund_currency: Optional[str] = None
    refund_status: Optional[str] = None
    buyer_username: Optional[str] = None
    buyer_comments: Optional[str] = None
    seller_comments: Optional[str] = None
    reject_reason: Optional[str] = None
    tracking_number: Optional[str] = None
    carrier: Optional[str] = None
    shipped_date: Optional[datetime] = None
    creation_date: Optional[datetime] = None
    closed_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def is_closed(self) -> bool:
        """Check if cancellation is closed."""
        return self.cancel_state == "CLOSED"

    @computed_field
    @property
    def is_pending(self) -> bool:
        """Check if cancellation is pending."""
        pending_statuses = ["CANCEL_REQUESTED", "CANCEL_PENDING"]
        return self.cancel_status in pending_statuses

    @computed_field
    @property
    def needs_action(self) -> bool:
        """Check if cancellation requires seller action (buyer-initiated pending)."""
        pending_statuses = ["CANCEL_REQUESTED", "CANCEL_PENDING"]
        return self.cancel_status in pending_statuses and self.requestor_role == "BUYER"

    @computed_field
    @property
    def is_past_response_due(self) -> bool:
        """Check if response deadline has passed."""
        if not self.response_due_date:
            return False
        from datetime import timezone
        return datetime.now(timezone.utc) > self.response_due_date

    @computed_field
    @property
    def was_approved(self) -> bool:
        """Check if cancellation was approved."""
        approved_statuses = [
            "CANCEL_CLOSED_WITH_REFUND",
            "CANCEL_CLOSED_UNKNOWN_REFUND",
            "CANCEL_CLOSED_NO_REFUND",
        ]
        return self.cancel_status in approved_statuses

    @computed_field
    @property
    def was_rejected(self) -> bool:
        """Check if cancellation was rejected."""
        return self.cancel_status == "CANCEL_REJECTED"

    model_config = {"from_attributes": True}


class CancellationListResponse(BaseModel):
    """
    Response for paginated list of cancellations.

    Attributes:
        items: List of cancellations
        total: Total count
        page: Current page
        page_size: Items per page
        total_pages: Total number of pages
    """

    items: List[EbayCancellationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = {"from_attributes": True}


class SyncCancellationsResponse(BaseModel):
    """
    Response for cancellation sync operation.

    Attributes:
        created: Number of new cancellations created
        updated: Number of existing cancellations updated
        skipped: Number of cancellations skipped
        errors: Number of errors
        total_fetched: Total cancellations fetched from eBay
        details: Per-cancellation details
    """

    created: int = 0
    updated: int = 0
    skipped: int = 0
    errors: int = 0
    total_fetched: int = 0
    details: List[Dict[str, Any]] = Field(default_factory=list)


class CancellationActionResponse(BaseModel):
    """
    Response for cancellation action (approve, reject, create).

    Attributes:
        success: Whether action was successful
        cancel_id: eBay cancel ID
        new_status: New status after action (if applicable)
        message: Optional message
    """

    success: bool
    cancel_id: str
    new_status: Optional[str] = None
    message: Optional[str] = None


class EligibilityResponse(BaseModel):
    """
    Response for cancellation eligibility check.

    Attributes:
        eligible: Whether order is eligible for cancellation
        eligibility_status: Detailed eligibility status
        order_id: eBay order ID checked
        reasons: List of reasons if not eligible
    """

    eligible: bool
    eligibility_status: Optional[str] = None
    order_id: str
    reasons: List[str] = Field(default_factory=list)


class CancellationStatisticsResponse(BaseModel):
    """
    Response for cancellation statistics.

    Attributes:
        pending: Number of pending cancellations
        closed: Number of closed cancellations
        needs_action: Number of cancellations needing seller action
        past_due: Number of cancellations past response deadline
    """

    pending: int
    closed: int
    needs_action: int
    past_due: int
