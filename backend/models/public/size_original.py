"""
SizeOriginal Model

Table pour les tailles originales de produits (schema product_attributes).

Business Rules (Updated: 2026-01-28):
- Tailles saisies librement par les utilisateurs
- Auto-création via get_or_create() dans SizeOriginalRepository
- PK sur `name` (String) - pas d'ID numérique
- size_normalized_id: FK optionnelle pour résolution automatique
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base


class SizeOriginal(Base):
    """
    Modèle pour les tailles originales de produits.

    Attributes:
    - name (PK): Taille en texte libre (ex: "W32/L34", "M", "42 EU")
    - size_normalized_id: FK vers sizes_normalized (résolution automatique)
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

    # ===== FK TO NORMALIZED SIZE (2026-01-28) =====
    size_normalized_id: Mapped[str | None] = mapped_column(
        String(100),
        ForeignKey(
            "product_attributes.sizes_normalized.name_en",
            onupdate="CASCADE",
            ondelete="SET NULL"
        ),
        nullable=True,
        index=True,
        comment="Link to normalized size for auto-resolution"
    )

    # ===== METADATA =====
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        comment="Date de création"
    )

    # ===== RELATIONSHIPS =====
    size_normalized: Mapped["SizeNormalized | None"] = relationship(
        "SizeNormalized",
        foreign_keys=[size_normalized_id],
        lazy="joined"
    )

    def __repr__(self) -> str:
        return f"<SizeOriginal(name='{self.name}')>"
