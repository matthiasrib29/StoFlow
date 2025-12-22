"""
Material Model

Table pour les matières de produits (schema product_attributes, multilingue).

Business Rules (Updated: 2025-12-22):
- 7 langues supportées: EN, FR, DE, IT, ES, NL, PL
- vinted_id pour mapping Vinted
"""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class Material(Base):
    """
    Modèle pour les matières de produits (multilingue).

    Attributes:
    - 7 traductions (EN, FR, DE, IT, ES, NL, PL)
    - vinted_id: ID Vinted pour mapping matières
    """

    __tablename__ = "materials"
    __table_args__ = {"schema": "product_attributes"}

    # ===== PRIMARY KEY =====
    name_en: Mapped[str] = mapped_column(
        String(100), primary_key=True, index=True, comment="Nom de la matière (EN)"
    )

    # ===== MULTILINGUAL TRANSLATIONS =====
    name_fr: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la matière (FR)"
    )
    name_de: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la matière (DE)"
    )
    name_it: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la matière (IT)"
    )
    name_es: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la matière (ES)"
    )
    name_nl: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la matière (NL)"
    )
    name_pl: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la matière (PL)"
    )

    # ===== MARKETPLACE MAPPINGS =====
    vinted_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, index=True, comment="ID Vinted pour mapping matières"
    )

    @property
    def name(self) -> str:
        """Alias pour compatibilité: name_en → name"""
        return self.name_en

    def __repr__(self) -> str:
        return f"<Material(name_en='{self.name_en}')>"
