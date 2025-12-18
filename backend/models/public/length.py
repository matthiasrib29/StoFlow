"""
Length Model

Table pour les longueurs de vêtements (schema product_attributes, partagée entre tenants).

Business Rules (Created: 2025-12-11):
- Longueurs partagées entre tous les tenants
- Champs bilingues (EN/FR)
- Utilisé pour décrire la longueur des vêtements (robes, pantalons, manches, etc.)
"""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class Length(Base):
    """
    Modèle pour les longueurs de vêtements.

    Attributes:
    - name_en: Nom de la longueur en anglais (PK)
    - name_fr: Nom de la longueur en français
    - description: Description optionnelle de la longueur
    """

    __tablename__ = "lengths"
    __table_args__ = {"schema": "product_attributes"}

    # ===== PRIMARY KEY =====
    name_en: Mapped[str] = mapped_column(
        String(100), primary_key=True, index=True, comment="Nom de la longueur (EN)"
    )

    # ===== MULTILINGUAL TRANSLATIONS =====
    name_fr: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la longueur (FR)"
    )

    # ===== DESCRIPTIVE FIELDS =====
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Description de la longueur"
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
        return f"<Length(name_en='{self.name_en}', name_fr='{self.name_fr}')>"
