"""
eBay Payment Dispute Model.

Stores payment dispute data from eBay Fulfillment API.
Used to track and manage disputes filed by buyers against orders.

Documentation:
- https://developer.ebay.com/api-docs/sell/fulfillment/types/api:PaymentDispute

Author: Claude
Date: 2026-01-14
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class EbayPaymentDispute(Base):
    """
    eBay Payment Dispute model.

    Stores payment dispute information fetched from eBay Fulfillment API.
    Disputes are filed by buyers when they have issues with transactions.

    Dispute States:
    - OPEN: Dispute is active, no seller action required yet
    - ACTION_NEEDED: Seller must respond before deadline
    - CLOSED: Dispute has been resolved

    Dispute Reasons:
    - ITEM_NOT_RECEIVED
    - SIGNIFICANTLY_NOT_AS_DESCRIBED
    - FRAUD
    - COUNTERFEIT
    - DUPLICATE_AMOUNT
    - INCORRECT_AMOUNT
    - CANCELLATION
    - RETURN_REFUND_NOT_PROCESSED
    - etc.

    Seller Responses:
    - CONTEST: Seller disputes the claim
    - ACCEPT: Seller accepts the claim (agrees to refund)
    """

    __tablename__ = "ebay_payment_disputes"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # eBay identifiers
    payment_dispute_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    order_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True
    )

    # Status fields
    dispute_state: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, index=True
    )  # OPEN, ACTION_NEEDED, CLOSED
    reason: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True
    )  # ITEM_NOT_RECEIVED, FRAUD, etc.
    reason_for_closure: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # How dispute was closed

    # Seller response
    seller_response: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # CONTEST, ACCEPT
    note: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # Seller note (max 1000 chars)

    # Amount
    dispute_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    dispute_currency: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Buyer info
    buyer_username: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True
    )

    # Revision (for API calls)
    revision: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Available choices (CONTEST, ACCEPT, etc.)
    available_choices: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Evidence
    evidence: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True
    )  # Evidence provided by seller
    evidence_requests: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True
    )  # Evidence requested by eBay

    # Line items involved
    line_items: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Resolution details (for closed disputes)
    resolution: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Return address (if buyer should return item)
    return_address: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Dates
    open_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    respond_by_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, index=True
    )  # Deadline for seller response
    closed_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Record timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<EbayPaymentDispute(id={self.id}, "
            f"payment_dispute_id='{self.payment_dispute_id}', "
            f"state='{self.dispute_state}', reason='{self.reason}')>"
        )

    # =========================================================================
    # COMPUTED PROPERTIES
    # =========================================================================

    @property
    def is_open(self) -> bool:
        """Check if dispute is open (OPEN or ACTION_NEEDED)."""
        return self.dispute_state in ("OPEN", "ACTION_NEEDED")

    @property
    def is_closed(self) -> bool:
        """Check if dispute is closed."""
        return self.dispute_state == "CLOSED"

    @property
    def needs_action(self) -> bool:
        """Check if dispute requires seller action."""
        return self.dispute_state == "ACTION_NEEDED"

    @property
    def is_past_deadline(self) -> bool:
        """Check if respond_by_date has passed."""
        if not self.respond_by_date:
            return False
        return datetime.now(timezone.utc) > self.respond_by_date

    @property
    def can_contest(self) -> bool:
        """Check if dispute can be contested."""
        if not self.available_choices:
            return False
        return "CONTEST" in self.available_choices

    @property
    def can_accept(self) -> bool:
        """Check if dispute can be accepted."""
        if not self.available_choices:
            return False
        return "ACCEPT" in self.available_choices

    @property
    def was_contested(self) -> bool:
        """Check if seller contested the dispute."""
        return self.seller_response == "CONTEST"

    @property
    def was_accepted(self) -> bool:
        """Check if seller accepted the dispute."""
        return self.seller_response == "ACCEPT"

    @property
    def evidence_count(self) -> int:
        """Get number of evidence items submitted."""
        if not self.evidence:
            return 0
        return len(self.evidence)

    @property
    def evidence_requested_count(self) -> int:
        """Get number of evidence types requested."""
        if not self.evidence_requests:
            return 0
        return len(self.evidence_requests)

    @property
    def days_until_deadline(self) -> Optional[int]:
        """Get number of days until deadline (negative if past)."""
        if not self.respond_by_date:
            return None
        delta = self.respond_by_date - datetime.now(timezone.utc)
        return delta.days

    @property
    def outcome(self) -> Optional[str]:
        """Get dispute outcome if closed."""
        if not self.resolution:
            return None
        return self.resolution.get("outcome")
