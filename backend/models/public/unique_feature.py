"""
UniqueFeature Model

Table pour les caractéristiques uniques (schema product_attributes, multilingue).

Business Rules (Updated: 2026-01-22):
- 7 langues supportées: EN, FR, DE, IT, ES, NL, PL
- Ex: Limited edition, Signed, Handmade, Custom, Collectible
- pricing_coefficient: Coefficient de prix pour bonus feature (0.00 à 0.20)
"""

from decimal import Decimal
from sqlalchemy import DECIMAL, String
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class UniqueFeature(Base):
    """
    Modèle pour les caractéristiques uniques de produits (multilingue).

    Extended Attributes (2026-01-22):
    - 7 traductions (EN, FR, DE, IT, ES, NL, PL)
    - Utilisé pour caractériser les aspects spéciaux/uniques du vêtement
    - pricing_coefficient: Bonus feature pour le pricing
    """

    __tablename__ = "unique_features"
    __table_args__ = {"schema": "product_attributes"}

    # ===== PRIMARY KEY =====
    name_en: Mapped[str] = mapped_column(
        String(100), primary_key=True, index=True, comment="Nom de la caractéristique unique (EN)"
    )

    # ===== MULTILINGUAL TRANSLATIONS =====
    name_fr: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la caractéristique unique (FR)"
    )
    name_de: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la caractéristique unique (DE)"
    )
    name_it: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la caractéristique unique (IT)"
    )
    name_es: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la caractéristique unique (ES)"
    )
    name_nl: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la caractéristique unique (NL)"
    )
    name_pl: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la caractéristique unique (PL)"
    )

    # ===== PRICING =====
    pricing_coefficient: Mapped[Decimal] = mapped_column(
        DECIMAL(3, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
        comment="Pricing coefficient for feature bonus (0.00 to 0.20)"
    )

    def __repr__(self) -> str:
        return f"<UniqueFeature(name_en='{self.name_en}', pricing_coefficient={self.pricing_coefficient})>"
