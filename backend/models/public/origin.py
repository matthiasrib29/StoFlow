"""
Origin Model

Table pour les origines/provenances (schema product_attributes, multilingue).

Business Rules (Updated: 2026-01-22):
- 7 langues supportées: EN, FR, DE, IT, ES, NL, PL
- Ex: Made in France, Made in Italy, Made in China, Made in Portugal
- Pricing coefficient: bonus for premium origins (Italy, France, Japan, USA, UK, Germany)
- is_premium: marks high-value manufacturing countries
"""

from decimal import Decimal

from sqlalchemy import Boolean, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class Origin(Base):
    """
    Modèle pour les origines/provenances de fabrication (multilingue).

    Extended Attributes (2026-01-22):
    - 7 traductions (EN, FR, DE, IT, ES, NL, PL)
    - pricing_coefficient: bonus for premium origins (+0.15)
    - is_premium: marks premium manufacturing countries
    """

    __tablename__ = "origins"
    __table_args__ = {"schema": "product_attributes"}

    # ===== PRIMARY KEY =====
    name_en: Mapped[str] = mapped_column(
        String(100), primary_key=True, index=True, comment="Nom de l'origine (EN)"
    )

    # ===== MULTILINGUAL TRANSLATIONS =====
    name_fr: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de l'origine (FR)"
    )
    name_de: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de l'origine (DE)"
    )
    name_it: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de l'origine (IT)"
    )
    name_es: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de l'origine (ES)"
    )
    name_nl: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de l'origine (NL)"
    )
    name_pl: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de l'origine (PL)"
    )

    # ===== PRICING =====
    pricing_coefficient: Mapped[Decimal] = mapped_column(
        Numeric(3, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
        comment="Pricing coefficient for origin bonus (-0.10 to +0.20)"
    )
    is_premium: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="Premium origin flag (Italy, France, Japan, USA, UK, Germany)"
    )

    def __repr__(self) -> str:
        return f"<Origin(name_en='{self.name_en}', is_premium={self.is_premium}, coefficient={self.pricing_coefficient})>"
