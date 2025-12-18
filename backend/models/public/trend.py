"""
Trend Model

Table pour les tendances/styles (schema public, multilingue).

Business Rules (Updated: 2025-12-08):
- 7 langues supportées: EN, FR, DE, IT, ES, NL, PL
- Ex: Vintage, Boho, Streetwear, Minimalist, Y2K
- Compatibilité pythonApiWOO
"""

import os
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class Trend(Base):
    """
    Modèle pour les tendances/styles de mode (multilingue).

    Extended Attributes (2025-12-08):
    - 7 traductions (EN, FR, DE, IT, ES, NL, PL)
    - Utilisé pour caractériser la tendance/style du vêtement
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

    def __repr__(self) -> str:
        return f"<Trend(name_en='{self.name_en}', name_fr='{self.name_fr}')>"
