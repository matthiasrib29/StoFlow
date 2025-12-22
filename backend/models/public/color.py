"""
Color Model

Table pour les couleurs de produits (schema product_attributes, multilingue).

Business Rules (Updated: 2025-12-22):
- 7 langues supportées: EN, FR, DE, IT, ES, NL, PL
- hex_code pour représentation visuelle
"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class Color(Base):
    """
    Modèle pour les couleurs de produits (multilingue).

    Attributes:
    - 7 traductions (EN, FR, DE, IT, ES, NL, PL)
    - hex_code: Code couleur hexadécimal
    """

    __tablename__ = "colors"
    __table_args__ = {"schema": "product_attributes"}

    # ===== PRIMARY KEY =====
    name_en: Mapped[str] = mapped_column(
        String(100), primary_key=True, index=True, comment="Nom de la couleur (EN)"
    )

    # ===== MULTILINGUAL TRANSLATIONS =====
    name_fr: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la couleur (FR)"
    )
    name_de: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la couleur (DE)"
    )
    name_it: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la couleur (IT)"
    )
    name_es: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la couleur (ES)"
    )
    name_nl: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la couleur (NL)"
    )
    name_pl: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la couleur (PL)"
    )

    # ===== VISUAL =====
    hex_code: Mapped[str | None] = mapped_column(
        String(7), nullable=True, comment="Code couleur hexadécimal (#RRGGBB)"
    )

    @property
    def name(self) -> str:
        """Alias pour compatibilité: name_en → name"""
        return self.name_en

    def __repr__(self) -> str:
        return f"<Color(name_en='{self.name_en}', hex_code='{self.hex_code}')>"
