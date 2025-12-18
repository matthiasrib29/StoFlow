"""
Pattern Model

Table pour les motifs de vêtements (schema product_attributes, partagée entre tenants).

Business Rules (Created: 2025-12-11):
- Motifs partagés entre tous les tenants
- Champs bilingues (EN/FR)
- Utilisé pour décrire le motif/pattern des vêtements
"""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class Pattern(Base):
    """
    Modèle pour les motifs de vêtements.

    Attributes:
    - name_en: Nom du motif en anglais (PK)
    - name_fr: Nom du motif en français
    - description: Description optionnelle du motif
    """

    __tablename__ = "patterns"
    __table_args__ = {"schema": "product_attributes"}

    # ===== PRIMARY KEY =====
    name_en: Mapped[str] = mapped_column(
        String(100), primary_key=True, index=True, comment="Nom du motif (EN)"
    )

    # ===== MULTILINGUAL TRANSLATIONS =====
    name_fr: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom du motif (FR)"
    )

    # ===== DESCRIPTIVE FIELDS =====
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Description du motif"
    )

    # ===== COMPATIBILITY PROPERTIES =====
    @property
    def name(self) -> str:
        """Alias pour compatibilité: name_en → name"""
        return self.name_en

    @property
    def french_name(self) -> str | None:
        """Alias pour compatibilité: name_fr → french_name"""
        return self.name_fr

    def __repr__(self) -> str:
        return f"<Pattern(name_en='{self.name_en}', name_fr='{self.name_fr}')>"
