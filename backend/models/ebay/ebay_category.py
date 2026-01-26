"""
eBay Category Model

Stores eBay's category hierarchy for clothing items (EBAY_GB marketplace).
Shared across all tenants (ebay schema).

Author: Claude
Date: 2026-01-23
"""

from sqlalchemy import Boolean, ForeignKey, Index, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from shared.database import Base


class EbayCategory(Base):
    """
    eBay category hierarchy.

    Stores eBay's internal category structure with parent-child relationships.
    Used for mapping Stoflow products to eBay categories when listing.

    Table: ebay.categories
    """

    __tablename__ = "categories"
    __table_args__ = (
        Index("ix_ebay_categories_parent_id", "parent_id"),
        Index("ix_ebay_categories_level", "level"),
        Index("ix_ebay_categories_is_leaf", "is_leaf"),
        Index("ix_ebay_categories_category_name", "category_name"),
        {"schema": "ebay"},
    )

    category_id: Mapped[str] = mapped_column(
        String(20),
        primary_key=True,
        comment="eBay category ID (natural key)",
    )

    category_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Category name (English, EBAY_GB)",
    )

    parent_id: Mapped[str | None] = mapped_column(
        String(20),
        ForeignKey("ebay.categories.category_id", ondelete="CASCADE"),
        nullable=True,
        comment="Parent category ID",
    )

    level: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        comment="Level in the category tree (0 = root)",
    )

    is_leaf: Mapped[bool] = mapped_column(
        Boolean,
        server_default="false",
        nullable=False,
        comment="True if category is a leaf (can be used for listing)",
    )

    path: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
        comment="Full breadcrumb path (e.g., Clothing > Men > T-Shirts)",
    )

    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        comment="Record creation timestamp",
    )

    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Record last update timestamp",
    )

    # Relationships
    parent: Mapped["EbayCategory | None"] = relationship(
        "EbayCategory",
        remote_side=[category_id],
        back_populates="children",
    )

    children: Mapped[list["EbayCategory"]] = relationship(
        "EbayCategory",
        back_populates="parent",
    )

    def __repr__(self) -> str:
        return f"<EbayCategory(id={self.category_id}, name={self.category_name}, level={self.level})>"
