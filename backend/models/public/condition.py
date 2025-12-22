"""
Condition Model

Table pour les conditions/états de produits (schema product_attributes).

Business Rules (Updated: 2025-12-18):
- note: Échelle numérique 0-10 (0=neuf, 10=très usé)
- Coefficient de pricing: ajustement prix selon l'état (0.8 à 1.0)
- IDs marketplace: Vinted, eBay
- 7 langues supportées: EN, FR, DE, IT, ES, NL, PL
"""

from sqlalchemy import BigInteger, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class Condition(Base):
    """
    Modèle pour les conditions/états de produits.

    La PK est 'note' (échelle numérique 0-10):
    - 0: Neuf avec étiquette
    - 1: Neuf sans étiquette
    - 2-3: Très bon état
    - 4-5: Bon état
    - 6-7: État satisfaisant
    - 8-10: Usé
    """

    __tablename__ = "conditions"
    __table_args__ = {"schema": "product_attributes"}

    # ===== PRIMARY KEY =====
    note: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, comment="Note 0-10 (0=neuf, 10=très usé)"
    )

    # ===== MULTILINGUAL NAMES =====
    name_en: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom en anglais"
    )
    name_fr: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom en français"
    )
    name_de: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom en allemand"
    )
    name_it: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom en italien"
    )
    name_es: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom en espagnol"
    )
    name_nl: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom en néerlandais"
    )
    name_pl: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom en polonais"
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

    def get_name(self, lang: str = "en") -> str:
        """
        Retourne le nom traduit pour une langue donnée.

        Args:
            lang: Code langue ISO 639-1 (fr, en, de, it, es, nl, pl)

        Returns:
            str: Nom traduit ou name_en par défaut
        """
        column_name = f"name_{lang}"
        value = getattr(self, column_name, None)
        return value if value else (self.name_en or f"Condition {self.note}")

    def __repr__(self) -> str:
        return f"<Condition(note={self.note}, name_en='{self.name_en}', coefficient={self.coefficient})>"
