"""
Rise Model

Table pour les hauteurs de taille (schema public, multilingue).

Business Rules (Updated: 2025-12-08):
- 7 langues supportées: EN, FR, DE, IT, ES, NL, PL
- Ex: High rise, Mid rise, Low rise
- Compatibilité pythonApiWOO
"""

import os
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class Rise(Base):
    """
    Modèle pour les hauteurs de taille (pantalons, jupes) (multilingue).

    Extended Attributes (2025-12-08):
    - 7 traductions (EN, FR, DE, IT, ES, NL, PL)
    - Utilisé pour indiquer la hauteur de taille du vêtement
    """

    __tablename__ = "rises"
    __table_args__ = {"schema": "product_attributes"}

    # ===== PRIMARY KEY =====
    name_en: Mapped[str] = mapped_column(
        String(100), primary_key=True, index=True, comment="Nom de la hauteur de taille (EN)"
    )

    # ===== MULTILINGUAL TRANSLATIONS =====
    name_fr: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la hauteur de taille (FR)"
    )
    name_de: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la hauteur de taille (DE)"
    )
    name_it: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la hauteur de taille (IT)"
    )
    name_es: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la hauteur de taille (ES)"
    )
    name_nl: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la hauteur de taille (NL)"
    )
    name_pl: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la hauteur de taille (PL)"
    )

    def __repr__(self) -> str:
        return f"<Rise(name_en='{self.name_en}', name_fr='{self.name_fr}')>"
