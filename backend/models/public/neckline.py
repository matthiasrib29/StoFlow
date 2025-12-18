"""
Neckline Model

Table pour les types d'encolures (schema product_attributes, partagée entre tenants).

Business Rules (Created: 2025-12-11):
- Encolures partagées entre tous les tenants
- Champs bilingues (EN/FR)
- Utilisé pour décrire le style d'encolure des vêtements
"""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class Neckline(Base):
    """
    Modèle pour les types d'encolures de vêtements.

    Attributes:
    - name_en: Nom de l'encolure en anglais (PK)
    - name_fr: Nom de l'encolure en français
    - description: Description optionnelle de l'encolure
    """

    __tablename__ = "necklines"
    __table_args__ = {"schema": "product_attributes"}

    # ===== PRIMARY KEY =====
    name_en: Mapped[str] = mapped_column(
        String(100), primary_key=True, index=True, comment="Nom de l'encolure (EN)"
    )

    # ===== MULTILINGUAL TRANSLATIONS =====
    name_fr: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de l'encolure (FR)"
    )

    # ===== DESCRIPTIVE FIELDS =====
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Description de l'encolure"
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
        return f"<Neckline(name_en='{self.name_en}', name_fr='{self.name_fr}')>"
