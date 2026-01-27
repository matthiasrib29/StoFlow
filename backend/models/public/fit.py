"""
Fit Model

Table pour les coupes de produits (schema product_attributes, multilingue).

Business Rules (Updated: 2026-01-22):
- 7 langues supportées: EN, FR, DE, IT, ES, NL, PL
- pricing_coefficient: Coefficient pour l'ajustement de prix (-0.20 à +0.20)
"""

from decimal import Decimal

from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class Fit(Base):
    """
    Modèle pour les coupes de produits (multilingue).

    Attributes:
    - 7 traductions (EN, FR, DE, IT, ES, NL, PL)
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

    # ===== PRICING =====
    pricing_coefficient: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Coefficient pour l'ajustement de prix (-0.20 à +0.20)"
    )

    @property
    def name(self) -> str:
        """Alias pour compatibilité: name_en → name"""
        return self.name_en

    def __repr__(self) -> str:
        return f"<Fit(name_en='{self.name_en}')>"
