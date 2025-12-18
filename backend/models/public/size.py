"""
Size Model

Table pour les tailles de produits (schema product_attributes).

Business Rules (Updated: 2025-12-08):
- Mappings Vinted: Woman, Man Top, Man Bottom (ID + title)
- Mappings Etsy: etsy_296, etsy_454
- Mappings eBay UK: size, waist_size, inside_leg
- Compatibilité pythonApiWOO avec 114 tailles
"""

import os
from sqlalchemy import BigInteger, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class Size(Base):
    """
    Modèle pour les tailles de produits avec mappings marketplace.

    Extended Attributes (2025-12-08):
    - Vinted mappings: Différents par genre et catégorie
    - Etsy mappings: etsy_296 (tops), etsy_454 (bottoms)
    - eBay UK mappings: size standard, waist, inside leg
    """

    __tablename__ = "sizes"
    __table_args__ = {"schema": "product_attributes"}

    # ===== PRIMARY KEY =====
    name: Mapped[str] = mapped_column(
        String(100), primary_key=True, index=True, comment="Code de la taille (EN)"
    )

    # ===== MULTILINGUAL TRANSLATIONS (Added 2025-12-08) =====
    name_fr: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la taille (FR)"
    )

    # ===== COMPATIBILITY PROPERTIES =====
    @property
    def name_en(self) -> str:
        """Alias pour compatibilité avec autres modèles: name → name_en"""
        return self.name

    @property
    def french_name(self) -> str | None:
        """Alias pour compatibilité: name_fr → french_name"""
        return self.name_fr

    # ===== VINTED MAPPINGS =====
    vinted_woman_title: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="Titre Vinted Women"
    )
    vinted_woman_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="ID Vinted Women"
    )
    vinted_man_top_title: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="Titre Vinted Men Top"
    )
    vinted_man_top_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="ID Vinted Men Top"
    )
    vinted_man_bottom_title: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="Titre Vinted Men Bottom"
    )
    vinted_man_bottom_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="ID Vinted Men Bottom"
    )

    # ===== ETSY MAPPINGS =====
    etsy_296: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="ID Etsy 296 (category-specific)"
    )
    etsy_454: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="ID Etsy 454 (category-specific)"
    )

    # ===== EBAY UK MAPPINGS =====
    ebay_gb_size: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Taille standard eBay UK"
    )
    ebay_gb_waist_size: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Tour de taille eBay UK"
    )
    ebay_gb_inside_leg: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Entrejambe eBay UK"
    )

    def __repr__(self) -> str:
        return f"<Size(name='{self.name}')>"
