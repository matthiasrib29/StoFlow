"""
Fit Model

Table pour les coupes de produits (schema product_attributes, multilingue).

Business Rules (Updated: 2025-12-22):
- 7 langues supportées: EN, FR, DE, IT, ES, NL, PL
"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class Fit(Base):
    """
    Modèle pour les coupes de produits (multilingue).

    Attributes:
    - 7 traductions (EN, FR, DE, IT, ES, NL, PL)
    """

    __tablename__ = "fits"
    __table_args__ = {"schema": "product_attributes"}

    # ===== PRIMARY KEY =====
    name_en: Mapped[str] = mapped_column(
        String(100), primary_key=True, index=True, comment="Nom de la coupe (EN)"
    )

    # ===== MULTILINGUAL TRANSLATIONS =====
    name_fr: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la coupe (FR)"
    )
    name_de: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la coupe (DE)"
    )
    name_it: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la coupe (IT)"
    )
    name_es: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la coupe (ES)"
    )
    name_nl: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la coupe (NL)"
    )
    name_pl: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la coupe (PL)"
    )

    @property
    def name(self) -> str:
        """Alias pour compatibilité: name_en → name"""
        return self.name_en

    def __repr__(self) -> str:
        return f"<Fit(name_en='{self.name_en}')>"
