"""
eBay Product Marketplace Model - User Schema

Tracks products published on each eBay marketplace.
N:N relationship between products and marketplaces.
Each row = 1 listing on 1 marketplace.

Business Rules:
- PK: sku_derived (e.g., "1234-FR") - unique per product per marketplace
- FK: sku_original → products.sku (CASCADE delete)
- Status: draft, published, sold, error, deleted
- Stores eBay offer_id, listing_id, and error messages
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class EbayProductMarketplace(Base):
    """
    eBay Product Marketplace - Tracks products published per marketplace.

    Attributes:
        sku_derived: Primary key - derived SKU (e.g., "1234-FR")
        product_id: Foreign key to products.id
        marketplace_id: Marketplace identifier (EBAY_FR, EBAY_GB, etc.)
        ebay_offer_id: eBay Offer ID
        ebay_listing_id: eBay published listing ID
        status: Publication status (draft, published, sold, error, deleted)
        error_message: Error message if publication failed
        published_at: Publication timestamp
        sold_at: Sale timestamp
        last_sync_at: Last synchronization timestamp
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "ebay_products_marketplace"
    __table_args__ = {"schema": "tenant"}  # Placeholder for schema_translate_map

    # Primary Key
    sku_derived: Mapped[str] = mapped_column(
        String(50), primary_key=True, nullable=False
    )

    # Foreign Keys
    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    marketplace_id: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )

    # eBay IDs
    ebay_offer_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    ebay_listing_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True, index=True
    )

    # Status & Error
    status: Mapped[str] = mapped_column(
        String(20), default="draft", nullable=False, index=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sold_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
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
            f"<EbayProductMarketplace(sku_derived='{self.sku_derived}', "
            f"marketplace='{self.marketplace_id}', status='{self.status}')>"
        )
