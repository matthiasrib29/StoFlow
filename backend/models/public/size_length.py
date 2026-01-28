"""
SizeLength Model

Table pour les longueurs de jambe (leg lengths) pour les pantalons (schema product_attributes).

Business Rules (Created: 2026-01-28):
- Séparation taille/longueur pour les bottoms (jeans, pants, etc.)
- Permet "W32/L34" → size_normalized = "W32", size_length = "34"
- Valeurs standards: 26, 28, 30, 32, 34, 36, 38 (en pouces)
- Table read-only (aucune auto-création)
"""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class SizeLength(Base):
    """
    Modèle pour les longueurs de jambe (leg lengths).

    Business Rules (Created: 2026-01-28):
    - Utilisé pour les bottoms (jeans, pants, shorts, etc.)
    - Stocke la partie "L" de "W32/L34"
    - equivalent_inches: longueur en pouces pour équivalences

    Standard Values:
    - 26, 28, 30, 32, 34, 36, 38 (most common)
    """

    __tablename__ = "size_lengths"
    __table_args__ = {"schema": "product_attributes"}

    # ===== PRIMARY KEY =====
    name_en: Mapped[str] = mapped_column(
        String(20), primary_key=True, index=True, comment="Leg length value (e.g., '32', '34')"
    )

    # ===== ATTRIBUTES =====
    equivalent_inches: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Length in inches for size conversion"
    )

    @property
    def name(self) -> str:
        """Alias pour compatibilité: name_en → name"""
        return self.name_en

    def __repr__(self) -> str:
        return f"<SizeLength(name_en='{self.name_en}', inches={self.equivalent_inches})>"
