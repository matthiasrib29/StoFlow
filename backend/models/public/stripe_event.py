"""
Stripe Event Model - Track processed Stripe webhook events for idempotency.

Stores event IDs to prevent duplicate processing of webhooks.
Index on event_id for fast lookup.

Security Fix 2026-01-20: Stripe webhook idempotency

Author: Claude
Date: 2026-01-20
"""

from datetime import datetime
from sqlalchemy import Index, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base
from shared.datetime_utils import utc_now


class StripeEvent(Base):
    """
    Processed Stripe webhook event.

    Tracks which Stripe events have been processed to prevent duplicate handling.
    """

    __tablename__ = "stripe_events"
    __table_args__ = (
        Index("idx_stripe_events_event_id", "event_id", unique=True),
        Index("idx_stripe_events_processed_at", "processed_at"),
    )

    # Primary key: Stripe event ID (e.g., "evt_1234...")
    event_id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
        index=True,
        doc="Stripe event ID"
    )

    # Event type (e.g., "checkout.session.completed")
    event_type: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Stripe event type"
    )

    # Processing result
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="processed",
        doc="Processing status (processed, failed, skipped)"
    )

    # Error message if processing failed
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Error message if processing failed"
    )

    # Timestamps
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        doc="Timestamp when event was processed"
    )

    def __repr__(self) -> str:
        return f"<StripeEvent event_id={self.event_id} type={self.event_type} status={self.status}>"
