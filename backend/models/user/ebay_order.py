"""
eBay Order Models - User Schema

Stores eBay orders and order line items.
Retrieved via eBay Fulfillment API.

Business Rules:
- EbayOrder: Main order with buyer and shipping info
- EbayOrderProduct: Line items (products sold in order)
- Order ID is unique per user
- FK relationship: order_products.order_id → orders.order_id
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base

if TYPE_CHECKING:
    from models.user.ebay_order import EbayOrderProduct


class EbayOrder(Base):
    """
    eBay Order - Main order information.

    Attributes:
        id: Primary key (auto-increment)
        order_id: eBay order ID (e.g., "12-12345-12345") - unique
        marketplace_id: Marketplace (EBAY_FR, EBAY_GB, etc.)
        buyer_username: Buyer's eBay username
        buyer_email: Buyer's email
        shipping_name: Shipping recipient name
        shipping_address: Shipping address
        shipping_city: Shipping city
        shipping_postal_code: Postal code
        shipping_country: Country code
        total_price: Total order price
        currency: Currency code
        shipping_cost: Shipping cost
        order_fulfillment_status: Fulfillment status (NOT_STARTED, IN_PROGRESS, FULFILLED)
        order_payment_status: Payment status (PAID, PENDING, etc.)
        creation_date: Order creation date
        paid_date: Payment date
        tracking_number: Shipping tracking number
        shipping_carrier: Carrier name
        created_at: Record creation timestamp
        updated_at: Record update timestamp
    """

    __tablename__ = "ebay_orders"
    # Schema will be set dynamically via search_path
    __table_args__ = {}

    # Primary Key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # Order Identification
    order_id: Mapped[str] = mapped_column(
        Text, nullable=False, unique=True, index=True
    )
    marketplace_id: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, index=True
    )

    # Buyer Information
    buyer_username: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    buyer_email: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Shipping Address
    shipping_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    shipping_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    shipping_city: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    shipping_postal_code: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    shipping_country: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Amounts
    total_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    shipping_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Status
    order_fulfillment_status: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, index=True
    )
    order_payment_status: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Dates
    creation_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    paid_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Tracking
    tracking_number: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    shipping_carrier: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

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

    # Relationship to products (line items)
    products: Mapped[List["EbayOrderProduct"]] = relationship(
        "EbayOrderProduct",
        foreign_keys="EbayOrderProduct.order_id",
        lazy="selectin",  # Auto-load products when fetching order
        cascade="all, delete-orphan",  # Delete products when order is deleted
    )

    def __repr__(self) -> str:
        return (
            f"<EbayOrder(order_id='{self.order_id}', "
            f"marketplace='{self.marketplace_id}', "
            f"total={self.total_price})>"
        )


class EbayOrderProduct(Base):
    """
    eBay Order Product - Line items in an order.

    Attributes:
        id: Primary key (auto-increment)
        order_id: FK to ebay_orders.order_id
        line_item_id: eBay line item ID
        sku: Derived SKU (e.g., "12345-FR")
        sku_original: Original SKU (e.g., "12345")
        title: Product title
        quantity: Quantity sold
        unit_price: Unit price
        total_price: Total line price
        currency: Currency code
        legacy_item_id: eBay legacy item ID (for linking)
        created_at: Record creation timestamp
    """

    __tablename__ = "ebay_orders_products"
    # Schema will be set dynamically via search_path
    __table_args__ = {}

    # Primary Key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # Foreign Key to Order
    order_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("ebay_orders.order_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Product Info
    line_item_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sku: Mapped[Optional[str]] = mapped_column(Text, nullable=True, index=True)
    sku_original: Mapped[Optional[str]] = mapped_column(Text, nullable=True, index=True)
    title: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Pricing
    quantity: Mapped[Optional[int]] = mapped_column(Integer, default=1, nullable=True)
    unit_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Legacy Item ID
    legacy_item_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        title_preview = self.title[:30] if self.title else ""
        return (
            f"<EbayOrderProduct(order_id='{self.order_id}', "
            f"sku='{self.sku}', title='{title_preview}')>"
        )
