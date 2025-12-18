"""
Sport Model

Table pour les sports de produits (schema product_attributes, partagée entre tenants).

Business Rules (Created: 2025-12-11):
- Sports partagés entre tous les tenants
- Champs bilingues (EN/FR)
- Utilisé pour catégoriser les vêtements de sport
"""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class Sport(Base):
    """
    Modèle pour les sports de produits.

    Attributes:
    - name_en: Nom du sport en anglais (PK)
    - name_fr: Nom du sport en français
    - description: Description optionnelle du sport
    """

    __tablename__ = "sports"
    __table_args__ = {"schema": "product_attributes"}

    # ===== PRIMARY KEY =====
    name_en: Mapped[str] = mapped_column(
        String(100), primary_key=True, index=True, comment="Nom du sport (EN)"
    )

    # ===== MULTILINGUAL TRANSLATIONS =====
    name_fr: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom du sport (FR)"
    )

    # ===== DESCRIPTIVE FIELDS =====
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Description du sport"
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
        return f"<Sport(name_en='{self.name_en}', name_fr='{self.name_fr}')>"
