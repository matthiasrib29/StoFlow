"""
SizeNormalized Model

Table pour les tailles normalisées de produits (schema product_attributes).

Business Rules (Updated: 2026-01-06):
- 7 langues supportées: EN, FR, DE, IT, ES, NL, PL
- Mappings marketplace: vinted_women_id, vinted_men_id, ebay_size, etsy_size
- Vinted a des IDs différents pour femmes vs hommes
- Table read-only (aucune auto-création)
"""

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class SizeNormalized(Base):
    """
    Modèle pour les tailles normalisées de produits (multilingue).

    Attributes:
    - 7 traductions (EN, FR, DE, IT, ES, NL, PL)
    - vinted_women_id, vinted_men_id: IDs Vinted par genre
    - ebay_size, etsy_size: IDs autres marketplaces
    """

    __tablename__ = "sizes_normalized"
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
    vinted_women_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="ID Vinted pour femmes"
    )
    vinted_men_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="ID Vinted pour hommes"
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
        return f"<SizeNormalized(name_en='{self.name_en}')>"
