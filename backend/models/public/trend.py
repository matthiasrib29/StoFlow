"""
Trend Model

Table pour les tendances/styles (schema product_attributes, multilingue).

Business Rules (Updated: 2026-01-22):
- 7 langues supportées: EN, FR, DE, IT, ES, NL, PL
- Ex: Vintage, Boho, Streetwear, Minimalist, Y2K
- pricing_coefficient: Coefficient de prix pour bonus trend (0.00 à 0.20)
"""

from decimal import Decimal
from sqlalchemy import DECIMAL, String
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class Trend(Base):
    """
    Modèle pour les tendances/styles de mode (multilingue).

    Extended Attributes (2026-01-22):
    - 7 traductions (EN, FR, DE, IT, ES, NL, PL)
    - Utilisé pour caractériser la tendance/style du vêtement
    - pricing_coefficient: Bonus trend pour le pricing
    """

    __tablename__ = "trends"
    __table_args__ = {"schema": "product_attributes"}

    # ===== PRIMARY KEY =====
    name_en: Mapped[str] = mapped_column(
        String(100), primary_key=True, index=True, comment="Nom de la tendance (EN)"
    )

    # ===== MULTILINGUAL TRANSLATIONS =====
    name_fr: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la tendance (FR)"
    )
    name_de: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la tendance (DE)"
    )
    name_it: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la tendance (IT)"
    )
    name_es: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la tendance (ES)"
    )
    name_nl: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la tendance (NL)"
    )
    name_pl: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la tendance (PL)"
    )

    # ===== PRICING =====
    pricing_coefficient: Mapped[Decimal] = mapped_column(
        DECIMAL(3, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
        comment="Pricing coefficient for trend bonus (0.00 to 0.20)"
    )

    def __repr__(self) -> str:
        return f"<Trend(name_en='{self.name_en}', pricing_coefficient={self.pricing_coefficient})>"
