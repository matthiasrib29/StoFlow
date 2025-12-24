"""
VintedDeletion Model - Schema vinted

Archives deleted Vinted products with their statistics.
Used for analytics and performance tracking.

Business Rules (2025-12-12):
- Created when a VintedProduct is deleted
- Stores stats at deletion time (views, favorites, etc.)
- Calculates days_active automatically
- Allows analysis of deleted product performance

Author: Claude
Date: 2025-12-12
Updated: 2025-12-24 - Moved to vinted schema
"""

from datetime import date as date_type
from decimal import Decimal

from sqlalchemy import BigInteger, Date, Integer, Numeric, Index
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class VintedDeletion(Base):
    """
    Archive of deleted Vinted products.

    Table: vinted.deletions
    """

    __tablename__ = "deletions"
    __table_args__ = (
        Index('idx_deletions_id_vinted', 'id_vinted'),
        Index('idx_deletions_id_site', 'id_site'),
        Index('idx_deletions_date_deleted', 'date_deleted'),
        Index('idx_deletions_days_active', 'days_active'),
        {"schema": "vinted"}
    )

    # Primary Key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    # External IDs
    id_vinted: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        index=True,
        comment="Vinted product ID (deleted)"
    )
    id_site: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        index=True,
        comment="Stoflow product ID"
    )

    # Price
    price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Price at deletion time"
    )

    # Dates
    date_published: Mapped[date_type | None] = mapped_column(
        Date,
        nullable=True,
        comment="Initial publication date"
    )
    date_deleted: Mapped[date_type | None] = mapped_column(
        Date,
        nullable=True,
        index=True,
        comment="Deletion date"
    )

    # Statistics at deletion time
    view_count: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        default=0,
        comment="View count"
    )
    favourite_count: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        default=0,
        comment="Favorite count"
    )
    conversations: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        default=0,
        comment="Conversation count"
    )

    # Lifetime
    days_active: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
        comment="Days online"
    )

    def __repr__(self) -> str:
        return (
            f"<VintedDeletion(id={self.id}, id_vinted={self.id_vinted}, "
            f"days_active={self.days_active})>"
        )

    @classmethod
    def from_vinted_product(cls, vinted_product) -> "VintedDeletion":
        """
        Create a VintedDeletion from a VintedProduct.

        Args:
            vinted_product: VintedProduct instance to archive

        Returns:
            VintedDeletion: Instance ready to persist
        """
        from datetime import date

        # Calculate days_active
        days_active = None
        if vinted_product.date:
            delta = date.today() - vinted_product.date
            days_active = delta.days

        return cls(
            id_vinted=vinted_product.vinted_id,
            id_site=vinted_product.product_id,
            price=vinted_product.price,
            date_published=vinted_product.date,
            date_deleted=date.today(),
            view_count=vinted_product.view_count or 0,
            favourite_count=vinted_product.favourite_count or 0,
            conversations=vinted_product.conversations or 0,
            days_active=days_active
        )
