"""
Size Model

Table pour les tailles de produits (schema product_attributes).

Business Rules (Updated: 2025-12-22):
- 7 langues supportées: EN, FR, DE, IT, ES, NL, PL
- Mappings marketplace simples: vinted_id, ebay_size, etsy_size
"""

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class Size(Base):
    """
    Modèle pour les tailles de produits (multilingue).

    Attributes:
    - 7 traductions (EN, FR, DE, IT, ES, NL, PL)
    - vinted_id, ebay_size, etsy_size: IDs marketplace
    """

    __tablename__ = "sizes"
    __table_args__ = {"schema": "product_attributes"}

    # ===== PRIMARY KEY =====
    name_en: Mapped[str] = mapped_column(
        String(100), primary_key=True, index=True, comment="Code de la taille (EN)"
    )

    # ===== MULTILINGUAL TRANSLATIONS =====
    name_fr: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la taille (FR)"
    )
    name_de: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la taille (DE)"
    )
    name_it: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la taille (IT)"
    )
    name_es: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la taille (ES)"
    )
    name_nl: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la taille (NL)"
    )
    name_pl: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nom de la taille (PL)"
    )

    # ===== MARKETPLACE MAPPINGS =====
    vinted_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="ID Vinted"
    )
    ebay_size: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Taille eBay"
    )
    etsy_size: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Taille Etsy"
    )

    @property
    def name(self) -> str:
        """Alias pour compatibilité: name_en → name"""
        return self.name_en

    def __repr__(self) -> str:
        return f"<Size(name_en='{self.name_en}')>"
