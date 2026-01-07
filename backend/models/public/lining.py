"""
Lining Model

Table pour les types de doublure de produits (schema product_attributes, multilingue).

Business Rules (Updated: 2026-01-07):
- 7 langues supportées: EN, FR, DE, IT, ES, NL, PL
- Options: Unlined, Fully lined, Partially lined, Fleece lined
"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class Lining(Base):
    """
    Modèle pour les types de doublure des produits (multilingue).

    Attributes:
    - 7 traductions (EN, FR, DE, IT, ES, NL, PL)
    """

    __tablename__ = "linings"
    __table_args__ = {"schema": "product_attributes"}

    # ===== PRIMARY KEY =====
    name_en: Mapped[str] = mapped_column(
        String(100), primary_key=True, index=True, comment="Nom de la doublure (EN)"
    )

    # ===== MULTILINGUAL TRANSLATIONS =====
    name_fr: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la doublure (FR)"
    )
    name_de: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la doublure (DE)"
    )
    name_it: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la doublure (IT)"
    )
    name_es: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la doublure (ES)"
    )
    name_nl: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la doublure (NL)"
    )
    name_pl: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la doublure (PL)"
    )

    @property
    def name(self) -> str:
        """Alias pour compatibilité: name_en → name"""
        return self.name_en

    def __repr__(self) -> str:
        return f"<Lining(name_en='{self.name_en}')>"
