"""
EbayMarketplaceSettings Model - Schema user_{id}

Per-marketplace eBay configuration: business policies, inventory location, and pricing.

Business Rules:
- One row per marketplace per user (e.g. EBAY_FR, EBAY_GB)
- Stores business policy IDs (payment, fulfillment, return)
- Stores inventory location key
- Pricing: coefficient + fee applied to base price
- Replaces the old platform_mappings approach

Author: Claude
Date: 2026-01-26
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class EbayMarketplaceSettings(Base):
    """
    Per-marketplace eBay settings for a user.

    Each row holds the business policies, inventory location,
    and pricing rules for one eBay marketplace (EBAY_FR, EBAY_GB, etc.).
    """

    __tablename__ = "ebay_marketplace_settings"
    __table_args__ = {"schema": "tenant"}  # Placeholder for schema_translate_map

    # Primary Key
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )

    # Marketplace identifier (EBAY_FR, EBAY_GB, EBAY_DE, etc.)
    marketplace_id: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
        comment="eBay marketplace ID (EBAY_FR, EBAY_GB, etc.)",
    )

    # Business Policies
    payment_policy_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="eBay payment policy ID",
    )
    fulfillment_policy_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="eBay fulfillment (shipping) policy ID",
    )
    return_policy_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="eBay return policy ID",
    )

    # Inventory Location
    inventory_location_key: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="eBay inventory location key",
    )

    # Pricing
    price_coefficient: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        server_default="1.00",
        comment="Price multiplier (e.g. 1.10 = +10%)",
    )
    price_fee: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        server_default="0.00",
        comment="Flat fee added to price (in marketplace currency)",
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
        comment="Whether this marketplace is enabled for the user",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<EbayMarketplaceSettings("
            f"id={self.id}, "
            f"marketplace_id='{self.marketplace_id}', "
            f"is_active={self.is_active})>"
        )
