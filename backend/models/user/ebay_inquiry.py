"""
eBay Inquiry Model - User Schema

Stores eBay INR (Item Not Received) inquiries from Post-Order API v2.
Linked to EbayOrder for order context.

Business Rules:
- inquiry_id is unique per user schema
- Links to ebay_orders via order_id FK
- inquiry_status tracks the inquiry workflow state
- respond_by_date is critical for seller metrics
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class EbayInquiry(Base):
    """
    eBay Inquiry - INR (Item Not Received) inquiry information.

    Attributes:
        id: Primary key (auto-increment)
        inquiry_id: eBay inquiry ID (e.g., "5000012345") - unique
        order_id: FK to ebay_orders.order_id (legacy order ID)

        Status fields:
        inquiry_state: High-level state (OPEN, CLOSED)
        inquiry_status: Current status (INR_WAITING_FOR_SELLER, etc.)
        inquiry_type: Type of inquiry (INR = Item Not Received)

        Claim fields:
        claim_amount: Amount claimed by buyer
        claim_currency: Currency code

        Buyer/Seller fields:
        buyer_username: Buyer's eBay username
        buyer_comments: Buyer's inquiry message
        seller_response: Seller's response type

        Item fields:
        item_id: eBay item ID
        item_title: Item title for reference

        Shipping (if tracking provided):
        shipment_tracking_number: Tracking number provided
        shipment_carrier: Shipping carrier

        Date fields:
        creation_date: When inquiry was created on eBay
        respond_by_date: Deadline for seller response
        closed_date: When inquiry was closed
        escalation_date: When escalated to case (if applicable)

        Metadata:
        raw_data: Full eBay API response (for debugging)
        created_at: Record creation timestamp
        updated_at: Record update timestamp
    """

    __tablename__ = "ebay_inquiries"
    __table_args__ = {"schema": "tenant"}  # Placeholder for schema_translate_map

    # Primary Key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # Inquiry Identification
    inquiry_id: Mapped[str] = mapped_column(
        Text, nullable=False, unique=True, index=True
    )
    order_id: Mapped[Optional[str]] = mapped_column(
        Text,
        ForeignKey("tenant.ebay_orders.order_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Status
    inquiry_state: Mapped[Optional[str]] = mapped_column(Text, nullable=True, index=True)
    inquiry_status: Mapped[Optional[str]] = mapped_column(Text, nullable=True, index=True)
    inquiry_type: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Claim Amount
    claim_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    claim_currency: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Buyer Info
    buyer_username: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    buyer_comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Seller Response
    seller_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Item Info
    item_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True, index=True)
    item_title: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Shipment Info (if tracking provided)
    shipment_tracking_number: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    shipment_carrier: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Dates
    creation_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    respond_by_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    closed_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    escalation_date: Mapped[Optional[datetime]] = mapped_column(
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
            f"<EbayInquiry(inquiry_id='{self.inquiry_id}', "
            f"status='{self.inquiry_status}', order_id='{self.order_id}')>"
        )

    @property
    def is_open(self) -> bool:
        """Check if inquiry is still open."""
        return self.inquiry_state == "OPEN"

    @property
    def needs_action(self) -> bool:
        """Check if inquiry requires seller action."""
        action_needed_statuses = [
            "INR_WAITING_FOR_SELLER",
        ]
        return self.inquiry_status in action_needed_statuses

    @property
    def is_past_due(self) -> bool:
        """Check if response deadline has passed."""
        if not self.respond_by_date:
            return False
        from datetime import timezone
        return datetime.now(timezone.utc) > self.respond_by_date

    @property
    def is_escalated(self) -> bool:
        """Check if inquiry was escalated to a case."""
        return self.inquiry_status == "INR_ESCALATED"
