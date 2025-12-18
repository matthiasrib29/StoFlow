"""
Category Platform Mapping Model

Table de mapping des categories vers les IDs des differentes plateformes
(Vinted, Etsy, eBay).

Business Rules (2025-12-17):
- Cle composite: (category, gender, fit) -> IDs plateformes
- Une seule table pour toutes les plateformes (pas de duplication)
- Fallback: exact match -> sans fit -> premier trouve
- eBay: IDs differents par marketplace (FR, DE, GB, IT, ES)
"""

from sqlalchemy import BigInteger, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base


class CategoryPlatformMapping(Base):
    """
    Mapping des categories internes vers les IDs des marketplaces.

    La cle composite (category, gender, fit) permet de trouver
    les IDs correspondants sur chaque plateforme.

    Example:
        >>> mapping = CategoryPlatformMapping(
        ...     category="Jeans",
        ...     gender="Men",
        ...     fit="Slim",
        ...     vinted_category_id=89,
        ...     etsy_taxonomy_id=1429,
        ...     ebay_category_id_fr=11483
        ... )
    """

    __tablename__ = "category_platform_mappings"
    __table_args__ = (
        UniqueConstraint(
            "category", "gender", "fit",
            name="uq_category_platform_mapping"
        ),
        Index(
            "idx_category_platform_lookup",
            "category", "gender", "fit"
        ),
        {"schema": "public"}
    )

    # ===== PRIMARY KEY =====
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )

    # ===== COMPOSITE KEY (lookup) =====
    category: Mapped[str] = mapped_column(
        String(100),
        ForeignKey(
            "product_attributes.categories.name_en",
            onupdate="CASCADE",
            ondelete="CASCADE"
        ),
        nullable=False,
        comment="Category name (EN) - FK to categories"
    )
    gender: Mapped[str] = mapped_column(
        String(100),
        ForeignKey(
            "product_attributes.genders.name_en",
            onupdate="CASCADE",
            ondelete="CASCADE"
        ),
        nullable=False,
        comment="Gender name (EN) - FK to genders"
    )
    fit: Mapped[str | None] = mapped_column(
        String(100),
        ForeignKey(
            "product_attributes.fits.name_en",
            onupdate="CASCADE",
            ondelete="SET NULL"
        ),
        nullable=True,
        comment="Fit name (EN) - FK to fits (optional)"
    )

    # ===== VINTED =====
    vinted_category_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Vinted catalog_id"
    )
    vinted_category_name: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Vinted category name (for display)"
    )
    vinted_category_path: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="Vinted category path (e.g. Hommes > Jeans > Slim)"
    )

    # ===== ETSY =====
    etsy_taxonomy_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="Etsy taxonomy_id"
    )
    etsy_category_name: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Etsy category name"
    )
    etsy_category_path: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="Etsy category path"
    )
    etsy_required_attributes: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="JSON: Required attributes for Etsy listings"
    )

    # ===== EBAY (per marketplace) =====
    ebay_category_id_fr: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="eBay category ID for EBAY_FR"
    )
    ebay_category_id_de: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="eBay category ID for EBAY_DE"
    )
    ebay_category_id_gb: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="eBay category ID for EBAY_GB"
    )
    ebay_category_id_it: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="eBay category ID for EBAY_IT"
    )
    ebay_category_id_es: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="eBay category ID for EBAY_ES"
    )
    ebay_category_name: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="eBay category name (EN)"
    )
    ebay_item_specifics: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="JSON: Required item specifics for eBay"
    )

    # ===== RELATIONSHIPS =====
    category_ref: Mapped["Category"] = relationship(
        "Category",
        foreign_keys=[category],
        lazy="joined"
    )
    gender_ref: Mapped["Gender"] = relationship(
        "Gender",
        foreign_keys=[gender],
        lazy="joined"
    )
    fit_ref: Mapped["Fit | None"] = relationship(
        "Fit",
        foreign_keys=[fit],
        lazy="joined"
    )

    def __repr__(self) -> str:
        return (
            f"<CategoryPlatformMapping("
            f"category='{self.category}', "
            f"gender='{self.gender}', "
            f"fit='{self.fit}', "
            f"vinted={self.vinted_category_id}, "
            f"etsy={self.etsy_taxonomy_id}, "
            f"ebay_fr={self.ebay_category_id_fr}"
            f")>"
        )


# Import for relationship type hints (avoid circular imports)
from models.public.category import Category
from models.public.fit import Fit
from models.public.gender import Gender as Gender
