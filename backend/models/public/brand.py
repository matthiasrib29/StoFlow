"""
Brand Model

Table pour les marques de produits (schema product_attributes, partagée entre tenants).

Business Rules (Updated: 2026-01-08):
- Marques partagées entre tous les tenants
- Pas de traduction nécessaire (les noms de marques restent identiques)
- Champs pythonApiWOO compatibles:
  * vinted_id: ID marketplace Vinted
  * monitoring: Flag pour tracking spécial
  * sector_jeans/sector_jacket: Segments de marché (BUDGET, STANDARD, HYPE, PREMIUM, ULTRA PREMIUM)
"""

import os
from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class Brand(Base):
    """
    Modèle pour les marques de produits.

    Business Rules (Updated: 2026-01-08):
    - Pas de traduction: les noms de marques sont internationaux
    - vinted_id: ID pour intégration Vinted
    - monitoring: Marque suivie spécialement
    - sector_jeans: Segment marché jeans (BUDGET → ULTRA PREMIUM)
    - sector_jacket: Segment marché vestes (BUDGET → ULTRA PREMIUM)
    """

    __tablename__ = "brands"
    __table_args__ = {"schema": "product_attributes"}

    # ===== PRIMARY KEY =====
    name: Mapped[str] = mapped_column(
        String(100), primary_key=True, index=True, comment="Nom de la marque"
    )

    # ===== DESCRIPTIVE FIELDS =====
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Description de la marque"
    )

    # ===== COMPATIBILITY PROPERTIES =====
    @property
    def name_en(self) -> str:
        """Alias pour compatibilité avec autres modèles: name → name_en"""
        return self.name

    # ===== MARKETPLACE INTEGRATION =====
    vinted_id: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="ID Vinted pour intégration marketplace"
    )

    # ===== MONITORING =====
    monitoring: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="Marque surveillée (tracking spécial)"
    )

    # ===== PRICING SEGMENTS =====
    sector_jeans: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Segment de marché pour les jeans: BUDGET, STANDARD, HYPE, PREMIUM, ULTRA PREMIUM",
    )
    sector_jacket: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Segment de marché pour les vestes: BUDGET, STANDARD, HYPE, PREMIUM, ULTRA PREMIUM",
    )

    def __repr__(self) -> str:
        return f"<Brand(name='{self.name}', jeans={self.sector_jeans}, jacket={self.sector_jacket}, monitoring={self.monitoring})>"
