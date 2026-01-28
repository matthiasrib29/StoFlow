"""
Pending Action Model - Schema Utilisateur

Represents an action detected by sync workflows that requires user confirmation
before being applied (e.g., marking a product as sold or deleting it).

Business Rules (2026-01-22):
- Created when sync detects a product sold/deleted on marketplace
- Product is set to PENDING_DELETION status until user confirms
- User can confirm (apply action) or reject (restore to PUBLISHED)
- Bulk confirm/reject supported
- History preserved via confirmed_at timestamp
"""

from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base


class PendingActionType(str, Enum):
    """Types of pending actions detected by sync workflows."""
    MARK_SOLD = "mark_sold"                       # Product sold on marketplace
    DELETE = "delete"                             # Product deleted from marketplace
    ARCHIVE = "archive"                          # Product to archive
    DELETE_VINTED_LISTING = "delete_vinted_listing"  # StoFlow SOLD but Vinted listing still active
    DELETE_EBAY_LISTING = "delete_ebay_listing"      # StoFlow SOLD but eBay listing still active


class PendingAction(Base):
    """
    Pending action awaiting user confirmation.

    Table: user_{id}.pending_actions

    Created by sync workflows when a product state change is detected
    on a marketplace. The user must confirm or reject the action.
    """

    __tablename__ = "pending_actions"
    __table_args__ = (
        Index("idx_pending_actions_product", "product_id"),
        Index("idx_pending_actions_confirmed", "confirmed_at"),
        Index("idx_pending_actions_marketplace", "marketplace"),
        {"schema": "tenant"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tenant.products.id", ondelete="CASCADE"),
        nullable=False,
        comment="Product concerned by this action"
    )

    action_type: Mapped[PendingActionType] = mapped_column(
        SQLEnum(
            PendingActionType,
            values_callable=lambda x: [e.value for e in x],
            name="pending_action_type"
        ),
        nullable=False,
        comment="Type of action to apply"
    )

    marketplace: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Source marketplace (vinted, ebay, etsy)"
    )

    reason: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Human-readable explanation of why this action was detected"
    )

    # Context data (sale price, buyer info, etc.)
    context_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional context (sale price, marketplace item id, etc.)"
    )

    # Previous status before PENDING_DELETION (to restore on reject)
    previous_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Product status before being set to PENDING_DELETION"
    )

    # Timestamps
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="When the action was detected by sync"
    )

    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the user confirmed or rejected the action"
    )

    confirmed_by: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Who confirmed (user_id or 'auto')"
    )

    # Whether the action was confirmed (True) or rejected (False)
    is_confirmed: Mapped[bool | None] = mapped_column(
        nullable=True,
        comment="True=confirmed (action applied), False=rejected (restored), None=pending"
    )

    # TTL: auto-expire stale pending actions (Issue #3 - Audit)
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Auto-expire unconfirmed actions after this date (default: 7 days)"
    )

    # Relationships
    product = relationship("Product", back_populates="pending_actions", lazy="raise")

    def __repr__(self) -> str:
        return (
            f"<PendingAction(id={self.id}, product_id={self.product_id}, "
            f"action={self.action_type}, marketplace={self.marketplace})>"
        )

    @property
    def is_pending(self) -> bool:
        """Check if action is still pending confirmation."""
        return self.confirmed_at is None
