"""
eBay Promoted Listing Model - User Schema

Tracks products in eBay Promoted Listings campaigns.
Each record = 1 product in 1 campaign with performance metrics.

Business Rules:
- Relates to products via sku_original (main FK)
- sku_derived is calculated (not a FK)
- Metrics updated periodically via eBay API
- ad_id is unique across all campaigns
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class EbayPromotedListing(Base):
    """
    eBay Promoted Listing - Tracks promoted products and metrics.

    Attributes:
        id: Primary key
        campaign_id: eBay campaign ID
        campaign_name: Campaign name
        marketplace_id: Marketplace (EBAY_FR, EBAY_GB, etc.)
        product_id: FK to products.id (main relation)
        sku_derived: Derived SKU (calculated, not FK)
        ad_id: Unique eBay ad ID
        listing_id: eBay listing ID (reference)
        bid_percentage: Bid percentage (2.0-100.0)
        ad_status: Status (ACTIVE, PAUSED, ENDED)
        total_clicks: Total clicks
        total_impressions: Total impressions
        total_sales: Total sales count
        total_sales_amount: Total sales amount
        total_ad_fees: Total advertising fees
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "ebay_promoted_listings"
    __table_args__ = {"schema": "tenant"}  # Placeholder for schema_translate_map

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Campaign Info
    campaign_id: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    campaign_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    marketplace_id: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )

    # Product Info - Main FK to products
    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sku_derived: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # Calculated, not FK

    # Ad Info
    ad_id: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True
    )
    listing_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    bid_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False
    )
    ad_status: Mapped[str] = mapped_column(
        String(20), default="ACTIVE", nullable=False, index=True
    )

    # Performance Metrics
    total_clicks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_impressions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_sales: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_sales_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), nullable=False
    )
    total_ad_fees: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), nullable=False
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    @property
    def ctr(self) -> float:
        """
        Click-Through Rate (CTR).
        Percentage of clicks per impressions.
        """
        if self.total_impressions == 0:
            return 0.0
        return (self.total_clicks / self.total_impressions) * 100

    @property
    def conversion_rate(self) -> float:
        """
        Conversion Rate.
        Percentage of sales per clicks.
        """
        if self.total_clicks == 0:
            return 0.0
        return (self.total_sales / self.total_clicks) * 100

    @property
    def roi(self) -> float:
        """
        Return On Investment (ROI).
        (Sales - Ad Fees) / Ad Fees * 100
        """
        if float(self.total_ad_fees) == 0:
            return 0.0
        profit = float(self.total_sales_amount) - float(self.total_ad_fees)
        return (profit / float(self.total_ad_fees)) * 100

    @property
    def cpa(self) -> float:
        """
        Cost Per Acquisition (CPA).
        Ad Fees / Number of Sales
        """
        if self.total_sales == 0:
            return 0.0
        return float(self.total_ad_fees) / self.total_sales

    def __repr__(self) -> str:
        return (
            f"<EbayPromotedListing(id={self.id}, "
            f"sku_derived='{self.sku_derived}', "
            f"marketplace='{self.marketplace_id}', "
            f"campaign='{self.campaign_id}', "
            f"status='{self.ad_status}')>"
        )
