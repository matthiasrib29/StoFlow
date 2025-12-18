"""
Color Model

Table pour les couleurs de produits (schema product_attributes, multilingue).

Business Rules (Updated: 2025-12-08):
- 7 langues supportées: EN, FR, DE, IT, ES, NL, PL
- IDs marketplace: Etsy, Vinted, eBay UK
- Compatibilité pythonApiWOO
"""

import os
from sqlalchemy import BigInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class Color(Base):
    """
    Modèle pour les couleurs de produits (multilingue + marketplace IDs).

    Extended Attributes (2025-12-08):
    - 7 traductions (EN, FR, DE, IT, ES, NL, PL)
    - etsy_2: ID Etsy pour mapping couleurs
    - vinted_id: ID Vinted
    - ebay_gb_color: Valeur eBay UK
    """

    __tablename__ = "colors"
    __table_args__ = {"schema": "product_attributes"}

    # ===== PRIMARY KEY =====
    name_en: Mapped[str] = mapped_column(
        String(100), primary_key=True, index=True, comment="Nom de la couleur (EN)"
    )

    # ===== MULTILINGUAL TRANSLATIONS =====
    name_fr: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la couleur (FR)"
    )
    name_de: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la couleur (DE)"
    )
    name_it: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la couleur (IT)"
    )
    name_es: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la couleur (ES)"
    )
    name_nl: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la couleur (NL)"
    )
    name_pl: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la couleur (PL)"
    )

    # ===== MARKETPLACE INTEGRATION =====
    etsy_2: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="ID Etsy pour mapping couleurs"
    )
    vinted_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="ID Vinted"
    )
    ebay_gb_color: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Valeur couleur eBay UK"
    )

    @property
    def name(self) -> str:
        """Alias pour compatibilité: name_en → name"""
        return self.name_en

    @property
    def french_name(self) -> str | None:
        """Alias pour compatibilité: name_fr → french_name"""
        return self.name_fr

    def __repr__(self) -> str:
        return f"<Color(name_en='{self.name_en}', name_fr='{self.name_fr}')>"
