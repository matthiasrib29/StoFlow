"""
eBay Refund Model - User Schema

Stores eBay refund records retrieved from order payment summaries.
Tracks both automatic refunds (from returns/cancellations) and manual refunds.

Business Rules:
- refund_id is unique per user schema
- Links to ebay_orders via order_id FK
- status tracks the refund processing state
- source tracks where the refund originated (RETURN, CANCELLATION, MANUAL)
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class EbayRefund(Base):
    """
    eBay Refund - Payment refund record.

    Attributes:
        id: Primary key (auto-increment)
        refund_id: eBay refund ID - unique
        order_id: FK to ebay_orders.order_id

        Source fields:
        refund_source: Where refund originated (RETURN, CANCELLATION, MANUAL, OTHER)
        return_id: Related return ID (if from return)
        cancel_id: Related cancellation ID (if from cancellation)

        Status fields:
        refund_status: Current status (PENDING, REFUNDED, FAILED)

        Amount fields:
        refund_amount: Amount refunded
        refund_currency: Currency code
        original_amount: Original order amount (for reference)

        Reason fields:
        reason: Refund reason code
        comment: Optional comment from seller

        Buyer Info:
        buyer_username: Buyer's eBay username

        Reference fields:
        refund_reference_id: eBay reference ID
        transaction_id: Payment transaction ID

        Date fields:
        refund_date: When refund was processed
        creation_date: When refund was initiated

        Metadata:
        raw_data: Full eBay API response (for debugging)
        created_at: Record creation timestamp
        updated_at: Record update timestamp
    """

    __tablename__ = "ebay_refunds"
    __table_args__ = {"schema": "tenant"}  # Placeholder for schema_translate_map

    # Primary Key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # Refund Identification
    refund_id: Mapped[str] = mapped_column(
        Text, nullable=False, unique=True, index=True
    )
    order_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("tenant.ebay_orders.order_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Source (where did this refund come from?)
    refund_source: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, index=True
    )  # RETURN, CANCELLATION, MANUAL, OTHER
    return_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True, index=True)
    cancel_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True, index=True)

    # Status
    refund_status: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, index=True
    )  # PENDING, REFUNDED, FAILED

    # Amount
    refund_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    refund_currency: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    original_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Reason
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Buyer Info
    buyer_username: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Reference IDs
    refund_reference_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    transaction_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Line Item (for partial refunds)
    line_item_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Dates
    refund_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    creation_date: Mapped[Optional[datetime]] = mapped_column(
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
            f"<EbayRefund(refund_id='{self.refund_id}', "
            f"status='{self.refund_status}', amount={self.refund_amount})>"
        )

    @property
    def is_completed(self) -> bool:
        """Check if refund has been processed."""
        return self.refund_status == "REFUNDED"

    @property
    def is_pending(self) -> bool:
        """Check if refund is still pending."""
        return self.refund_status == "PENDING"

    @property
    def is_failed(self) -> bool:
        """Check if refund failed."""
        return self.refund_status == "FAILED"

    @property
    def is_from_return(self) -> bool:
        """Check if refund is from a return."""
        return self.refund_source == "RETURN" or self.return_id is not None

    @property
    def is_from_cancellation(self) -> bool:
        """Check if refund is from a cancellation."""
        return self.refund_source == "CANCELLATION" or self.cancel_id is not None

    @property
    def is_manual(self) -> bool:
        """Check if refund was manually issued by seller."""
        return self.refund_source == "MANUAL"
