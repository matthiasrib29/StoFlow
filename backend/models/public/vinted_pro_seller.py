"""
Vinted Pro Seller Model

Model for storing discovered Vinted professional (business) sellers.
Admin-only feature for finding and tracking pro sellers on Vinted.

Author: Claude
Date: 2026-01-27
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, DateTime, Index, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class VintedProSeller(Base):
    """
    Vinted professional seller discovered via user search API.

    Stores complete information about business=true Vinted sellers,
    including extracted contact info from their 'about' field.

    Table: public.vinted_pro_sellers
    """

    __tablename__ = "vinted_pro_sellers"
    __table_args__ = (
        Index("idx_vinted_pro_sellers_vinted_user_id", "vinted_user_id", unique=True),
        Index("idx_vinted_pro_sellers_country_code", "country_code"),
        Index("idx_vinted_pro_sellers_marketplace", "marketplace"),
        Index("idx_vinted_pro_sellers_status", "status"),
        Index("idx_vinted_pro_sellers_item_count", "item_count"),
        Index("idx_vinted_pro_sellers_legal_code", "legal_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # --- Vinted user data ---
    vinted_user_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False, unique=True, comment="Vinted user ID"
    )
    login: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Vinted username"
    )
    country_code: Mapped[str | None] = mapped_column(
        String(10), nullable=True, comment="Country code (FR, DE, etc.)"
    )
    country_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Vinted country ID"
    )
    country_title: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Country title (France, etc.)"
    )

    # --- Seller stats ---
    item_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="Number of active items for sale"
    )
    total_items_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="Total items ever listed"
    )
    given_item_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="Items given away"
    )
    taken_item_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="Items taken/purchased"
    )
    followers_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="Number of followers"
    )
    following_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="Number of following"
    )
    feedback_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="Number of feedback reviews"
    )
    feedback_reputation: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True, comment="Feedback reputation score (0-5)"
    )
    positive_feedback_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="Positive feedback count"
    )
    neutral_feedback_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="Neutral feedback count"
    )
    negative_feedback_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="Negative feedback count"
    )
    is_on_holiday: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="Is on holiday mode"
    )

    # --- Business account info ---
    business_account_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="Business account ID"
    )
    business_name: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Business commercial name"
    )
    legal_name: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Legal name (first/last)"
    )
    legal_code: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="SIRET / legal code"
    )
    entity_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="Entity type code"
    )
    entity_type_title: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Entity type title"
    )
    nationality: Mapped[str | None] = mapped_column(
        String(10), nullable=True, comment="Nationality code"
    )
    business_country: Mapped[str | None] = mapped_column(
        String(10), nullable=True, comment="Business country code"
    )
    business_city: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Business city"
    )
    verified_identity: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True, comment="Identity verified"
    )
    business_is_active: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True, comment="Business account is active"
    )

    # --- Profile ---
    about: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Bio/about text (raw)"
    )
    profile_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="URL to Vinted profile"
    )
    last_loged_on_ts: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="Last login timestamp from API"
    )

    # --- Extracted contacts (from about field) ---
    contact_email: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Extracted email from about"
    )
    contact_instagram: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Extracted Instagram handle"
    )
    contact_tiktok: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Extracted TikTok handle"
    )
    contact_youtube: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="Extracted YouTube channel"
    )
    contact_website: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="Extracted website URL"
    )
    contact_phone: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="Extracted phone number"
    )

    # --- Metadata ---
    marketplace: Mapped[str] = mapped_column(
        String(20), default="vinted_fr", nullable=False, comment="Marketplace origin"
    )
    status: Mapped[str] = mapped_column(
        String(50), default="new", nullable=False,
        comment="Prospection status: new, contacted, converted, ignored"
    )
    notes: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Admin notes"
    )

    # --- Timestamps ---
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
        comment="When this seller was discovered"
    )
    last_scanned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
        comment="Last time data was scanned/updated"
    )
    contacted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="When the seller was contacted"
    )
    created_by: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Admin user ID who triggered discovery"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
        nullable=False, comment="Last modification timestamp"
    )

    def __repr__(self) -> str:
        return (
            f"<VintedProSeller(id={self.id}, login={self.login}, "
            f"business_name={self.business_name}, items={self.item_count}, status={self.status})>"
        )
