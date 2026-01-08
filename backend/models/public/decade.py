"""
Decade Model

Table pour les décennies (schema product_attributes).

Business Rules (Updated: 2026-01-08):
- Pas de traduction nécessaire (codes internationaux: 1950s, 1960s, 1970s, etc.)
- Les décennies sont des codes universels utilisés dans tous les pays
- Table read-only (aucune auto-création)
"""

import os
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class Decade(Base):
    """
    Modèle pour les décennies de style vestimentaire.

    Business Rules (Updated: 2026-01-08):
    - Pas de traduction: les codes de décennies sont internationaux
    - Utilisé pour caractériser l'époque/style du vêtement
    """

    __tablename__ = "decades"
    __table_args__ = {"schema": "product_attributes"}

    # ===== PRIMARY KEY =====
    name_en: Mapped[str] = mapped_column(
        String(100), primary_key=True, index=True, comment="Code de la décennie"
    )

    @property
    def name(self) -> str:
        """Alias pour compatibilité: name_en → name"""
        return self.name_en

    def __repr__(self) -> str:
        return f"<Decade(name_en='{self.name_en}')>"
