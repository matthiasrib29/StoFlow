"""
ConditionSup Model

Table pour les conditions supplémentaires (schema public, multilingue).

Business Rules (2025-12-08):
- 7 langues supportées: EN, FR, DE, IT, ES, NL, PL
- États complémentaires pour détailler la condition
- Compatibilité pythonApiWOO
"""

import os
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class ConditionSup(Base):
    """
    Modèle pour les états supplémentaires de produits (multilingue).

    Extended Attributes (2025-12-08):
    - 7 traductions (EN, FR, DE, IT, ES, NL, PL)
    - Complète la table conditions pour détails supplémentaires
    """

    __tablename__ = "condition_sups"
    __table_args__ = {"schema": "product_attributes"}

    # ===== PRIMARY KEY =====
    name_en: Mapped[str] = mapped_column(
        String(100), primary_key=True, index=True, comment="Nom de l'état supplémentaire (EN)"
    )

    # ===== MULTILINGUAL TRANSLATIONS =====
    name_fr: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de l'état supplémentaire (FR)"
    )
    name_de: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de l'état supplémentaire (DE)"
    )
    name_it: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de l'état supplémentaire (IT)"
    )
    name_es: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de l'état supplémentaire (ES)"
    )
    name_nl: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de l'état supplémentaire (NL)"
    )
    name_pl: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de l'état supplémentaire (PL)"
    )

    def __repr__(self) -> str:
        return f"<ConditionSup(name_en='{self.name_en}', name_fr='{self.name_fr}')>"
