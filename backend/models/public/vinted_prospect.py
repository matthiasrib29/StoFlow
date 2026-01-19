"""
Vinted Prospect Model

Model for storing discovered Vinted users for prospection purposes.
Admin-only feature for finding potential power sellers on Vinted FR.

Author: Claude
Date: 2026-01-19
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, DateTime, Index, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class VintedProspect(Base):
    """
    Vinted user discovered for prospection.

    Stores information about Vinted sellers found via user search API.
    Used by admins to identify and contact potential power sellers.

    Table: public.vinted_prospects
    """

    __tablename__ = "vinted_prospects"
    __table_args__ = (
        Index("idx_vinted_prospects_country", "country_code"),
        Index("idx_vinted_prospects_item_count", "item_count"),
        Index("idx_vinted_prospects_status", "status"),
        Index("idx_vinted_prospects_vinted_user_id", "vinted_user_id", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Vinted user data
    vinted_user_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        unique=True,
        comment="Vinted user ID"
    )
    login: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Vinted username"
    )
    country_code: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="Country code (FR, DE, etc.)"
    )

    # Seller stats
    item_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of active items for sale"
    )
    total_items_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Total items ever listed"
    )
    feedback_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of feedback reviews"
    )
    feedback_reputation: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Feedback reputation score (0-5)"
    )
    is_business: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Is a business account"
    )
    profile_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="URL to Vinted profile"
    )

    # Prospection tracking
    status: Mapped[str] = mapped_column(
        String(50),
        default="new",
        nullable=False,
        comment="Prospection status: new, contacted, converted, ignored"
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Admin notes about this prospect"
    )

    # Timestamps
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="When this user was discovered"
    )
    last_synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Last time stats were synced"
    )
    contacted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the prospect was contacted"
    )
    created_by: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Admin user ID who triggered the discovery"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Last modification timestamp"
    )

    def __repr__(self) -> str:
        return f"<VintedProspect(id={self.id}, login={self.login}, items={self.item_count}, status={self.status})>"
