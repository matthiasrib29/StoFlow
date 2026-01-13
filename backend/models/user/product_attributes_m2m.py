"""
Many-to-Many Junction Tables for Product Attributes

These tables enable products to have multiple colors, materials, and condition_sups.

Architecture:
- ProductColor: Links products to colors (with is_primary flag)
- ProductMaterial: Links products to materials (with optional percentage)
- ProductConditionSup: Links products to condition supplements

All tables use composite primary keys (product_id, attribute_value).
All tables cascade on product deletion.
All tables have FK constraints to product_attributes schema.

Created: 2026-01-07
"""

from sqlalchemy import Boolean, ForeignKeyConstraint, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base


class ProductColor(Base):
    """
    Many-to-Many relationship between products and colors.

    Attributes:
        product_id: Foreign key to products table
        color: Foreign key to product_attributes.colors.name_en
        is_primary: Whether this is the primary/dominant color (only one per product)

    Business Rules:
        - One product can have multiple colors
        - Only ONE color can be marked as primary per product
        - First color added is automatically primary
        - ON DELETE CASCADE: Deleting product deletes color links
        - ON UPDATE CASCADE: Updating color name updates all links
    """

    __tablename__ = "product_colors"
    __table_args__ = (
        ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            ondelete="CASCADE",
            name="fk_product_colors_product_id"
        ),
        ForeignKeyConstraint(
            ["color"],
            ["product_attributes.colors.name_en"],
            onupdate="CASCADE",
            ondelete="CASCADE",
            name="fk_product_colors_color"
        ),
        # Unique constraint: only one primary color per product
        Index(
            "uq_product_colors_primary",
            "product_id",
            unique=True,
            postgresql_where=text("is_primary = TRUE")
        ),
        Index("idx_product_colors_product_id", "product_id"),
        Index("idx_product_colors_color", "color"),
        {"schema": "tenant"},  # Placeholder for schema_translate_map
    )

    product_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    color: Mapped[str] = mapped_column(String(100), primary_key=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    product: Mapped["Product"] = relationship(
        "Product",
        back_populates="product_colors",
        foreign_keys=[product_id]
    )


class ProductMaterial(Base):
    """
    Many-to-Many relationship between products and materials.

    Attributes:
        product_id: Foreign key to products table
        material: Foreign key to product_attributes.materials.name_en
        percentage: Optional percentage of this material in composition (0-100)

    Business Rules:
        - One product can have multiple materials
        - Percentage is optional (NULL allowed)
        - If percentages provided, ideally sum to 100 (warning if not, but not enforced)
        - ON DELETE CASCADE: Deleting product deletes material links
        - ON UPDATE CASCADE: Updating material name updates all links

    Examples:
        - Product A: [("Cotton", 80), ("Polyester", 20)]
        - Product B: [("Denim", None)] - percentage unknown
    """

    __tablename__ = "product_materials"
    __table_args__ = (
        ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            ondelete="CASCADE",
            name="fk_product_materials_product_id"
        ),
        ForeignKeyConstraint(
            ["material"],
            ["product_attributes.materials.name_en"],
            onupdate="CASCADE",
            ondelete="CASCADE",
            name="fk_product_materials_material"
        ),
        Index("idx_product_materials_product_id", "product_id"),
        Index("idx_product_materials_material", "material"),
        {"schema": "tenant"},  # Placeholder for schema_translate_map
    )

    product_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    material: Mapped[str] = mapped_column(String(100), primary_key=True)
    percentage: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Percentage of material in composition (0-100)"
    )

    # Relationships
    product: Mapped["Product"] = relationship(
        "Product",
        back_populates="product_materials",
        foreign_keys=[product_id]
    )


class ProductConditionSup(Base):
    """
    Many-to-Many relationship between products and condition supplements.

    Attributes:
        product_id: Foreign key to products table
        condition_sup: Foreign key to product_attributes.condition_sups.name_en

    Business Rules:
        - One product can have multiple condition supplements
        - No limit on number of condition_sups per product
        - ON DELETE CASCADE: Deleting product deletes condition_sup links
        - ON UPDATE CASCADE: Updating condition_sup name updates all links

    Examples:
        - Product A: ["Faded", "Small hole", "Vintage wear"]
        - Product B: ["Like new"] - single condition supplement
    """

    __tablename__ = "product_condition_sups"
    __table_args__ = (
        ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            ondelete="CASCADE",
            name="fk_product_condition_sups_product_id"
        ),
        ForeignKeyConstraint(
            ["condition_sup"],
            ["product_attributes.condition_sups.name_en"],
            onupdate="CASCADE",
            ondelete="CASCADE",
            name="fk_product_condition_sups_condition_sup"
        ),
        Index("idx_product_condition_sups_product_id", "product_id"),
        Index("idx_product_condition_sups_condition_sup", "condition_sup"),
        {"schema": "tenant"},  # Placeholder for schema_translate_map
    )

    product_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    condition_sup: Mapped[str] = mapped_column(String(100), primary_key=True)

    # Relationships
    product: Mapped["Product"] = relationship(
        "Product",
        back_populates="product_condition_sups",
        foreign_keys=[product_id]
    )
