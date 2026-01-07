"""
Stretch Model

Table pour les niveaux d'élasticité (schema product_attributes, multilingue).

Business Rules (Updated: 2026-01-07):
- 7 langues supportées: EN, FR, DE, IT, ES, NL, PL
- 4 niveaux standards: No Stretch, Slight Stretch, Moderate Stretch, Super Stretch
"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class Stretch(Base):
    """
    Modèle pour les niveaux d'élasticité des produits (multilingue).

    Attributes:
    - 7 traductions (EN, FR, DE, IT, ES, NL, PL)
    - Single-value attribute: un seul stretch par produit
    """

    __tablename__ = "stretches"
    __table_args__ = {"schema": "product_attributes"}

    # ===== PRIMARY KEY =====
    name_en: Mapped[str] = mapped_column(
        String(100), primary_key=True, index=True, comment="Nom du stretch (EN)"
    )

    # ===== MULTILINGUAL TRANSLATIONS =====
    name_fr: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom du stretch (FR)"
    )
    name_de: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom du stretch (DE)"
    )
    name_it: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom du stretch (IT)"
    )
    name_es: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom du stretch (ES)"
    )
    name_nl: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom du stretch (NL)"
    )
    name_pl: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom du stretch (PL)"
    )

    @property
    def name(self) -> str:
        """Alias pour compatibilité: name_en → name"""
        return self.name_en

    def __repr__(self) -> str:
        return f"<Stretch(name_en='{self.name_en}')>"
