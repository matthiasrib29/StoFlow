"""
eBay Return Model - User Schema

Stores eBay return requests retrieved via Post-Order API v2.
Linked to EbayOrder for order context.

Business Rules:
- return_id is unique per user schema
- Links to ebay_orders via order_id FK
- status tracks the return workflow state
- deadline_date is critical for seller metrics
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base


class EbayReturn(Base):
    """
    eBay Return - Return request information.

    Attributes:
        id: Primary key (auto-increment)
        return_id: eBay return ID (e.g., "5000012345") - unique
        order_id: FK to ebay_orders.order_id

        Status fields:
        status: Current return status (ReturnStatus enum value)
        state: High-level state (OPEN, CLOSED)
        return_type: Type of return (RETURN, REPLACEMENT, REFUND_ONLY)

        Reason fields:
        reason: Return reason (ReturnReason enum value)
        reason_detail: Buyer's detailed explanation

        Refund fields:
        refund_amount: Amount to refund
        refund_currency: Currency code
        refund_status: RefundStatus enum value

        Buyer/Seller fields:
        buyer_username: Buyer's eBay username
        buyer_comments: Buyer's comments
        seller_comments: Seller's response
        rma_number: Return Merchandise Authorization number

        Shipping fields:
        return_tracking_number: Return shipment tracking
        return_carrier: Carrier for return

        Date fields:
        creation_date: When return was created on eBay
        deadline_date: Deadline for seller response
        closed_date: When return was closed
        received_date: When item was received back

        Metadata:
        raw_data: Full eBay API response (for debugging)
        created_at: Record creation timestamp
        updated_at: Record update timestamp
    """

    __tablename__ = "ebay_returns"
    __table_args__ = {"schema": "tenant"}  # Placeholder for schema_translate_map

    # Primary Key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # Return Identification
    return_id: Mapped[str] = mapped_column(
        Text, nullable=False, unique=True, index=True
    )
    order_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("tenant.ebay_orders.order_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Status
    status: Mapped[Optional[str]] = mapped_column(Text, nullable=True, index=True)
    state: Mapped[Optional[str]] = mapped_column(Text, nullable=True, index=True)
    return_type: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Reason
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reason_detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Refund
    refund_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    refund_currency: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    refund_status: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Buyer Info
    buyer_username: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    buyer_comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Seller Info
    seller_comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rma_number: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Return Shipping
    return_tracking_number: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    return_carrier: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Dates
    creation_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    deadline_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    closed_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    received_date: Mapped[Optional[datetime]] = mapped_column(
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

    # Relationship to order (optional - order might not exist locally)
    # order = relationship("EbayOrder", foreign_keys=[order_id], lazy="selectin")

    def __repr__(self) -> str:
        return (
            f"<EbayReturn(return_id='{self.return_id}', "
            f"status='{self.status}', order_id='{self.order_id}')>"
        )

    @property
    def is_open(self) -> bool:
        """Check if return is still open."""
        return self.state == "OPEN"

    @property
    def needs_action(self) -> bool:
        """Check if return requires seller action."""
        action_needed_statuses = [
            "RETURN_REQUESTED",
            "RETURN_WAITING_FOR_RMA",
            "RETURN_ITEM_DELIVERED",
        ]
        return self.status in action_needed_statuses

    @property
    def is_past_deadline(self) -> bool:
        """Check if deadline has passed."""
        if not self.deadline_date:
            return False
        from datetime import timezone
        return datetime.now(timezone.utc) > self.deadline_date
