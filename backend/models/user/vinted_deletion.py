"""
VintedDeletion Model - Schema user_{id}

Ce modèle archive les produits supprimés de Vinted avec leurs statistiques.
Utilisé pour analytics et suivi des performances.

Adapté de pythonApiWOO/Models/vinted/VintedDeletionModel.py

Business Rules (2025-12-12):
- Créé lors de la suppression d'un VintedProduct
- Conserve les stats au moment de la suppression (vues, favoris, etc.)
- Calcule days_active automatiquement
- Permet d'analyser la performance des produits supprimés

Author: Claude
Date: 2025-12-12
Source: pythonApiWOO/Models/vinted/VintedDeletionModel.py
"""

from datetime import date as date_type
from decimal import Decimal

from sqlalchemy import BigInteger, Date, Integer, Numeric, Index
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class VintedDeletion(Base):
    """
    Modèle VintedDeletion - Archive des produits Vinted supprimés.

    Structure identique à pythonApiWOO pour compatibilité.

    Attributes:
        id: ID auto-incrémenté (PK)
        id_vinted: ID Vinted du produit supprimé
        id_site: ID du produit dans Stoflow (product_id)
        price: Prix au moment de la suppression
        date_published: Date de publication initiale
        date_deleted: Date de suppression
        view_count: Nombre de vues au moment de la suppression
        favourite_count: Nombre de favoris
        days_active: Nombre de jours en ligne
        conversations: Nombre de conversations
    """

    __tablename__ = "vinted_deletions"
    __table_args__ = (
        Index('idx_vinted_deletions_id_vinted', 'id_vinted'),
        Index('idx_vinted_deletions_id_site', 'id_site'),
        Index('idx_vinted_deletions_date_deleted', 'date_deleted'),
        Index('idx_vinted_deletions_days_active', 'days_active'),
    )

    # Primary Key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    # IDs externes
    id_vinted: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        index=True,
        comment="ID Vinted du produit supprimé"
    )
    id_site: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        index=True,
        comment="ID du produit dans Stoflow (product_id)"
    )

    # Prix
    price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Prix au moment de la suppression"
    )

    # Dates
    date_published: Mapped[date_type | None] = mapped_column(
        Date,
        nullable=True,
        comment="Date de publication initiale"
    )
    date_deleted: Mapped[date_type | None] = mapped_column(
        Date,
        nullable=True,
        index=True,
        comment="Date de suppression"
    )

    # Statistiques au moment de la suppression
    view_count: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        default=0,
        comment="Nombre de vues"
    )
    favourite_count: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        default=0,
        comment="Nombre de favoris"
    )
    conversations: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        default=0,
        comment="Nombre de conversations"
    )

    # Durée de vie
    days_active: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
        comment="Nombre de jours en ligne"
    )

    def __repr__(self) -> str:
        return (
            f"<VintedDeletion(id={self.id}, id_vinted={self.id_vinted}, "
            f"days_active={self.days_active})>"
        )

    @classmethod
    def from_vinted_product(cls, vinted_product: "VintedProduct") -> "VintedDeletion":
        """
        Crée une VintedDeletion depuis un VintedProduct.

        Args:
            vinted_product: Instance VintedProduct à archiver

        Returns:
            VintedDeletion: Instance prête à être persistée
        """
        from datetime import date

        # Calcul de days_active
        days_active = None
        if vinted_product.date:
            delta = date.today() - vinted_product.date
            days_active = delta.days

        return cls(
            id_vinted=vinted_product.vinted_id,
            id_site=vinted_product.product_id,
            price=vinted_product.price,
            date_published=vinted_product.date,
            date_deleted=date.today(),
            view_count=vinted_product.view_count or 0,
            favourite_count=vinted_product.favourite_count or 0,
            conversations=vinted_product.conversations or 0,
            days_active=days_active
        )
