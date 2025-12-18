"""
Closure Model

Table pour les types de fermetures (schema public, multilingue).

Business Rules (Updated: 2025-12-08):
- 7 langues support�es: EN, FR, DE, IT, ES, NL, PL
- Ex: Zip, Button, Velcro, Lace-up, Buckle
- Compatibilit� pythonApiWOO
"""

import os
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class Closure(Base):
    """
    Mod�le pour les types de fermetures de v�tements (multilingue).

    Extended Attributes (2025-12-08):
    - 7 traductions (EN, FR, DE, IT, ES, NL, PL)
    - Utilis� pour d�crire le syst�me de fermeture du v�tement
    """

    __tablename__ = "closures"
    __table_args__ = {"schema": "product_attributes"}

    # ===== PRIMARY KEY =====
    name_en: Mapped[str] = mapped_column(
        String(100), primary_key=True, index=True, comment="Nom de la fermeture (EN)"
    )

    # ===== MULTILINGUAL TRANSLATIONS =====
    name_fr: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la fermeture (FR)"
    )
    name_de: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la fermeture (DE)"
    )
    name_it: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la fermeture (IT)"
    )
    name_es: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la fermeture (ES)"
    )
    name_nl: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la fermeture (NL)"
    )
    name_pl: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la fermeture (PL)"
    )

    def __repr__(self) -> str:
        return f"<Closure(name_en='{self.name_en}', name_fr='{self.name_fr}')>"
