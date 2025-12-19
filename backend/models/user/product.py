"""
Product Model - Schema Utilisateur

Ce modèle représente un produit créé par un utilisateur.
Chaque produit est isolé dans le schema de l'utilisateur (user_{id}).

Business Rules (Updated: 2025-12-09):
- Statuts complets avec workflow MVP (DRAFT, PUBLISHED, SOLD, ARCHIVED)
- Réplication complète de pythonApiWOO (26+ attributs)
- Foreign keys vers tables d'attributs (public schema)
- Soft delete via deleted_at
- ID auto-incrémenté comme identifiant unique (SERIAL)
- Images gérées via ProductImage (table séparée)
"""

import os
from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    DECIMAL,
    CheckConstraint,
    DateTime,
    Enum as SQLEnum,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base


class ProductStatus(str, Enum):
    """
    Statuts disponibles pour un produit.

    Workflow MVP (2025-12-04):
    - DRAFT: Brouillon (en cours d'édition)
    - PUBLISHED: Publié sur marketplaces
    - SOLD: Vendu
    - ARCHIVED: Archivé (retiré de la vente)

    Autres statuts (post-MVP):
    - PENDING_REVIEW: En attente de review
    - APPROVED: Approuvé (pré-publication)
    - REJECTED: Rejeté par review
    - SCHEDULED: Publication programmée
    - SUSPENDED: Suspendu (modération)
    - FLAGGED: Signalé (modération)
    """

    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    SUSPENDED = "suspended"
    FLAGGED = "flagged"
    SOLD = "sold"
    ARCHIVED = "archived"


class Product(Base):
    """
    Modèle Product - Représente un produit d'un utilisateur.

    Extended Attributes (Updated: 2025-12-08):
    - 33+ attributs de pythonApiWOO répliqués
    - FK vers tables product_attributes (brand, category, condition, color, etc.)
    - 6 dimensions pour measurements (dim1-dim6)
    - Attributs de tarification (pricing_rarity, pricing_quality, etc.)
    - Features descriptifs (unique_feature, marking)
    - Soft delete (deleted_at)
    - Stock quantity tracking
    """

    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("stock_quantity >= 0", name="check_stock_positive"),
        # Indexes
        Index("idx_product_brand", "brand"),
        Index("idx_product_category", "category"),
        Index("idx_product_color", "color"),
        Index("idx_product_condition", "condition"),
        Index("idx_product_sport", "sport"),
        Index("idx_product_neckline", "neckline"),
        Index("idx_product_length", "length"),
        Index("idx_product_pattern", "pattern"),
        Index("idx_product_status", "status"),
        Index("idx_product_created_at", "created_at"),
        Index("idx_product_deleted_at", "deleted_at"),
        # Foreign Key Constraints (cross-schema)
        # NOTE (2025-12-09): ForeignKeys désactivées car les tables d'attributs
        # (brands, categories, colors, etc.) n'existent plus en DB
        # Les colonnes restent en String pour flexibilité (valeurs libres)
        # TODO: Réactiver si tables d'attributs sont recréées
        # ForeignKeyConstraint(
        #     ["brand"],
        #     ["brands.name"] if os.getenv('TESTING') else ["product_attributes.brands.name"],
        #     onupdate="CASCADE",
        #     ondelete="SET NULL",
        #     name="fk_products_brand",
        # ),
        # ForeignKeyConstraint(
        #     ["category"],
        #     ["categories.name_en"] if os.getenv('TESTING') else ["product_attributes.categories.name_en"],
        #     onupdate="CASCADE",
        #     ondelete="RESTRICT",
        #     name="fk_products_category",
        # ),
        # ForeignKeyConstraint(
        #     ["condition"],
        #     ["conditions.name"] if os.getenv('TESTING') else ["product_attributes.conditions.name"],
        #     onupdate="CASCADE",
        #     ondelete="RESTRICT",
        #     name="fk_products_condition",
        # ),
        # ForeignKeyConstraint(
        #     ["label_size"],
        #     ["sizes.name"] if os.getenv('TESTING') else ["product_attributes.sizes.name"],
        #     onupdate="CASCADE",
        #     ondelete="SET NULL",
        #     name="fk_products_size",
        # ),
        # ForeignKeyConstraint(
        #     ["color"],
        #     ["colors.name_en"] if os.getenv('TESTING') else ["product_attributes.colors.name_en"],
        #     onupdate="CASCADE",
        #     ondelete="SET NULL",
        #     name="fk_products_color",
        # ),
        # ForeignKeyConstraint(
        #     ["material"],
        #     ["materials.name_en"] if os.getenv('TESTING') else ["product_attributes.materials.name_en"],
        #     onupdate="CASCADE",
        #     ondelete="SET NULL",
        #     name="fk_products_material",
        # ),
        # ForeignKeyConstraint(
        #     ["fit"],
        #     ["fits.name_en"] if os.getenv('TESTING') else ["public.fits.name_en"],
        #     onupdate="CASCADE",
        #     ondelete="SET NULL",
        #     name="fk_products_fit",
        # ),
        # ForeignKeyConstraint(
        #     ["gender"],
        #     ["genders.name_en"] if os.getenv('TESTING') else ["public.genders.name_en"],
        #     onupdate="CASCADE",
        #     ondelete="SET NULL",
        #     name="fk_products_gender",
        # ),
        # ForeignKeyConstraint(
        #     ["season"],
        #     ["seasons.name_en"] if os.getenv('TESTING') else ["product_attributes.seasons.name_en"],
        #     onupdate="CASCADE",
        #     ondelete="SET NULL",
        #     name="fk_products_season",
        # ),
    )

    # ===== PRIMARY KEY =====
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # ===== BUSINESS FIELDS (BASE) =====
    title: Mapped[str] = mapped_column(
        String(500), nullable=False, index=True, comment="Titre du produit"
    )
    description: Mapped[str] = mapped_column(Text, nullable=False, comment="Description complète")
    price: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2), nullable=False, comment="Prix de vente"
    )

    # ===== FOREIGN KEYS VERS PUBLIC (ATTRIBUTS PRINCIPAUX) =====
    category: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True, comment="Catégorie (FK public.categories)"
    )
    brand: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Marque (FK public.brands)"
    )
    condition: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="État (FK public.conditions)"
    )
    size: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True, comment="Taille standardisée (FK product_attributes.sizes)"
    )
    label_size: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Taille étiquette (texte libre)"
    )
    color: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True, comment="Couleur (FK public.colors)"
    )
    material: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Matière (FK public.materials)"
    )
    fit: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Coupe (FK public.fits)"
    )
    gender: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Genre (FK public.genders)"
    )
    season: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Saison (FK public.seasons)"
    )
    sport: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Sport (FK product_attributes.sports)"
    )
    neckline: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Encolure (FK product_attributes.necklines)"
    )
    length: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Longueur (FK product_attributes.lengths)"
    )
    pattern: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Motif (FK product_attributes.patterns)"
    )

    # ===== ATTRIBUTS SUPPLÉMENTAIRES (SANS FK) =====
    condition_sup: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="État supplémentaire/détails"
    )
    rise: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Hauteur de taille (pantalons)"
    )
    closure: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Type de fermeture"
    )
    sleeve_length: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Longueur de manches"
    )
    origin: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Origine/provenance"
    )
    decade: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Décennie"
    )
    trend: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Tendance"
    )
    name_sup: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Titre supplémentaire"
    )
    location: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Emplacement physique"
    )
    model: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Référence modèle"
    )

    # ===== ATTRIBUTS DE TARIFICATION (PRICING) =====
    pricing_edit: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Prix édité manuellement (indicateur)"
    )
    pricing_rarity: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Rareté pour calcul prix"
    )
    pricing_quality: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Qualité pour calcul prix"
    )
    pricing_details: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Détails spécifiques pour calcul prix"
    )
    pricing_style: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Style pour tarification"
    )

    # ===== FEATURES DESCRIPTIFS =====
    unique_feature: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Features uniques séparées par virgules (ex: Vintage,Logo brodé,Pièce unique)"
    )
    marking: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Marquages/écritures visibles séparés par virgules (dates, codes, textes)"
    )

    # ===== DIMENSIONS (MEASUREMENTS EN CM) =====
    dim1: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Dimension 1: Tour de poitrine/Épaules (cm)"
    )
    dim2: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Dimension 2: Longueur totale (cm)"
    )
    dim3: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Dimension 3: Longueur manche (cm)"
    )
    dim4: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Dimension 4: Tour de taille (cm)"
    )
    dim5: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Dimension 5: Tour de hanches (cm)"
    )
    dim6: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Dimension 6: Entrejambe (cm)"
    )

    # ===== STOCK =====
    stock_quantity: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="Quantité en stock"
    )

    # ===== IMAGES (DEPRECATED - Utiliser product_images relationship) =====
    images: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="DEPRECATED: JSON array d'URLs. Utiliser product_images relationship",
    )

    # ===== STATUS ET WORKFLOW =====
    status: Mapped[ProductStatus] = mapped_column(
        SQLEnum(ProductStatus, name="product_status", create_type=True),
        default=ProductStatus.DRAFT,
        nullable=False,
        index=True,
        comment="Statut du produit (workflow MVP: DRAFT, PUBLISHED, SOLD, ARCHIVED)",
    )

    # ===== DATES IMPORTANTES =====
    scheduled_publish_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Date de publication programmée (si status=scheduled)",
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Date de publication effective"
    )
    sold_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Date de vente"
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Date de suppression (soft delete)",
    )

    # ===== INTEGRATION METADATA =====
    integration_metadata: Mapped[dict | None] = mapped_column(
        JSONB,  # NOTE: Always JSONB (PostgreSQL) - tests now use PostgreSQL (not SQLite)
        nullable=True,
        comment="Métadonnées pour intégrations (vinted_id, source, etc.)",
    )

    # ===== TIMESTAMPS =====
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

    # ProductImages (nouvelle table)
    product_images: Mapped[list["ProductImage"]] = relationship(
        "ProductImage",
        back_populates="product",
        order_by="ProductImage.display_order",
        cascade="all, delete-orphan",
    )

    # Marketplace relations
    # VintedProduct (1:1 relationship via product_id FK in vinted_products)
    vinted_product: Mapped["VintedProduct | None"] = relationship(
        "VintedProduct",
        back_populates="product",
        uselist=False,
        lazy="joined"
    )

    # EbayProduct (1:1 relationship via product_id FK in ebay_products)
    ebay_product: Mapped["EbayProduct | None"] = relationship(
        "EbayProduct",
        back_populates="product",
        uselist=False,
        lazy="joined"
    )

    publication_history: Mapped[list["PublicationHistory"]] = relationship(
        "PublicationHistory", back_populates="product", cascade="all, delete-orphan"
    )

    ai_generation_logs: Mapped[list["AIGenerationLog"]] = relationship(
        "AIGenerationLog", back_populates="product", cascade="all, delete-orphan"
    )

    # Attribute relations (vers public schema) - Commented out to fix SQLAlchemy error
    # TODO: Add explicit primaryjoin for each relationship
    # brand_rel: Mapped["Brand | None"] = relationship(
    #     "Brand", foreign_keys=[brand], viewonly=True
    # )
    # category_rel: Mapped["Category | None"] = relationship(
    #     "Category", foreign_keys=[category], viewonly=True
    # )
    # condition_rel: Mapped["Condition | None"] = relationship(
    #     "Condition", foreign_keys=[condition], viewonly=True
    # )
    # size_rel: Mapped["Size | None"] = relationship(
    #     "Size", foreign_keys=[label_size], viewonly=True
    # )
    # color_rel: Mapped["Color | None"] = relationship(
    #     "Color", foreign_keys=[color], viewonly=True
    # )
    # material_rel: Mapped["Material | None"] = relationship(
    #     "Material", foreign_keys=[material], viewonly=True
    # )
    # fit_rel: Mapped["Fit | None"] = relationship("Fit", foreign_keys=[fit], viewonly=True)
    # gender_rel: Mapped["Gender | None"] = relationship(
    #     "Gender", foreign_keys=[gender], viewonly=True
    # )
    # season_rel: Mapped["Season | None"] = relationship(
    #     "Season", foreign_keys=[season], viewonly=True
    # )

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, title='{self.title[:30]}...', status={self.status})>"
