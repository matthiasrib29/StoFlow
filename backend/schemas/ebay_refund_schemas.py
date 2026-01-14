"""
eBay Refund Pydantic Schemas

Schemas for request/response validation in refund API endpoints.

Created: 2026-01-14
Author: Claude
"""

from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, computed_field


# =============================================================================
# Request Schemas
# =============================================================================


class SyncRefundsRequest(BaseModel):
    """Request to sync refunds from eBay orders."""

    days_back: int = Field(default=30, ge=1, le=180, description="Days to look back")


class SyncRefundsFromOrderRequest(BaseModel):
    """Request to sync refunds from a specific order."""

    order_id: str = Field(..., min_length=1, description="eBay order ID")


class IssueRefundRequest(BaseModel):
    """Request to issue a refund."""

    order_id: str = Field(..., min_length=1, description="eBay order ID")
    reason: Literal[
        "BUYER_CANCEL",
        "BUYER_RETURN",
        "ITEM_NOT_RECEIVED",
        "SELLER_WRONG_ITEM",
        "SELLER_OUT_OF_STOCK",
        "SELLER_FOUND_ISSUE",
        "OTHER",
    ] = Field(..., description="Refund reason code")
    amount: float = Field(..., gt=0, description="Refund amount")
    currency: str = Field(default="EUR", description="Currency code")
    line_item_id: Optional[str] = Field(
        default=None, description="Line item ID for partial refund"
    )
    comment: Optional[str] = Field(
        default=None, max_length=500, description="Optional comment"
    )


# =============================================================================
# Response Schemas
# =============================================================================


class EbayRefundResponse(BaseModel):
    """Response schema for a single refund."""

    id: int
    refund_id: str
    order_id: Optional[str] = None

    # Source
    refund_source: Optional[str] = None
    return_id: Optional[str] = None
    cancel_id: Optional[str] = None

    # Status
    refund_status: Optional[str] = None

    # Amount
    refund_amount: Optional[float] = None
    refund_currency: Optional[str] = None
    original_amount: Optional[float] = None

    # Reason
    reason: Optional[str] = None
    comment: Optional[str] = None

    # Buyer
    buyer_username: Optional[str] = None

    # Reference IDs
    refund_reference_id: Optional[str] = None
    transaction_id: Optional[str] = None
    line_item_id: Optional[str] = None

    # Dates
    refund_date: Optional[datetime] = None
    creation_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # Computed properties
    @computed_field
    @property
    def is_completed(self) -> bool:
        """Check if refund has been processed."""
        return self.refund_status == "REFUNDED"

    @computed_field
    @property
    def is_pending(self) -> bool:
        """Check if refund is still pending."""
        return self.refund_status == "PENDING"

    @computed_field
    @property
    def is_failed(self) -> bool:
        """Check if refund failed."""
        return self.refund_status == "FAILED"

    @computed_field
    @property
    def is_from_return(self) -> bool:
        """Check if refund is from a return."""
        return self.refund_source == "RETURN" or self.return_id is not None

    @computed_field
    @property
    def is_from_cancellation(self) -> bool:
        """Check if refund is from a cancellation."""
        return self.refund_source == "CANCELLATION" or self.cancel_id is not None

    @computed_field
    @property
    def is_manual(self) -> bool:
        """Check if refund was manually issued."""
        return self.refund_source == "MANUAL"

    model_config = {"from_attributes": True}


class RefundListResponse(BaseModel):
    """Paginated list of refunds."""

    items: List[EbayRefundResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class SyncRefundsResponse(BaseModel):
    """Response for sync operation."""

    created: int
    updated: int
    skipped: int
    errors: int = 0


class IssueRefundResponse(BaseModel):
    """Response for issue refund operation."""

    success: bool
    refund_id: Optional[str] = None
    refund_status: Optional[str] = None
    message: Optional[str] = None


class RefundSourceStatistics(BaseModel):
    """Statistics by refund source."""

    RETURN: int = 0
    CANCELLATION: int = 0
    MANUAL: int = 0


class RefundStatisticsResponse(BaseModel):
    """Response for refund statistics."""

    pending: int
    completed: int
    failed: int
    total_refunded: float
    by_source: RefundSourceStatistics


# =============================================================================
# API Constants
# =============================================================================


# Valid refund reason codes for documentation
REFUND_REASON_CODES = [
    "BUYER_CANCEL",
    "BUYER_RETURN",
    "ITEM_NOT_RECEIVED",
    "SELLER_WRONG_ITEM",
    "SELLER_OUT_OF_STOCK",
    "SELLER_FOUND_ISSUE",
    "OTHER",
]

# Valid refund status values
REFUND_STATUS_VALUES = [
    "PENDING",
    "REFUNDED",
    "FAILED",
]

# Valid refund source values
REFUND_SOURCE_VALUES = [
    "RETURN",
    "CANCELLATION",
    "MANUAL",
    "OTHER",
]
