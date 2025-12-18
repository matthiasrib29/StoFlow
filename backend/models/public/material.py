"""
Material Model

Table pour les matières de produits (schema product_attributes, multilingue).

Business Rules (Updated: 2025-12-18):
- 7 langues supportées: EN, FR, DE, IT, ES, NL, PL
- IDs marketplace: Vinted, Etsy, eBay UK
- Compatibilité pythonApiWOO
"""

import os
from sqlalchemy import BigInteger, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class Material(Base):
    """
    Modèle pour les matières de produits (multilingue + marketplace IDs).

    Extended Attributes (2025-12-18):
    - 7 traductions (EN, FR, DE, IT, ES, NL, PL)
    - vinted_id: ID Vinted pour mapping matières
    - etsy_357: ID Etsy pour mapping matières
    - ebay_gb_material: Valeur eBay UK
    """

    __tablename__ = "materials"
    __table_args__ = {"schema": "product_attributes"}

    # ===== PRIMARY KEY =====
    name_en: Mapped[str] = mapped_column(
        String(100), primary_key=True, index=True, comment="Nom de la matière (EN)"
    )

    # ===== MULTILINGUAL TRANSLATIONS =====
    name_fr: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la matière (FR)"
    )
    name_de: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la matière (DE)"
    )
    name_it: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la matière (IT)"
    )
    name_es: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la matière (ES)"
    )
    name_nl: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la matière (NL)"
    )
    name_pl: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la matière (PL)"
    )

    # ===== MARKETPLACE INTEGRATION =====
    vinted_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, index=True, comment="ID Vinted pour mapping matières"
    )
    etsy_357: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="ID Etsy pour mapping matières"
    )
    ebay_gb_material: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Valeur matière eBay UK"
    )

    @property
    def french_name(self) -> str | None:
        """Alias pour compatibilité: name_fr → french_name"""
        return self.name_fr

    def __repr__(self) -> str:
        return f"<Material(name_en='{self.name_en}', name_fr='{self.name_fr}')>"
