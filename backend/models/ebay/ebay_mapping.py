"""
eBay Mapping Model

Maps Stoflow categories to eBay categories (simple category + gender mapping).
Shared across all tenants (ebay schema).

Author: Claude
Date: 2026-01-23
"""

from sqlalchemy import Boolean, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base


class EbayMapping(Base):
    """
    Stoflow to eBay category mapping.

    Maps Stoflow categories (category + gender) to eBay category IDs.
    Unlike Vinted mapping, no attribute-based filtering is needed since
    eBay categories are less granular.

    Table: ebay.mapping
    """

    __tablename__ = "mapping"
    __table_args__ = (
        UniqueConstraint("my_category", "my_gender", name="uq_ebay_mapping_category_gender"),
        {"schema": "ebay"},
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    # Stoflow side
    my_category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="StoFlow category (name_en from product_attributes.categories)",
    )

    my_gender: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Gender: men, women, boys, girls",
    )

    # eBay side
    ebay_category_id: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="FK to ebay.categories.category_id",
    )

    is_default: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
        comment="True = default for reverse mapping (eBay -> StoFlow)",
    )

    # Relationships
    ebay_category: Mapped["EbayCategory"] = relationship(
        "EbayCategory",
        foreign_keys=[ebay_category_id],
        primaryjoin="EbayMapping.ebay_category_id == EbayCategory.category_id",
    )

    def __repr__(self) -> str:
        return (
            f"<EbayMapping(id={self.id}, "
            f"my_category={self.my_category}, my_gender={self.my_gender}, "
            f"ebay_category_id={self.ebay_category_id}, is_default={self.is_default})>"
        )
