"""
Vinted Category Model

Stores Vinted's category hierarchy for clothing items.
Shared across all tenants (vinted schema).

Author: Claude
Date: 2025-12-24
"""

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base


class VintedCategory(Base):
    """
    Vinted category hierarchy.

    Stores Vinted's internal category structure with parent-child relationships.
    Used for mapping Stoflow categories to Vinted categories.

    Table: vinted.categories
    """

    __tablename__ = "categories"
    __table_args__ = {"schema": "vinted"}

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        comment="Vinted category ID"
    )

    code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Vinted category code"
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Category title"
    )

    parent_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("vinted.categories.id", ondelete="CASCADE"),
        nullable=True,
        comment="Parent category ID"
    )

    path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Full path (e.g., Femmes > Vêtements > Jeans)"
    )

    is_leaf: Mapped[bool] = mapped_column(
        Boolean,
        server_default="false",
        nullable=False,
        comment="True if category can be selected for products"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        server_default="true",
        nullable=False,
        comment="True if category is active"
    )

    gender: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Gender: women, men, girls, boys"
    )

    # Relationships
    parent: Mapped["VintedCategory | None"] = relationship(
        "VintedCategory",
        remote_side=[id],
        back_populates="children"
    )

    children: Mapped[list["VintedCategory"]] = relationship(
        "VintedCategory",
        back_populates="parent"
    )

    def __repr__(self) -> str:
        return f"<VintedCategory(id={self.id}, title={self.title}, gender={self.gender})>"
