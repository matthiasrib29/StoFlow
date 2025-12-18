"""
UniqueFeature Model

Table pour les caractéristiques uniques (schema public, multilingue).

Business Rules (Updated: 2025-12-08):
- 7 langues supportées: EN, FR, DE, IT, ES, NL, PL
- Ex: Limited edition, Signed, Handmade, Custom, Collectible
- Compatibilité pythonApiWOO
"""

import os
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class UniqueFeature(Base):
    """
    Modèle pour les caractéristiques uniques de produits (multilingue).

    Extended Attributes (2025-12-08):
    - 7 traductions (EN, FR, DE, IT, ES, NL, PL)
    - Utilisé pour caractériser les aspects spéciaux/uniques du vêtement
    """

    __tablename__ = "unique_features"
    __table_args__ = {"schema": "product_attributes"}

    # ===== PRIMARY KEY =====
    name_en: Mapped[str] = mapped_column(
        String(100), primary_key=True, index=True, comment="Nom de la caractéristique unique (EN)"
    )

    # ===== MULTILINGUAL TRANSLATIONS =====
    name_fr: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la caractéristique unique (FR)"
    )
    name_de: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la caractéristique unique (DE)"
    )
    name_it: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la caractéristique unique (IT)"
    )
    name_es: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la caractéristique unique (ES)"
    )
    name_nl: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la caractéristique unique (NL)"
    )
    name_pl: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la caractéristique unique (PL)"
    )

    def __repr__(self) -> str:
        return f"<UniqueFeature(name_en='{self.name_en}', name_fr='{self.name_fr}')>"
