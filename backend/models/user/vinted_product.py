"""
VintedProduct Model - Schema user_{id}

Ce modèle stocke les produits Vinted (importés ou publiés).
Relation 1:1 optionnelle avec Product via product_id.

Business Rules (Updated: 2025-12-18):
- vinted_id = identifiant unique Vinted (PK logique)
- product_id = FK optionnelle vers Product (relation 1:1)
- Toutes les données viennent directement de l'API Vinted ou HTML parsing
- Stocke les IDs Vinted (brand_id, size_id, catalog_id) pour les opérations

Architecture:
- Stocké dans schema user_{id} pour isolation multi-tenant
- Plugin navigateur execute les requêtes API Vinted
- Backend stocke directement les données Vinted
- Peut être lié à un Product Stoflow après import ou publication
"""

from datetime import datetime, date as date_type

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List, Any, TYPE_CHECKING

from shared.database import Base

if TYPE_CHECKING:
    from models.user.product import Product


class VintedProduct(Base):
    """
    Modèle VintedProduct - Stockage des produits Vinted (standalone).

    Attributes:
        vinted_id: ID Vinted (PK - clé primaire)

        # Infos produit
        title: Titre du listing
        description: Description complète
        price: Prix de vente
        currency: Devise (EUR par défaut)
        total_price: Prix total avec frais

        # Catégorisation (avec IDs Vinted)
        brand: Nom de la marque
        brand_id: ID Vinted de la marque
        size: Taille (texte)
        size_id: ID Vinted de la taille
        color1, color1_id: Couleur principale avec ID
        color2, color2_id: Couleur secondaire avec ID
        catalog_id: ID Vinted de la catégorie

        # Dimensions
        measurement_width: Largeur en cm
        measurement_length: Longueur en cm
        measurement_unit: Unité de mesure

        # État et statut
        status: published, sold, deleted, draft
        condition: État du produit (texte)
        status_id: ID Vinted de l'état/condition
        manufacturer_labelling: Étiquetage du fabricant
        is_draft, is_closed, is_reserved, is_hidden, is_unisex

        # Vendeur
        seller_id: ID vendeur Vinted
        seller_login: Login vendeur

        # Frais
        service_fee: Frais de service

        # Analytics
        view_count: Nombre de vues
        favourite_count: Nombre de favoris

        # Images
        url: URL du listing
        photos_data: JSON des photos [{id, url, ...}]
        primary_photo_url: Property calculée depuis photos_data

        # Dates
        published_at: Date de publication sur Vinted (from image timestamp)
        created_at: Date import dans Stoflow
        updated_at: Dernière sync
    """

    __tablename__ = "vinted_products"
    __table_args__ = (
        Index('idx_vinted_products_status', 'status'),
        Index('idx_vinted_products_published_at', 'published_at'),
        Index('idx_vinted_products_brand', 'brand'),
        Index('idx_vinted_products_catalog_id', 'catalog_id'),
        Index('idx_vinted_products_seller_id', 'seller_id'),
        {"schema": "tenant"},  # Placeholder for schema_translate_map
    )

    # Primary Key (Vinted ID)
    vinted_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        comment="ID Vinted (PK)"
    )

    # Link to Stoflow Product (1:1 relationship, optional)
    product_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey('products.id', ondelete='SET NULL', onupdate='CASCADE'),
        unique=True,
        nullable=True,
        index=True,
        comment="FK vers Product Stoflow (relation 1:1)"
    )

    # Product Info
    title: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Titre du listing Vinted"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Description complète"
    )
    price: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Prix de vente"
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default='EUR',
        comment="Devise"
    )
    total_price: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Prix total avec frais"
    )

    # Categorization (with Vinted IDs)
    brand: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Nom de la marque"
    )
    brand_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="ID Vinted de la marque"
    )
    size: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Taille"
    )
    size_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="ID Vinted de la taille"
    )
    color1: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Couleur principale"
    )
    color1_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="ID Vinted de la couleur principale"
    )
    color2: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Couleur secondaire"
    )
    color2_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="ID Vinted de la couleur secondaire"
    )
    catalog_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="ID Vinted de la catégorie"
    )

    # Dimensions
    measurement_width: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Largeur en cm"
    )
    measurement_length: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Longueur en cm"
    )
    measurement_unit: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Unité de mesure (cm, inches)"
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default='published',
        comment="Status: draft, published, sold, deleted"
    )
    condition: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="État du produit"
    )
    status_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="ID Vinted du status/condition (from item_upload API)"
    )
    manufacturer_labelling: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Étiquetage du fabricant"
    )
    item_attributes: Mapped[Optional[List[Any]]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Attributs supplémentaires (JSON from item_upload API)"
    )
    is_draft: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Est un brouillon"
    )
    is_closed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Est fermé (vendu/supprimé)"
    )
    is_reserved: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Est réservé"
    )
    is_hidden: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Est masqué"
    )
    is_unisex: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Produit unisexe"
    )

    # Seller info
    seller_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        comment="ID vendeur Vinted"
    )
    seller_login: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Login vendeur"
    )

    # Fees
    service_fee: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Frais de service"
    )

    # Analytics
    view_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Nombre de vues"
    )
    favourite_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Nombre de favoris"
    )

    # URLs & Images
    url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="URL du listing Vinted"
    )
    photos_data: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="JSON des photos [{id, url, ...}]"
    )

    # Dates
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Date de publication sur Vinted (from image timestamp)"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # ===== RELATIONSHIPS =====

    # Link to Stoflow Product (1:1)
    product: Mapped[Optional["Product"]] = relationship(
        "Product",
        back_populates="vinted_product",
        uselist=False,
        lazy="joined"
    )

    def __repr__(self) -> str:
        return (
            f"<VintedProduct(vinted_id={self.vinted_id}, "
            f"status='{self.status}', title='{self.title[:30] if self.title else None}')>"
        )

    @property
    def is_published(self) -> bool:
        """Vérifie si le produit est publié"""
        return self.status == 'published' and not self.is_closed

    @property
    def is_sold(self) -> bool:
        """Vérifie si le produit a été vendu"""
        return self.status == 'sold'

    @property
    def primary_photo_url(self) -> Optional[str]:
        """
        Extract primary photo URL from photos_data JSON.

        Returns the first photo URL from photos_data, preferring full_size_url
        over url for better image quality.

        Returns:
            The primary photo URL, or None if no photos available.
        """
        if not self.photos_data:
            return None
        try:
            import json
            photos = json.loads(self.photos_data)
            if photos and len(photos) > 0:
                return photos[0].get('full_size_url') or photos[0].get('url')
        except (json.JSONDecodeError, KeyError, IndexError, TypeError):
            pass
        return None
