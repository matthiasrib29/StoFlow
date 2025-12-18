"""
Condition Model

Table pour les conditions/états de produits (schema product_attributes).

Business Rules (Updated: 2025-12-08):
- Coefficient de pricing: ajustement prix selon l'état (0.8 à 1.0)
- IDs marketplace: Vinted, eBay
- 7 langues supportées: EN, FR, DE, IT, ES, NL, PL
- Compatibilité pythonApiWOO
"""

import os
from sqlalchemy import BigInteger, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class Condition(Base):
    """
    Modèle pour les conditions/états de produits.

    Extended Attributes (2025-12-08):
    - coefficient: Multiplicateur de prix (ex: 0.85 pour GOOD, 1.0 pour NEW)
    - vinted_id, ebay_condition: IDs marketplace
    - 7 descriptions multilingues pour affichage
    """

    __tablename__ = "conditions"
    __table_args__ = {"schema": "product_attributes"}

    # ===== PRIMARY KEY =====
    name: Mapped[str] = mapped_column(
        String(100), primary_key=True, index=True, comment="Code de la condition"
    )

    # ===== MARKETPLACE INTEGRATION =====
    vinted_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="ID Vinted"
    )
    ebay_condition: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Code eBay condition (ex: PRE_OWNED_EXCELLENT)"
    )

    # ===== PRICING COEFFICIENT =====
    coefficient: Mapped[float | None] = mapped_column(
        Numeric(5, 3), default=1.0, nullable=True, comment="Coefficient de pricing (0.8-1.0)"
    )

    # ===== MULTILINGUAL DESCRIPTIONS =====
    description_fr: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="Description en français"
    )
    description_en: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="Description en anglais"
    )
    description_de: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="Description en allemand"
    )
    description_it: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="Description en italien"
    )
    description_es: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="Description en espagnol"
    )
    description_nl: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="Description en néerlandais"
    )
    description_pl: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="Description en polonais"
    )

    def get_description(self, lang: str = "en") -> str:
        """
        Retourne la description traduite pour une langue donnée.

        Args:
            lang: Code langue ISO 639-1 (fr, en, de, it, es, nl, pl)

        Returns:
            str: Description traduite ou description_en par défaut

        Examples:
            >>> condition = Condition(name='a')
            >>> condition.get_description('fr')
            'Excellent'
            >>> condition.get_description('de')
            'Ausgezeichnet'
        """
        column_name = f"description_{lang}"
        value = getattr(self, column_name, None)
        # Fallback sur description_en si la langue demandée n'existe pas
        return value if value else getattr(self, "description_en", "Good")

    def __repr__(self) -> str:
        return f"<Condition(name='{self.name}', coefficient={self.coefficient})>"
