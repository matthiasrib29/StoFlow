"""
Fit Model

Table pour les coupes de produits (schema public, multilingue).

Business Rules (Updated: 2025-12-08):
- Coefficient de pricing selon la coupe (ex: Slim = 1.1, Relaxed = 0.95)
- 7 langues supportées: EN, FR, DE, IT, ES, NL, PL
- IDs marketplace: eBay UK, Etsy
- Compatibilité pythonApiWOO
"""

import os
from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class Fit(Base):
    """
    Modèle pour les coupes de produits (multilingue + coefficient + marketplace IDs).

    Extended Attributes (2025-12-08):
    - coefficient: Multiplicateur de prix selon la coupe
    - 7 traductions (EN, FR, DE, IT, ES, NL, PL)
    - ebay_gb_fit: Valeur eBay UK
    - etsy_406, etsy_407: IDs Etsy pour mappings
    """

    __tablename__ = "fits"
    __table_args__ = {"schema": "product_attributes"}

    # ===== PRIMARY KEY =====
    name_en: Mapped[str] = mapped_column(
        String(100), primary_key=True, index=True, comment="Nom de la coupe (EN)"
    )

    # ===== MULTILINGUAL TRANSLATIONS =====
    name_fr: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la coupe (FR)"
    )
    name_de: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la coupe (DE)"
    )
    name_it: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la coupe (IT)"
    )
    name_es: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la coupe (ES)"
    )
    name_nl: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la coupe (NL)"
    )
    name_pl: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la coupe (PL)"
    )

    # ===== MARKETPLACE INTEGRATION =====
    ebay_gb_fit: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Valeur coupe eBay UK"
    )
    etsy_406: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="ID Etsy 406"
    )
    etsy_407: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="ID Etsy 407"
    )

    # ===== PRICING COEFFICIENT =====
    coefficient: Mapped[float | None] = mapped_column(
        Numeric(5, 3), default=1.0, nullable=True, comment="Coefficient de pricing (0.9-1.2)"
    )

    @property
    def french_name(self) -> str | None:
        """Alias pour compatibilité: name_fr → french_name"""
        return self.name_fr

    def __repr__(self) -> str:
        return f"<Fit(name_en='{self.name_en}', name_fr='{self.name_fr}', coefficient={self.coefficient})>"
