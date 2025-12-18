"""
VintedOrder Model - Schema user_{id}

Ce modèle stocke les commandes/ventes Vinted synchronisées.

Business Rules (2025-12-12):
- Une commande = une transaction Vinted
- transaction_id = clé primaire (ID Vinted)
- Stocke les informations acheteur/vendeur et expédition
- Table liée: vinted_order_products pour les articles

Author: Claude
Date: 2025-12-12
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Numeric, String, Text, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base


class VintedOrder(Base):
    """
    Modèle VintedOrder - Commandes/ventes Vinted.

    Attributes:
        transaction_id: ID transaction Vinted (PK)
        buyer_id: ID acheteur Vinted
        buyer_login: Login acheteur
        seller_id: ID vendeur Vinted
        seller_login: Login vendeur
        status: Statut de la commande
        total_price: Prix total
        currency: Devise (EUR par défaut)
        shipping_price: Frais de port
        service_fee: Frais de service Vinted
        buyer_protection_fee: Frais protection acheteur
        seller_revenue: Revenu net vendeur
        tracking_number: Numéro de suivi
        carrier: Transporteur
        created_at_vinted: Date création sur Vinted
        shipped_at: Date expédition
        delivered_at: Date livraison
        completed_at: Date finalisation
    """

    __tablename__ = "vinted_orders"
    __table_args__ = (
        Index('idx_vinted_orders_buyer_id', 'buyer_id'),
        Index('idx_vinted_orders_status', 'status'),
        Index('idx_vinted_orders_created_at_vinted', 'created_at_vinted'),
    )

    # Primary Key = transaction_id Vinted
    transaction_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        comment="ID transaction Vinted (PK)"
    )

    # Participants
    buyer_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="ID acheteur Vinted"
    )
    buyer_login: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Login acheteur"
    )
    seller_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="ID vendeur Vinted"
    )
    seller_login: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Login vendeur"
    )

    # Statut
    status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Statut commande"
    )

    # Montants
    total_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Prix total"
    )
    currency: Mapped[str | None] = mapped_column(
        String(3),
        nullable=True,
        server_default='EUR',
        comment="Devise"
    )
    shipping_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Frais de port"
    )
    service_fee: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Frais de service"
    )
    buyer_protection_fee: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Protection acheteur"
    )
    seller_revenue: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Revenu vendeur net"
    )

    # Expédition
    tracking_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Numéro de suivi"
    )
    carrier: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Transporteur"
    )

    # Dates Vinted
    created_at_vinted: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Date création Vinted"
    )
    shipped_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Date expédition"
    )
    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Date livraison"
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Date finalisation"
    )

    # Timestamps système
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Date création locale"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Date MAJ locale"
    )

    # Relationships
    products: Mapped[list["VintedOrderProduct"]] = relationship(
        "VintedOrderProduct",
        back_populates="order",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<VintedOrder(transaction_id={self.transaction_id}, "
            f"buyer_login={self.buyer_login}, status={self.status}, "
            f"total_price={self.total_price})>"
        )


class VintedOrderProduct(Base):
    """
    Modèle VintedOrderProduct - Articles d'une commande Vinted.

    Structure alignée avec la migration 20251212_1240.

    Attributes:
        id: ID auto-incrémenté (PK)
        transaction_id: FK vers vinted_orders.transaction_id
        vinted_item_id: ID article sur Vinted
        product_id: ID produit Stoflow (si lié)
        title: Titre du produit
        price: Prix unitaire
        size: Taille
        brand: Marque
        photo_url: URL photo principale
    """

    __tablename__ = "vinted_order_products"
    __table_args__ = (
        Index('idx_vinted_order_products_transaction_id', 'transaction_id'),
        Index('idx_vinted_order_products_vinted_item_id', 'vinted_item_id'),
        Index('idx_vinted_order_products_product_id', 'product_id'),
    )

    # Primary Key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    # Foreign Key vers VintedOrder
    transaction_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("vinted_orders.transaction_id", ondelete="CASCADE"),
        nullable=False,
        comment="FK vers vinted_orders"
    )

    # IDs
    vinted_item_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="ID article Vinted"
    )
    product_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="ID produit Stoflow"
    )

    # Détails produit
    title: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Titre produit"
    )
    price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Prix unitaire"
    )
    size: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Taille"
    )
    brand: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Marque"
    )
    photo_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="URL photo principale"
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationship
    order: Mapped["VintedOrder"] = relationship(
        "VintedOrder",
        back_populates="products"
    )

    def __repr__(self) -> str:
        return (
            f"<VintedOrderProduct(id={self.id}, transaction_id={self.transaction_id}, "
            f"vinted_item_id={self.vinted_item_id}, title={self.title})>"
        )
