"""
eBay Dashboard Schemas

Pydantic schemas for eBay unified dashboard API (response only).

Schemas:
- Response: DashboardStatisticsResponse, UrgentItemsResponse, RecentActivityResponse,
            DomainStatistics, TotalsStatistics, UrgentItem, ActivityItem

Created: 2026-01-14
Author: Claude
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# =============================================================================
# STATISTICS SCHEMAS
# =============================================================================


class ReturnStatistics(BaseModel):
    """Statistics for returns."""

    open: int = Field(default=0, description="Number of open returns")
    closed: int = Field(default=0, description="Number of closed returns")
    needs_action: int = Field(default=0, description="Returns needing seller action")
    past_deadline: int = Field(default=0, description="Returns past deadline")


class CancellationStatistics(BaseModel):
    """Statistics for cancellations."""

    pending: int = Field(default=0, description="Number of pending cancellations")
    closed: int = Field(default=0, description="Number of closed cancellations")
    needs_action: int = Field(default=0, description="Cancellations needing seller action")
    past_due: int = Field(default=0, description="Cancellations past response due date")


class RefundStatistics(BaseModel):
    """Statistics for refunds."""

    pending: int = Field(default=0, description="Number of pending refunds")
    completed: int = Field(default=0, description="Number of completed refunds")
    failed: int = Field(default=0, description="Number of failed refunds")
    total_refunded: float = Field(default=0.0, description="Total amount refunded")


class PaymentDisputeStatistics(BaseModel):
    """Statistics for payment disputes."""

    open: int = Field(default=0, description="Number of open disputes")
    action_needed: int = Field(default=0, description="Disputes needing action")
    closed: int = Field(default=0, description="Number of closed disputes")
    total_disputed: float = Field(default=0.0, description="Total amount disputed")


class InquiryStatistics(BaseModel):
    """Statistics for INR inquiries."""

    open: int = Field(default=0, description="Number of open inquiries")
    closed: int = Field(default=0, description="Number of closed inquiries")
    needs_action: int = Field(default=0, description="Inquiries needing seller action")
    past_deadline: int = Field(default=0, description="Inquiries past deadline")


class TotalsStatistics(BaseModel):
    """Aggregated totals across all domains."""

    open: int = Field(default=0, description="Total open items across all domains")
    needs_action: int = Field(
        default=0, description="Total items needing action across all domains"
    )
    past_deadline: int = Field(
        default=0, description="Total items past deadline across all domains"
    )


class DashboardStatisticsResponse(BaseModel):
    """
    Response for unified dashboard statistics.

    Aggregates statistics from all eBay post-sale domains:
    returns, cancellations, refunds, payment disputes, and INR inquiries.
    """

    returns: ReturnStatistics
    cancellations: CancellationStatistics
    refunds: RefundStatistics
    payment_disputes: PaymentDisputeStatistics
    inquiries: InquiryStatistics
    totals: TotalsStatistics
    generated_at: datetime = Field(
        description="When the statistics were generated"
    )


# =============================================================================
# URGENT ITEMS SCHEMAS
# =============================================================================


class UrgentItem(BaseModel):
    """
    Represents an urgent item requiring seller action.

    Common fields across all domain types.
    """

    id: int = Field(description="Internal ID")
    type: str = Field(
        description="Item type: return, cancellation, payment_dispute, or inquiry"
    )
    urgency: str = Field(
        description="Urgency level: critical or high"
    )
    external_id: Optional[str] = Field(
        default=None,
        alias="return_id",
        description="External ID (return_id, cancel_id, dispute_id, inquiry_id)",
    )
    order_id: Optional[str] = Field(default=None, description="eBay order ID")
    status: Optional[str] = Field(default=None, description="Current status")
    reason: Optional[str] = Field(default=None, description="Reason (if applicable)")
    amount: Optional[float] = Field(
        default=None,
        alias="refund_amount",
        description="Amount (refund, dispute, claim)",
    )
    currency: Optional[str] = Field(
        default=None,
        alias="refund_currency",
        description="Currency code",
    )
    buyer_username: Optional[str] = Field(
        default=None, description="Buyer's eBay username"
    )
    deadline_date: Optional[datetime] = Field(
        default=None, description="Response deadline"
    )
    is_past_due: Optional[bool] = Field(
        default=None, description="Whether past deadline"
    )

    # Return-specific
    return_id: Optional[str] = Field(default=None)

    # Cancellation-specific
    cancel_id: Optional[str] = Field(default=None)
    requestor_role: Optional[str] = Field(default=None)
    response_due_date: Optional[datetime] = Field(default=None)

    # Dispute-specific
    dispute_id: Optional[str] = Field(default=None)
    state: Optional[str] = Field(default=None)
    dispute_amount: Optional[float] = Field(default=None)
    dispute_currency: Optional[str] = Field(default=None)

    # Inquiry-specific
    inquiry_id: Optional[str] = Field(default=None)
    claim_amount: Optional[float] = Field(default=None)
    claim_currency: Optional[str] = Field(default=None)
    item_title: Optional[str] = Field(default=None)
    respond_by_date: Optional[datetime] = Field(default=None)
    is_escalated: Optional[bool] = Field(default=None)
    is_past_deadline: Optional[bool] = Field(default=None)

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }


class UrgentItemsResponse(BaseModel):
    """
    Response for urgent items requiring seller action.

    Groups urgent items by domain type.
    """

    returns: List[UrgentItem] = Field(
        default_factory=list, description="Urgent returns"
    )
    cancellations: List[UrgentItem] = Field(
        default_factory=list, description="Urgent cancellations"
    )
    payment_disputes: List[UrgentItem] = Field(
        default_factory=list, description="Urgent payment disputes"
    )
    inquiries: List[UrgentItem] = Field(
        default_factory=list, description="Urgent INR inquiries"
    )
    total_count: int = Field(
        default=0, description="Total number of urgent items"
    )
    generated_at: datetime = Field(
        description="When the data was generated"
    )


# =============================================================================
# RECENT ACTIVITY SCHEMAS
# =============================================================================


class ActivityItem(BaseModel):
    """
    Represents a recent activity item.

    Common structure for all domain types.
    """

    type: str = Field(
        description="Activity type: return, cancellation, refund, payment_dispute, or inquiry"
    )
    id: int = Field(description="Internal ID")
    external_id: Optional[str] = Field(
        default=None, description="External ID from eBay"
    )
    order_id: Optional[str] = Field(default=None, description="eBay order ID")
    status: Optional[str] = Field(default=None, description="Current status")
    amount: Optional[float] = Field(default=None, description="Amount (if applicable)")
    currency: Optional[str] = Field(default=None, description="Currency code")
    buyer_username: Optional[str] = Field(
        default=None, description="Buyer's eBay username"
    )
    date: Optional[datetime] = Field(
        default=None, description="Creation or event date"
    )
    updated_at: Optional[datetime] = Field(
        default=None, description="Last update timestamp"
    )

    model_config = {"extra": "allow"}


class RecentActivityResponse(BaseModel):
    """
    Response for recent activity timeline.

    Returns most recent items across all domains sorted by date.
    """

    items: List[ActivityItem] = Field(
        default_factory=list, description="Recent activity items"
    )
    total_count: int = Field(
        default=0, description="Number of items returned"
    )
