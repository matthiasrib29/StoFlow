"""
Decade Model

Table pour les décennies (schema product_attributes).

Business Rules (Updated: 2026-01-22):
- Pas de traduction nécessaire (codes internationaux: 1950s, 1960s, 1970s, etc.)
- Les décennies sont des codes universels utilisés dans tous les pays
- Table read-only (aucune auto-création)
- pricing_coefficient: Coefficient de prix pour bonus vintage (0.00 à 0.20)
"""

from decimal import Decimal
from sqlalchemy import DECIMAL, String
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class Decade(Base):
    """
    Modèle pour les décennies de style vestimentaire.

    Business Rules (Updated: 2026-01-22):
    - Pas de traduction: les codes de décennies sont internationaux
    - Utilisé pour caractériser l'époque/style du vêtement
    - pricing_coefficient: Bonus vintage pour le pricing (plus ancien = plus élevé)
    """

    __tablename__ = "decades"
    __table_args__ = {"schema": "product_attributes"}

    # ===== PRIMARY KEY =====
    name_en: Mapped[str] = mapped_column(
        String(100), primary_key=True, index=True, comment="Code de la décennie"
    )

    # ===== PRICING =====
    pricing_coefficient: Mapped[Decimal] = mapped_column(
        DECIMAL(3, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
        comment="Pricing coefficient for vintage bonus (0.00 to 0.20)"
    )

    @property
    def name(self) -> str:
        """Alias pour compatibilité: name_en → name"""
        return self.name_en

    def __repr__(self) -> str:
        return f"<Decade(name_en='{self.name_en}', pricing_coefficient={self.pricing_coefficient})>"
