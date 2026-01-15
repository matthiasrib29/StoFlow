"""
Product Model - Schema Utilisateur

Ce modèle représente un produit créé par un utilisateur.
Chaque produit est isolé dans le schema de l'utilisateur (user_{id}).

Business Rules (Updated: 2026-01-03):
- Statuts complets avec workflow MVP (DRAFT, PUBLISHED, SOLD, ARCHIVED)
- Réplication complète de pythonApiWOO (26+ attributs)
- Foreign keys vers tables d'attributs (public schema)
- Soft delete via deleted_at
- ID auto-incrémenté comme identifiant unique (SERIAL)
- Images stockées en JSONB: [{url, order, created_at}]
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
        Index("idx_product_condition", "condition"),
        Index("idx_product_sport", "sport"),
        Index("idx_product_neckline", "neckline"),
        Index("idx_product_length", "length"),
        Index("idx_product_pattern", "pattern"),
        Index("idx_product_stretch", "stretch"),
        Index("idx_product_status", "status"),
        Index("idx_product_created_at", "created_at"),
        Index("idx_product_deleted_at", "deleted_at"),
        # Foreign Key Constraints (cross-schema to product_attributes)
        # NOTE (2025-12-30): FK réactivées - tables product_attributes existent
        # Ces FK assurent l'intégrité référentielle des attributs produit
        ForeignKeyConstraint(
            ["brand"],
            ["brands.name"] if os.getenv('TESTING') else ["product_attributes.brands.name"],
            onupdate="CASCADE",
            ondelete="SET NULL",
            name="fk_products_brand",
        ),
        ForeignKeyConstraint(
            ["category"],
            ["categories.name_en"] if os.getenv('TESTING') else ["product_attributes.categories.name_en"],
            onupdate="CASCADE",
            ondelete="SET NULL",
            name="fk_products_category",
        ),
        ForeignKeyConstraint(
            ["condition"],
            ["conditions.note"] if os.getenv('TESTING') else ["product_attributes.conditions.note"],
            onupdate="CASCADE",
            ondelete="SET NULL",
            name="fk_products_condition",
        ),
        ForeignKeyConstraint(
            ["size_normalized"],
            ["sizes_normalized.name_en"] if os.getenv('TESTING') else ["product_attributes.sizes_normalized.name_en"],
            onupdate="CASCADE",
            ondelete="SET NULL",
            name="fk_products_size_normalized",
        ),
        ForeignKeyConstraint(
            ["size_original"],
            ["sizes_original.name"] if os.getenv('TESTING') else ["product_attributes.sizes_original.name"],
            onupdate="CASCADE",
            ondelete="SET NULL",
            name="fk_products_size_original",
        ),
        # Removed: fk_products_color (column dropped, replaced by product_colors M2M)
        # Removed: fk_products_material (column dropped, replaced by product_materials M2M)
        ForeignKeyConstraint(
            ["fit"],
            ["fits.name_en"] if os.getenv('TESTING') else ["product_attributes.fits.name_en"],
            onupdate="CASCADE",
            ondelete="SET NULL",
            name="fk_products_fit",
        ),
        ForeignKeyConstraint(
            ["gender"],
            ["genders.name_en"] if os.getenv('TESTING') else ["product_attributes.genders.name_en"],
            onupdate="CASCADE",
            ondelete="SET NULL",
            name="fk_products_gender",
        ),
        ForeignKeyConstraint(
            ["season"],
            ["seasons.name_en"] if os.getenv('TESTING') else ["product_attributes.seasons.name_en"],
            onupdate="CASCADE",
            ondelete="SET NULL",
            name="fk_products_season",
        ),
        ForeignKeyConstraint(
            ["neckline"],
            ["necklines.name_en"] if os.getenv('TESTING') else ["product_attributes.necklines.name_en"],
            onupdate="CASCADE",
            ondelete="SET NULL",
            name="fk_products_neckline",
        ),
        ForeignKeyConstraint(
            ["pattern"],
            ["patterns.name_en"] if os.getenv('TESTING') else ["product_attributes.patterns.name_en"],
            onupdate="CASCADE",
            ondelete="SET NULL",
            name="fk_products_pattern",
        ),
        ForeignKeyConstraint(
            ["sport"],
            ["sports.name_en"] if os.getenv('TESTING') else ["product_attributes.sports.name_en"],
            onupdate="CASCADE",
            ondelete="SET NULL",
            name="fk_products_sport",
        ),
        ForeignKeyConstraint(
            ["length"],
            ["lengths.name_en"] if os.getenv('TESTING') else ["product_attributes.lengths.name_en"],
            onupdate="CASCADE",
            ondelete="SET NULL",
            name="fk_products_length",
        ),
        ForeignKeyConstraint(
            ["rise"],
            ["rises.name_en"] if os.getenv('TESTING') else ["product_attributes.rises.name_en"],
            onupdate="CASCADE",
            ondelete="SET NULL",
            name="fk_products_rise",
        ),
        ForeignKeyConstraint(
            ["closure"],
            ["closures.name_en"] if os.getenv('TESTING') else ["product_attributes.closures.name_en"],
            onupdate="CASCADE",
            ondelete="SET NULL",
            name="fk_products_closure",
        ),
        ForeignKeyConstraint(
            ["sleeve_length"],
            ["sleeve_lengths.name_en"] if os.getenv('TESTING') else ["product_attributes.sleeve_lengths.name_en"],
            onupdate="CASCADE",
            ondelete="SET NULL",
            name="fk_products_sleeve_length",
        ),
        ForeignKeyConstraint(
            ["origin"],
            ["origins.name_en"] if os.getenv('TESTING') else ["product_attributes.origins.name_en"],
            onupdate="CASCADE",
            ondelete="SET NULL",
            name="fk_products_origin",
        ),
        ForeignKeyConstraint(
            ["decade"],
            ["decades.name_en"] if os.getenv('TESTING') else ["product_attributes.decades.name_en"],
            onupdate="CASCADE",
            ondelete="SET NULL",
            name="fk_products_decade",
        ),
        ForeignKeyConstraint(
            ["trend"],
            ["trends.name_en"] if os.getenv('TESTING') else ["product_attributes.trends.name_en"],
            onupdate="CASCADE",
            ondelete="SET NULL",
            name="fk_products_trend",
        ),
        ForeignKeyConstraint(
            ["stretch"],
            ["stretches.name_en"] if os.getenv('TESTING') else ["product_attributes.stretches.name_en"],
            onupdate="CASCADE",
            ondelete="SET NULL",
            name="fk_products_stretch",
        ),
        {"schema": "tenant"},  # Placeholder for schema_translate_map
    )

    # ===== PRIMARY KEY =====
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # ===== OPTIMISTIC LOCKING =====
    version_number: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="Version number for optimistic locking (incremented on each update)"
    )

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
    condition: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="État - note 0-10 (FK product_attributes.conditions.note)"
    )
    size_normalized: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True, comment="Taille standardisée (FK product_attributes.sizes_normalized)"
    )
    size_original: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Taille originale (FK product_attributes.sizes_original, auto-créée)"
    )
    # Removed: color (column dropped, replaced by product_colors M2M table)
    # Removed: material (column dropped, replaced by product_materials M2M table)
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

    # ===== ATTRIBUTS AVEC FK (SUITE) =====
    rise: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Hauteur de taille (FK product_attributes.rises)"
    )
    closure: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Type de fermeture (FK product_attributes.closures)"
    )
    sleeve_length: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Longueur de manches (FK product_attributes.sleeve_lengths)"
    )
    origin: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Origine/provenance (FK product_attributes.origins)"
    )
    decade: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Décennie (FK product_attributes.decades)"
    )
    trend: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Tendance (FK product_attributes.trends)"
    )
    stretch: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Stretch/Elasticity (FK product_attributes.stretches)"
    )
    lining: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Lining type (FK product_attributes.linings)"
    )

    # ===== ATTRIBUTS TEXTE LIBRE (SANS FK) =====
    # Removed: condition_sup (column dropped, replaced by product_condition_sups M2M table)
    location: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Emplacement physique (texte libre)"
    )
    model: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Référence modèle (texte libre)"
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
    unique_feature: Mapped[list | None] = mapped_column(
        JSONB, nullable=True, comment="Features uniques (JSONB array ex: ['Vintage', 'Logo brodé', 'Pièce unique'])"
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

    # ===== IMAGES (JSONB) =====
    # Structure: [{"url": "...", "order": 0, "created_at": "..."}, ...]
    # Max 20 images par produit (limite Vinted)
    images: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
        server_default="[]",
        comment="Product images as JSONB array [{url, order, created_at}]",
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
    sold_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Date de vente"
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Date de suppression (soft delete)",
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

    # Marketplace relations
    # VintedProduct (1:1 relationship via product_id FK in vinted_products)
    # lazy="select" to avoid unnecessary JOINs on product lists
    # Use selectinload() when you need the relation
    vinted_product: Mapped["VintedProduct | None"] = relationship(
        "VintedProduct",
        back_populates="product",
        uselist=False,
        lazy="select"
    )

    # EbayProduct (1:1 relationship via product_id FK in ebay_products)
    # lazy="select" to avoid unnecessary JOINs on product lists
    # Use selectinload() when you need the relation
    ebay_product: Mapped["EbayProduct | None"] = relationship(
        "EbayProduct",
        back_populates="product",
        uselist=False,
        lazy="select"
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
    #     "Size", foreign_keys=[size_normalized], viewonly=True
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

    # ===== MANY-TO-MANY RELATIONSHIPS (NEW - 2026-01-07) =====
    product_colors: Mapped[list["ProductColor"]] = relationship(
        "ProductColor",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    product_materials: Mapped[list["ProductMaterial"]] = relationship(
        "ProductMaterial",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    product_condition_sups: Mapped[list["ProductConditionSup"]] = relationship(
        "ProductConditionSup",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # ===== ONE-TO-MANY RELATIONSHIP - PRODUCT IMAGES (NEW - 2026-01-15) =====
    product_images: Mapped[list["ProductImage"]] = relationship(
        "ProductImage",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ProductImage.order"
    )

    # ===== HELPER PROPERTIES FOR BACKWARD COMPATIBILITY =====
    @property
    def primary_color(self) -> str | None:
        """
        Return primary color or first color for legacy compatibility.

        Business Rule: Primary color is marked with is_primary=TRUE.
        If no primary, returns first color in list.
        """
        if not self.product_colors:
            return None
        primary = next((pc.color for pc in self.product_colors if pc.is_primary), None)
        return primary or self.product_colors[0].color

    @property
    def colors(self) -> list[str]:
        """Return all colors as a list."""
        return [pc.color for pc in self.product_colors]

    @property
    def materials(self) -> list[str]:
        """Return all materials as a list."""
        return [pm.material for pm in self.product_materials]

    @property
    def condition_sups(self) -> list[str]:
        """Return all condition_sups as a list."""
        return [pcs.condition_sup for pcs in self.product_condition_sups]

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, title='{self.title[:30]}...', status={self.status})>"
