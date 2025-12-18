"""
Origin Model

Table pour les origines/provenances (schema public, multilingue).

Business Rules (Updated: 2025-12-08):
- 7 langues supportées: EN, FR, DE, IT, ES, NL, PL
- Ex: Made in France, Made in Italy, Made in China, Made in Portugal
- Compatibilité pythonApiWOO
"""

import os
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class Origin(Base):
    """
    Modèle pour les origines/provenances de fabrication (multilingue).

    Extended Attributes (2025-12-08):
    - 7 traductions (EN, FR, DE, IT, ES, NL, PL)
    - Utilisé pour indiquer le pays/origine de fabrication
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

    def __repr__(self) -> str:
        return f"<Origin(name_en='{self.name_en}', name_fr='{self.name_fr}')>"
