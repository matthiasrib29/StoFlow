"""
Marketplace Action Type Model

Unified action types for all marketplaces (Vinted, eBay, Etsy).
Shared across all tenants (public schema).

Business Rules (2026-01-09):
- One table for all marketplaces with 'marketplace' column
- Unique constraint on (marketplace, code)
- Replaces separate vinted.action_types, ebay.action_types, etsy.action_types

Author: Claude
Date: 2026-01-09
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class MarketplaceActionType(Base):
    """
    Unified action types for all marketplaces.

    Defines the different types of actions that can be performed on each marketplace,
    along with their priority, rate limiting, and retry configuration.

    Table: public.marketplace_action_types
    """

    __tablename__ = "marketplace_action_types"
    __table_args__ = (
        UniqueConstraint("marketplace", "code", name="uq_marketplace_action_types_marketplace_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    marketplace: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Target marketplace: 'vinted', 'ebay', 'etsy'"
    )

    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Action code: publish, sync, orders, message, update, delete, etc."
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Display name"
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    priority: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False,
        comment="1=CRITICAL, 2=HIGH, 3=NORMAL, 4=LOW"
    )

    is_batch: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="True if action processes multiple items"
    )

    rate_limit_ms: Mapped[int] = mapped_column(
        Integer,
        default=2000,
        nullable=False,
        comment="Delay between requests in ms"
    )

    max_retries: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False
    )

    timeout_seconds: Mapped[int] = mapped_column(
        Integer,
        default=60,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<MarketplaceActionType(marketplace={self.marketplace}, code={self.code}, priority={self.priority})>"
