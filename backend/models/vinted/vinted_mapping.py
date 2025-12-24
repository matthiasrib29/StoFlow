"""
Vinted Mapping Model

Maps Stoflow categories to Vinted categories with attribute filtering.
Shared across all tenants (vinted schema).

Author: Claude
Date: 2025-12-24
"""

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base


class VintedMapping(Base):
    """
    Stoflow to Vinted category mapping.

    Maps Stoflow categories (with optional attributes like fit, length, etc.)
    to Vinted category IDs. Supports default mappings per category+gender pair.

    Table: vinted.mapping
    """

    __tablename__ = "mapping"
    __table_args__ = {"schema": "vinted"}

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    # Vinted side
    vinted_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vinted.categories.id"),
        nullable=False,
        comment="FK to vinted.categories"
    )

    vinted_gender: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Gender from Vinted category"
    )

    # Stoflow side
    my_category: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("product_attributes.categories.name_en"),
        nullable=False,
        comment="FK to categories"
    )

    my_gender: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="men, women, boys, girls"
    )

    # Optional attribute filters
    my_fit: Mapped[str | None] = mapped_column(
        String(50),
        ForeignKey("product_attributes.fits.name_en", onupdate="CASCADE", ondelete="SET NULL"),
        nullable=True
    )

    my_length: Mapped[str | None] = mapped_column(
        String(50),
        ForeignKey("product_attributes.lengths.name_en", onupdate="CASCADE", ondelete="SET NULL"),
        nullable=True
    )

    my_rise: Mapped[str | None] = mapped_column(
        String(50),
        ForeignKey("product_attributes.rises.name_en", onupdate="CASCADE", ondelete="SET NULL"),
        nullable=True
    )

    my_material: Mapped[str | None] = mapped_column(
        String(50),
        ForeignKey("product_attributes.materials.name_en", onupdate="CASCADE", ondelete="SET NULL"),
        nullable=True
    )

    my_pattern: Mapped[str | None] = mapped_column(
        String(50),
        ForeignKey("product_attributes.patterns.name_en", onupdate="CASCADE", ondelete="SET NULL"),
        nullable=True
    )

    my_neckline: Mapped[str | None] = mapped_column(
        String(50),
        ForeignKey("product_attributes.necklines.name_en", onupdate="CASCADE", ondelete="SET NULL"),
        nullable=True
    )

    my_sleeve_length: Mapped[str | None] = mapped_column(
        String(50),
        ForeignKey("product_attributes.sleeve_lengths.name_en", onupdate="CASCADE", ondelete="SET NULL"),
        nullable=True
    )

    is_default: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="True if this is the default mapping for the category+gender pair"
    )

    # Relationships
    vinted_category: Mapped["VintedCategory"] = relationship(
        "VintedCategory",
        foreign_keys=[vinted_id]
    )

    def __repr__(self) -> str:
        return (
            f"<VintedMapping(id={self.id}, "
            f"my_category={self.my_category}, my_gender={self.my_gender}, "
            f"vinted_id={self.vinted_id}, is_default={self.is_default})>"
        )
