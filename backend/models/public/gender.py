"""
Gender Model

Table pour les genres de produits (schema public, multilingue).

Business Rules (Updated: 2025-12-08):
- 7 langues supportées: EN, FR, DE, IT, ES, NL, PL
- Ex: Men, Women, Boys, Girls
- Compatibilité pythonApiWOO
"""

import os
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class Gender(Base):
    """
    Modèle pour les genres de produits (multilingue).

    Extended Attributes (2025-12-08):
    - 7 traductions (EN, FR, DE, IT, ES, NL, PL)
    - Utilisé pour caractériser le genre cible du vêtement
    """

    __tablename__ = "genders"
    __table_args__ = {"schema": "product_attributes"}

    # ===== PRIMARY KEY =====
    name_en: Mapped[str] = mapped_column(
        String(100), primary_key=True, index=True, comment="Nom du genre (EN)"
    )

    # ===== MULTILINGUAL TRANSLATIONS =====
    name_fr: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom du genre (FR)"
    )
    name_de: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom du genre (DE)"
    )
    name_it: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom du genre (IT)"
    )
    name_es: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom du genre (ES)"
    )
    name_nl: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom du genre (NL)"
    )
    name_pl: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom du genre (PL)"
    )

    def __repr__(self) -> str:
        return f"<Gender(name_en='{self.name_en}', name_fr='{self.name_fr}')>"
