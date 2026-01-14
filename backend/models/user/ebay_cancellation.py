"""
eBay Cancellation Model - User Schema

Stores eBay order cancellation requests retrieved via Post-Order API v2.
Linked to EbayOrder for order context.

Business Rules:
- cancel_id is unique per user schema
- Links to ebay_orders via order_id FK
- cancel_status tracks the cancellation workflow state
- Seller needs to respond to buyer-initiated cancellations
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class EbayCancellation(Base):
    """
    eBay Cancellation - Order cancellation request information.

    Cancel States:
        CLOSED: Cancellation completed

    Cancel Statuses:
        CANCEL_REQUESTED: Buyer requested cancellation
        CANCEL_PENDING: Awaiting seller response
        CANCEL_CLOSED_WITH_REFUND: Cancelled and refunded
        CANCEL_CLOSED_UNKNOWN_REFUND: Closed with unknown refund status
        CANCEL_CLOSED_FOR_COMMITMENT: Cancelled due to commitment issues
        CANCEL_REJECTED: Seller rejected cancellation

    Cancel Reasons:
        BUYER_ASKED_CANCEL: Buyer requested
        ORDER_UNPAID: Order not paid
        ADDRESS_ISSUES: Address problems
        OUT_OF_STOCK: Item unavailable
        OTHER_SELLER_CANCEL_REASON: Other seller reason

    Attributes:
        id: Primary key (auto-increment)
        cancel_id: eBay cancellation ID (e.g., "5000012345") - unique
        order_id: FK to ebay_orders.order_id

        Status fields:
        cancel_status: Current status (see statuses above)
        cancel_state: High-level state (currently only CLOSED)
        cancel_reason: Why cancellation was initiated

        Request fields:
        requestor_role: Who initiated (BUYER or SELLER)
        request_date: When cancellation was requested
        response_due_date: Deadline for seller to respond

        Refund fields:
        refund_amount: Amount refunded
        refund_currency: Currency code
        refund_status: Status of refund

        Buyer/Seller fields:
        buyer_username: Buyer's eBay username
        buyer_comments: Buyer's cancellation reason text
        seller_comments: Seller's response text
        reject_reason: If rejected, the reason code

        Shipping (for rejection):
        tracking_number: If rejected because shipped
        carrier: Carrier name
        shipped_date: When item was shipped

        Dates:
        creation_date: When cancel request was created on eBay
        closed_date: When cancellation was closed

        Metadata:
        raw_data: Full eBay API response (for debugging)
        created_at: Record creation timestamp
        updated_at: Record update timestamp
    """

    __tablename__ = "ebay_cancellations"
    __table_args__ = {"schema": "tenant"}  # Placeholder for schema_translate_map

    # Primary Key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # Cancellation Identification
    cancel_id: Mapped[str] = mapped_column(
        Text, nullable=False, unique=True, index=True
    )
    order_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("tenant.ebay_orders.order_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Status
    cancel_status: Mapped[Optional[str]] = mapped_column(Text, nullable=True, index=True)
    cancel_state: Mapped[Optional[str]] = mapped_column(Text, nullable=True, index=True)
    cancel_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Request Info
    requestor_role: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    request_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    response_due_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    # Refund
    refund_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    refund_currency: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    refund_status: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Buyer Info
    buyer_username: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    buyer_comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Seller Info
    seller_comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reject_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Shipping Info (used when rejecting because already shipped)
    tracking_number: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    carrier: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    shipped_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Dates
    creation_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    closed_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Raw eBay Data (for debugging)
    raw_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<EbayCancellation(cancel_id='{self.cancel_id}', "
            f"status='{self.cancel_status}', order_id='{self.order_id}')>"
        )

    @property
    def is_closed(self) -> bool:
        """Check if cancellation is closed."""
        return self.cancel_state == "CLOSED"

    @property
    def is_pending(self) -> bool:
        """Check if cancellation is pending seller response."""
        pending_statuses = ["CANCEL_REQUESTED", "CANCEL_PENDING"]
        return self.cancel_status in pending_statuses

    @property
    def needs_action(self) -> bool:
        """Check if cancellation requires seller action."""
        return self.is_pending and self.requestor_role == "BUYER"

    @property
    def was_approved(self) -> bool:
        """Check if cancellation was approved."""
        approved_statuses = [
            "CANCEL_CLOSED_WITH_REFUND",
            "CANCEL_CLOSED_UNKNOWN_REFUND",
            "CANCEL_CLOSED_FOR_COMMITMENT",
        ]
        return self.cancel_status in approved_statuses

    @property
    def was_rejected(self) -> bool:
        """Check if cancellation was rejected."""
        return self.cancel_status == "CANCEL_REJECTED"

    @property
    def is_past_response_due(self) -> bool:
        """Check if response deadline has passed."""
        if not self.response_due_date:
            return False
        from datetime import timezone
        return datetime.now(timezone.utc) > self.response_due_date
