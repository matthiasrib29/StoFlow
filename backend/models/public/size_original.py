"""
SizeOriginal Model

Table pour les tailles originales de produits (schema product_attributes).

Business Rules (Created: 2026-01-06):
- Tailles saisies librement par les utilisateurs
- Auto-création via get_or_create() dans SizeOriginalRepository
- PK sur `name` (String) - pas d'ID numérique
- Pas de traductions ni mappings marketplace (contrairement à sizes_normalized)
"""

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class SizeOriginal(Base):
    """
    Modèle pour les tailles originales de produits.

    Attributes:
    - name (PK): Taille en texte libre (ex: "W32/L34", "M", "42 EU")
    - created_at: Date de création
    """

    __tablename__ = "sizes_original"
    __table_args__ = {"schema": "product_attributes"}

    # ===== PRIMARY KEY =====
    name: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
        index=True,
        comment="Taille originale (texte libre, auto-créable)"
    )

    # ===== METADATA =====
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        comment="Date de création"
    )

    def __repr__(self) -> str:
        return f"<SizeOriginal(name='{self.name}')>"
