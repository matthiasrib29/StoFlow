"""
EbayProduct Model - Schema user_{id}

Ce modèle stocke les produits eBay (importés depuis l'inventaire eBay).
Relation 1:1 optionnelle avec Product via product_id.

Business Rules:
- ebay_sku = identifiant unique eBay (SKU de l'inventory item)
- product_id = FK optionnelle vers Product (relation 1:1)
- Toutes les données viennent de l'API eBay Inventory
- Supporte multi-marketplace (EBAY_FR, EBAY_GB, etc.)

Architecture:
- Stocké dans schema user_{id} pour isolation multi-tenant
- Données récupérées via OAuth2 (pas de plugin)
- Peut être lié à un Product Stoflow après import
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base

if TYPE_CHECKING:
    from models.user.product import Product


class EbayProduct(Base):
    """
    Modèle EbayProduct - Stockage des produits eBay (standalone).

    Attributes:
        id: Identifiant unique interne (PK)
        ebay_sku: SKU eBay de l'inventory item (unique, not null)

        # Infos produit
        title: Titre du listing
        description: Description complète
        price: Prix de vente
        currency: Devise (EUR, GBP, etc.)

        # Catégorisation
        brand: Nom de la marque
        size: Taille
        color: Couleur principale
        material: Matière
        category_id: ID catégorie eBay

        # État
        condition: État eBay (NEW, LIKE_NEW, GOOD, ACCEPTABLE)
        condition_description: Description de l'état

        # Disponibilité
        quantity: Quantité disponible
        availability_type: Type de disponibilité (IN_STOCK, OUT_OF_STOCK)

        # Marketplace
        marketplace_id: Marketplace eBay (EBAY_FR, EBAY_GB, etc.)

        # eBay IDs
        ebay_listing_id: ID du listing publié
        ebay_offer_id: ID de l'offer

        # Images
        image_urls: JSON des URLs d'images

        # Package details
        package_weight_value, package_weight_unit: Poids du colis
        package_length_value, package_length_unit: Longueur
        package_width_value, package_width_unit: Largeur
        package_height_value, package_height_unit: Hauteur

        # Offer details
        merchant_location_key: Emplacement d'inventaire
        secondary_category_id: Catégorie secondaire si double listing
        lot_size: Nombre d'items dans un lot
        quantity_limit_per_buyer: Limite d'achat par acheteur
        listing_description: Description du listing eBay
        sold_quantity: Nombre d'unités vendues
        available_quantity: Quantité disponible pour achat

        # Statut
        status: active, sold, inactive, ended

        # Dates
        created_at: Date import dans Stoflow
        updated_at: Dernière sync
    """

    __tablename__ = "ebay_products"
    __table_args__ = (
        Index("idx_ebay_products_status", "status"),
        Index("idx_ebay_products_ebay_sku", "ebay_sku"),
        Index("idx_ebay_products_marketplace_id", "marketplace_id"),
        Index("idx_ebay_products_brand", "brand"),
        Index("idx_ebay_products_ebay_listing_id", "ebay_listing_id"),
        {"schema": "tenant"},  # Placeholder for schema_translate_map
    )

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # eBay SKU (unique identifier from eBay Inventory)
    ebay_sku: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="SKU unique eBay (inventory item)",
    )

    # Link to Stoflow Product (1:1 relationship, optional)
    product_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("tenant.products.id", ondelete="SET NULL", onupdate="CASCADE"),
        unique=True,
        nullable=True,
        index=True,
        comment="FK vers Product Stoflow (relation 1:1)",
    )

    # Product Info
    title: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Titre du listing eBay"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Description complète"
    )
    price: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2), nullable=True, comment="Prix de vente"
    )
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="EUR", comment="Devise"
    )

    # Categorization
    brand: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Marque"
    )
    size: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Taille"
    )
    color: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Couleur principale"
    )
    material: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Matière"
    )
    category_id: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="ID catégorie eBay"
    )

    # Condition
    condition: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="État eBay (NEW, LIKE_NEW, GOOD, ACCEPTABLE)",
    )
    condition_description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Description détaillée de l'état"
    )

    # Availability
    quantity: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, comment="Quantité disponible"
    )
    availability_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        default="IN_STOCK",
        comment="Type de disponibilité",
    )

    # Marketplace
    marketplace_id: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="EBAY_FR",
        comment="Marketplace eBay (EBAY_FR, EBAY_GB, etc.)",
    )

    # eBay IDs
    ebay_listing_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True, index=True, comment="ID du listing publié"
    )
    ebay_offer_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True, comment="ID de l'offer"
    )

    # Images (JSON array of URLs)
    image_urls: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="JSON des URLs d'images"
    )

    # Aspects (eBay product aspects as JSON)
    aspects: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="JSON des aspects eBay (Brand, Color, Size, etc.)"
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        comment="Status: active, sold, inactive, ended",
    )

    # Listing details
    listing_format: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Format (FIXED_PRICE, AUCTION)"
    )
    listing_duration: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="Durée du listing (GTC, DAYS_30, etc.)"
    )

    # Package details
    package_weight_value: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2), nullable=True, comment="Poids du colis"
    )
    package_weight_unit: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True, comment="Unité de poids (KILOGRAM, POUND)"
    )
    package_length_value: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2), nullable=True, comment="Longueur du colis"
    )
    package_length_unit: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True, comment="Unité de longueur (INCH, CENTIMETER)"
    )
    package_width_value: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2), nullable=True, comment="Largeur du colis"
    )
    package_width_unit: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True, comment="Unité de largeur (INCH, CENTIMETER)"
    )
    package_height_value: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2), nullable=True, comment="Hauteur du colis"
    )
    package_height_unit: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True, comment="Unité de hauteur (INCH, CENTIMETER)"
    )

    # Offer details (from eBay Offer API)
    merchant_location_key: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Identifiant de l'emplacement d'inventaire"
    )
    secondary_category_id: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="ID catégorie secondaire si double listing"
    )
    lot_size: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Nombre d'items dans un lot"
    )
    quantity_limit_per_buyer: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Limite d'achat par acheteur"
    )
    listing_description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Description du listing (peut différer de product.description)"
    )
    sold_quantity: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Nombre d'unités vendues"
    )
    available_quantity: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Quantité disponible pour achat"
    )

    # Timestamps
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Date de publication sur eBay"
    )
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Dernière synchronisation"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ===== RELATIONSHIPS =====

    # Link to Stoflow Product (1:1)
    # lazy="raise" to prevent N+1 queries - use joinedload() or selectinload() when needed
    product: Mapped[Optional["Product"]] = relationship(
        "Product",
        back_populates="ebay_product",
        uselist=False,
        lazy="raise",
    )

    def __repr__(self) -> str:
        return (
            f"<EbayProduct(id={self.id}, ebay_sku='{self.ebay_sku}', "
            f"status='{self.status}', title='{self.title[:30] if self.title else None}')>"
        )

    @property
    def is_active(self) -> bool:
        """Check if product is active on eBay."""
        return self.status == "active" and self.quantity > 0

    @property
    def is_published(self) -> bool:
        """Check if product has a listing on eBay."""
        return self.ebay_listing_id is not None
