"""
VintedOrder Model - Schema vinted

Stores Vinted orders/sales (shared table).

Business Rules (2025-12-12):
- One order = one Vinted transaction
- transaction_id = primary key (Vinted ID)
- Stores buyer/seller info and shipping details
- Related table: vinted_order_products for items

Author: Claude
Date: 2025-12-12
Updated: 2025-12-24 - Moved to vinted schema
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Numeric, String, Text, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base


class VintedOrder(Base):
    """
    Vinted orders/sales.

    Table: vinted.orders
    """

    __tablename__ = "orders"
    __table_args__ = (
        Index('idx_orders_buyer_id', 'buyer_id'),
        Index('idx_orders_status', 'status'),
        Index('idx_orders_created_at_vinted', 'created_at_vinted'),
        {"schema": "vinted"}
    )

    # Primary Key = Vinted transaction_id
    transaction_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        comment="Vinted transaction ID (PK)"
    )

    # Vinted IDs (for linking to other Vinted entities)
    conversation_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="Vinted conversation/thread ID (for messages)"
    )
    offer_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="Vinted offer ID"
    )

    # Participants - Buyer
    buyer_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="Vinted buyer ID"
    )
    buyer_login: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Buyer login"
    )
    buyer_photo_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Buyer profile photo URL"
    )
    buyer_country_code: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="Buyer country code (FR, DE, etc.)"
    )
    buyer_city: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Buyer city"
    )
    buyer_feedback_reputation: Mapped[float | None] = mapped_column(
        Numeric(3, 2),
        nullable=True,
        comment="Buyer reputation score (0-5)"
    )

    # Participants - Seller
    seller_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="Vinted seller ID"
    )
    seller_login: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Seller login"
    )

    # Status (multiple representations)
    status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Order status (completed/pending/refunded)"
    )
    vinted_status_code: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Vinted status code (230=paid, 400+=completed)"
    )
    vinted_status_text: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Vinted status text FR (Le paiement a été validé)"
    )
    transaction_user_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="User action status (needs_action/waiting/completed/failed)"
    )

    # Item count (for bundles)
    item_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        server_default='1',
        comment="Number of items in order"
    )

    # Amounts
    total_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Total price"
    )
    currency: Mapped[str | None] = mapped_column(
        String(3),
        nullable=True,
        server_default='EUR',
        comment="Currency"
    )
    shipping_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Shipping cost"
    )
    service_fee: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Service fee"
    )
    buyer_protection_fee: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Buyer protection fee"
    )
    seller_revenue: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Net seller revenue"
    )

    # Shipping
    tracking_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Tracking number"
    )
    carrier: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Carrier"
    )

    # Vinted dates
    created_at_vinted: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Vinted creation date"
    )
    shipped_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Shipping date"
    )
    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Delivery date"
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Completion date"
    )

    # System timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Local creation date"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Local update date"
    )

    # Relationships
    products: Mapped[list["VintedOrderProduct"]] = relationship(
        "VintedOrderProduct",
        back_populates="order",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<VintedOrder(transaction_id={self.transaction_id}, "
            f"buyer_login={self.buyer_login}, status={self.status}, "
            f"total_price={self.total_price})>"
        )


class VintedOrderProduct(Base):
    """
    Products in a Vinted order.

    Table: vinted.order_products
    """

    __tablename__ = "order_products"
    __table_args__ = (
        Index('idx_order_products_transaction_id', 'transaction_id'),
        Index('idx_order_products_vinted_item_id', 'vinted_item_id'),
        Index('idx_order_products_product_id', 'product_id'),
        {"schema": "vinted"}
    )

    # Primary Key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    # Foreign Key to VintedOrder
    transaction_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("vinted.orders.transaction_id", ondelete="CASCADE"),
        nullable=False,
        comment="FK to vinted.orders"
    )

    # IDs
    vinted_item_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="Vinted item ID"
    )
    product_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="Stoflow product ID"
    )

    # Product details
    title: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Product title"
    )
    price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Unit price"
    )
    size: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Size"
    )
    brand: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Brand"
    )
    photo_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Main photo URL"
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationship
    order: Mapped["VintedOrder"] = relationship(
        "VintedOrder",
        back_populates="products"
    )

    def __repr__(self) -> str:
        return (
            f"<VintedOrderProduct(id={self.id}, transaction_id={self.transaction_id}, "
            f"vinted_item_id={self.vinted_item_id}, title={self.title})>"
        )
