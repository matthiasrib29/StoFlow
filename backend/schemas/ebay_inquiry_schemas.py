"""
eBay Inquiry Schemas

Pydantic schemas for eBay INR inquiries API (request/response).

Schemas:
- Request: SyncInquiriesRequest, ProvideShipmentInfoRequest, ProvideRefundRequest,
           SendMessageRequest, EscalateInquiryRequest
- Response: EbayInquiryResponse, InquiryListResponse, SyncInquiriesResponse,
            InquiryActionResponse, InquiryStatisticsResponse

Created: 2026-01-14
Author: Claude
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, computed_field


# =============================================================================
# REQUEST SCHEMAS
# =============================================================================


class SyncInquiriesRequest(BaseModel):
    """
    Request to synchronize inquiries from eBay.

    Attributes:
        inquiry_state: Optional filter by state (OPEN, CLOSED)
    """

    inquiry_state: Optional[str] = Field(
        default=None,
        pattern="^(OPEN|CLOSED)$",
        description="Filter by state: OPEN or CLOSED",
    )


class ProvideShipmentInfoRequest(BaseModel):
    """
    Request to provide shipment tracking for an INR inquiry.

    Attributes:
        tracking_number: Shipment tracking number
        carrier: Shipping carrier (e.g., "UPS", "FEDEX", "DHL")
        shipped_date: Optional ship date
        comments: Optional seller comments
    """

    tracking_number: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Shipment tracking number",
    )
    carrier: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Shipping carrier (e.g., UPS, FEDEX)",
    )
    shipped_date: Optional[datetime] = Field(
        default=None,
        description="Date item was shipped",
    )
    comments: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Seller comments to buyer",
    )


class ProvideRefundRequest(BaseModel):
    """
    Request to provide refund for an INR inquiry.

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


class InquirySendMessageRequest(BaseModel):
    """
    Request to send message to buyer about inquiry.

    Attributes:
        message: Message text
    """

    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Message text to send to buyer",
    )


class EscalateInquiryRequest(BaseModel):
    """
    Request to escalate an inquiry to an eBay case.

    Attributes:
        comments: Optional escalation comments
    """

    comments: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Escalation comments",
    )


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================


class EbayInquiryResponse(BaseModel):
    """
    Response for a single eBay INR inquiry.

    Attributes:
        id: Internal inquiry ID
        inquiry_id: eBay inquiry ID
        order_id: eBay order ID
        inquiry_state: Inquiry state (OPEN, CLOSED)
        inquiry_status: Inquiry status
        inquiry_type: Type of inquiry (INR)
        claim_amount: Claimed amount
        claim_currency: Currency code
        buyer_username: Buyer's eBay username
        buyer_comments: Buyer's comments
        seller_response: Seller's response type
        item_id: eBay item ID
        item_title: Item title
        shipment_tracking_number: Tracking number (if provided)
        shipment_carrier: Carrier (if provided)
        creation_date: When inquiry was created
        respond_by_date: Deadline for response
        closed_date: When inquiry was closed
        escalation_date: When escalated (if applicable)
        created_at: Record creation timestamp
        updated_at: Record update timestamp
    """

    id: int
    inquiry_id: str
    order_id: Optional[str] = None
    inquiry_state: Optional[str] = None
    inquiry_status: Optional[str] = None
    inquiry_type: Optional[str] = None
    claim_amount: Optional[float] = None
    claim_currency: Optional[str] = None
    buyer_username: Optional[str] = None
    buyer_comments: Optional[str] = None
    seller_response: Optional[str] = None
    item_id: Optional[str] = None
    item_title: Optional[str] = None
    shipment_tracking_number: Optional[str] = None
    shipment_carrier: Optional[str] = None
    creation_date: Optional[datetime] = None
    respond_by_date: Optional[datetime] = None
    closed_date: Optional[datetime] = None
    escalation_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def is_open(self) -> bool:
        """Check if inquiry is still open."""
        return self.inquiry_state == "OPEN"

    @computed_field
    @property
    def needs_action(self) -> bool:
        """Check if inquiry requires seller action."""
        return self.inquiry_status == "INR_WAITING_FOR_SELLER"

    @computed_field
    @property
    def is_past_due(self) -> bool:
        """Check if response deadline has passed."""
        if not self.respond_by_date:
            return False
        from datetime import timezone
        return datetime.now(timezone.utc) > self.respond_by_date

    @computed_field
    @property
    def is_escalated(self) -> bool:
        """Check if inquiry was escalated to a case."""
        return self.inquiry_status == "INR_ESCALATED"

    model_config = {"from_attributes": True}


class InquiryListResponse(BaseModel):
    """
    Response for paginated list of inquiries.

    Attributes:
        items: List of inquiries
        total: Total count
        page: Current page
        page_size: Items per page
        total_pages: Total number of pages
    """

    items: List[EbayInquiryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = {"from_attributes": True}


class SyncInquiriesResponse(BaseModel):
    """
    Response for inquiry sync operation.

    Attributes:
        success: Whether sync succeeded
        created: Number of new inquiries created
        updated: Number of existing inquiries updated
        total_fetched: Total inquiries fetched from eBay
        errors: List of error messages
    """

    success: bool = True
    created: int = 0
    updated: int = 0
    total_fetched: int = 0
    errors: List[str] = Field(default_factory=list)


class InquiryActionResponse(BaseModel):
    """
    Response for inquiry action (shipment info, refund, message, escalate).

    Attributes:
        success: Whether action was successful
        inquiry_id: eBay inquiry ID
        new_status: New status after action (if applicable)
        message: Optional message
    """

    success: bool
    inquiry_id: str
    new_status: Optional[str] = None
    message: Optional[str] = None


class InquiryStatisticsResponse(BaseModel):
    """
    Response for inquiry statistics.

    Attributes:
        open: Number of open inquiries
        closed: Number of closed inquiries
        needs_action: Number of inquiries needing action
        past_deadline: Number of inquiries past deadline
    """

    open: int
    closed: int
    needs_action: int
    past_deadline: int
