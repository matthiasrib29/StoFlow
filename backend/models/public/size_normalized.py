"""
SizeNormalized Model

Table pour les tailles normalisées de produits (schema product_attributes).

Business Rules (Updated: 2026-01-28):
- Pas de traduction nécessaire (codes internationaux: XS, S, M, L, XL, 28, 30, etc.)
- Mappings marketplace: vinted_women_id, vinted_men_id, ebay_size, etsy_size
- Vinted a des IDs différents pour femmes vs hommes
- Table read-only (aucune auto-création)
- category_group: Classification des tailles (letter, numeric_eu, waist, one_size)
- Equivalences: FR, US, IT pour conversion internationale
"""

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class SizeNormalized(Base):
    """
    Modèle pour les tailles normalisées de produits.

    Business Rules (Updated: 2026-01-28):
    - Pas de traduction: les codes de tailles sont internationaux
    - vinted_women_id, vinted_men_id: IDs Vinted par genre
    - ebay_size, etsy_size: IDs autres marketplaces
    - category_group: letter, numeric_eu, waist, one_size
    - equivalent_fr/us/it: Equivalences internationales
    """

    __tablename__ = "sizes_normalized"
    __table_args__ = {"schema": "product_attributes"}

    # ===== PRIMARY KEY =====
    name_en: Mapped[str] = mapped_column(
        String(100), primary_key=True, index=True, comment="Code de la taille"
    )

    # ===== CATEGORY GROUP (2026-01-28) =====
    category_group: Mapped[str | None] = mapped_column(
        String(20), nullable=True, index=True,
        comment="Size category: letter, numeric_eu, waist, one_size"
    )

    # ===== SIZE EQUIVALENCES (2026-01-28) =====
    equivalent_fr: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="French size equivalent (e.g., 38, 40)"
    )
    equivalent_us: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="US size equivalent (e.g., 6, 8, S, M)"
    )
    equivalent_it: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="Italian size equivalent (e.g., 42, 44)"
    )

    # ===== MARKETPLACE MAPPINGS =====
    vinted_women_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="ID Vinted pour femmes"
    )
    vinted_men_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="ID Vinted pour hommes"
    )
    ebay_size: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Taille eBay"
    )
    etsy_size: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Taille Etsy"
    )

    @property
    def name(self) -> str:
        """Alias pour compatibilité: name_en → name"""
        return self.name_en

    def __repr__(self) -> str:
        return f"<SizeNormalized(name_en='{self.name_en}')>"
