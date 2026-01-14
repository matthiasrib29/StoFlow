"""
eBay Return Schemas

Pydantic schemas for eBay returns API (request/response).

Schemas:
- Request: SyncReturnsRequest, AcceptReturnRequest, DeclineReturnRequest,
           IssueRefundRequest, MarkAsReceivedRequest, SendMessageRequest
- Response: EbayReturnResponse, ReturnListResponse, SyncReturnsResponse,
            ReturnActionResponse, ReturnStatisticsResponse

Created: 2026-01-13
Author: Claude
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, computed_field


# =============================================================================
# REQUEST SCHEMAS
# =============================================================================


class SyncReturnsRequest(BaseModel):
    """
    Request to synchronize returns from eBay.

    Attributes:
        days_back: Number of days to look back (default 30, max 120)
        return_state: Optional filter by state (OPEN, CLOSED)
    """

    days_back: int = Field(
        default=30,
        ge=1,
        le=120,
        description="Number of days to look back (1-120)",
    )
    return_state: Optional[str] = Field(
        default=None,
        pattern="^(OPEN|CLOSED)$",
        description="Filter by state: OPEN or CLOSED",
    )


class AcceptReturnRequest(BaseModel):
    """
    Request to accept a return.

    Attributes:
        comments: Optional seller comments
        rma_number: Optional RMA number
    """

    comments: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Seller comments to buyer",
    )
    rma_number: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Return Merchandise Authorization number",
    )


class DeclineReturnRequest(BaseModel):
    """
    Request to decline a return.

    Attributes:
        comments: Required reason for declining
    """

    comments: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Required reason for declining the return",
    )


class IssueRefundRequest(BaseModel):
    """
    Request to issue a refund.

    Attributes:
        refund_amount: Optional partial refund amount (full if not specified)
        currency: Currency code (e.g., "EUR")
        comments: Optional refund comments
    """

    refund_amount: Optional[float] = Field(
        default=None,
        gt=0,
        description="Partial refund amount (omit for full refund)",
    )
    currency: Optional[str] = Field(
        default=None,
        pattern="^[A-Z]{3}$",
        description="Currency code (e.g., EUR, USD)",
    )
    comments: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Refund comments",
    )


class MarkAsReceivedRequest(BaseModel):
    """
    Request to mark return item as received.

    Attributes:
        comments: Optional comments about item condition
    """

    comments: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Comments about item condition",
    )


class SendMessageRequest(BaseModel):
    """
    Request to send message to buyer.

    Attributes:
        message: Message text
    """

    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Message text to send to buyer",
    )


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================


class EbayReturnResponse(BaseModel):
    """
    Response for a single eBay return.

    Attributes:
        id: Internal return ID
        return_id: eBay return ID
        order_id: eBay order ID
        state: Return state (OPEN, CLOSED)
        status: Return status
        return_type: Type of return
        reason: Return reason
        reason_detail: Detailed reason
        refund_amount: Refund amount
        refund_currency: Currency code
        refund_status: Refund status
        buyer_username: Buyer's eBay username
        buyer_comments: Buyer's comments
        seller_comments: Seller's comments
        rma_number: RMA number
        return_tracking_number: Return shipment tracking
        return_carrier: Return carrier
        creation_date: When return was created
        deadline_date: Deadline for response
        closed_date: When return was closed
        received_date: When item was received
        created_at: Record creation timestamp
        updated_at: Record update timestamp
    """

    id: int
    return_id: str
    order_id: Optional[str] = None
    state: Optional[str] = None
    status: Optional[str] = None
    return_type: Optional[str] = None
    reason: Optional[str] = None
    reason_detail: Optional[str] = None
    refund_amount: Optional[float] = None
    refund_currency: Optional[str] = None
    refund_status: Optional[str] = None
    buyer_username: Optional[str] = None
    buyer_comments: Optional[str] = None
    seller_comments: Optional[str] = None
    rma_number: Optional[str] = None
    return_tracking_number: Optional[str] = None
    return_carrier: Optional[str] = None
    creation_date: Optional[datetime] = None
    deadline_date: Optional[datetime] = None
    closed_date: Optional[datetime] = None
    received_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def is_open(self) -> bool:
        """Check if return is still open."""
        return self.state == "OPEN"

    @computed_field
    @property
    def needs_action(self) -> bool:
        """Check if return requires seller action."""
        action_statuses = [
            "RETURN_REQUESTED",
            "RETURN_WAITING_FOR_RMA",
            "RETURN_ITEM_DELIVERED",
        ]
        return self.status in action_statuses

    @computed_field
    @property
    def is_past_deadline(self) -> bool:
        """Check if deadline has passed."""
        if not self.deadline_date:
            return False
        from datetime import timezone
        return datetime.now(timezone.utc) > self.deadline_date

    model_config = {"from_attributes": True}


class ReturnListResponse(BaseModel):
    """
    Response for paginated list of returns.

    Attributes:
        items: List of returns
        total: Total count
        page: Current page
        page_size: Items per page
        total_pages: Total number of pages
    """

    items: List[EbayReturnResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = {"from_attributes": True}


class SyncReturnsResponse(BaseModel):
    """
    Response for return sync operation.

    Attributes:
        created: Number of new returns created
        updated: Number of existing returns updated
        skipped: Number of returns skipped
        errors: Number of errors
        total_fetched: Total returns fetched from eBay
        details: Per-return details
    """

    created: int = 0
    updated: int = 0
    skipped: int = 0
    errors: int = 0
    total_fetched: int = 0
    details: List[Dict[str, Any]] = Field(default_factory=list)


class ReturnActionResponse(BaseModel):
    """
    Response for return action (accept, decline, refund, etc.).

    Attributes:
        success: Whether action was successful
        return_id: eBay return ID
        new_status: New status after action (if applicable)
        refund_status: Refund status (for refund action)
        message: Optional message
    """

    success: bool
    return_id: str
    new_status: Optional[str] = None
    refund_status: Optional[str] = None
    message: Optional[str] = None


class ReturnStatisticsResponse(BaseModel):
    """
    Response for return statistics.

    Attributes:
        open: Number of open returns
        closed: Number of closed returns
        needs_action: Number of returns needing action
        past_deadline: Number of returns past deadline
    """

    open: int
    closed: int
    needs_action: int
    past_deadline: int
