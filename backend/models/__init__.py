"""
Models Package

Ce package contient tous les modeles SQLAlchemy pour l'application Stoflow.

Structure:
- models/public: Modeles du schema 'public' (partages entre tous les users)
- models/user: Modeles des schemas users (isoles par user, user_{id})
- models/vinted: Modeles du schema 'vinted' (donnees Vinted partagees)

Updated (2025-12-12): Tous les modeles sont maintenant exportes.
Updated (2025-12-24): Ajout du schema vinted pour les tables Vinted partagees.
"""

# ===== PUBLIC SCHEMA MODELS =====
from models.public import (
    # Users & Subscriptions
    User,
    UserRole,
    SubscriptionTier,
    SubscriptionQuota,
    # Pricing & Credits
    ClothingPrice,
    AICredit,
    # eBay Configuration
    MarketplaceConfig,
    AspectMapping,
    ExchangeRate,
    # Vinted Job System
    VintedActionType,
    # Product Attributes (schema product_attributes)
    Brand,
    Category,
    Closure,
    Color,
    Condition,
    ConditionSup,
    Decade,
    Fit,
    GenderAttribute,
    Length,
    Material,
    Neckline,
    Origin,
    Pattern,
    Rise,
    Season,
    SizeNormalized,
    SizeOriginal,
    SleeveLength,
    Sport,
    Trend,
    UniqueFeature,
)

# ===== VINTED SCHEMA MODELS =====
from models.vinted import (
    VintedCategory,
    VintedMapping,
)

# ===== USER SCHEMA MODELS (user_{id}) =====
from models.user import (
    # Products
    Product,
    ProductStatus,
    # Publications
    PublicationHistory,
    PublicationStatus,
    # AI
    AIGenerationLog,
    # Plugin removed (2026-01-09): Replaced by WebSocket communication
    # PluginTask,
    # TaskStatus,
    # Vinted
    VintedProduct,
    VintedConnection,
    VintedOrder,
    VintedOrderProduct,
    VintedDeletion,
    # Vinted Job System
    MarketplaceJob,
    JobStatus,
    VintedJobStats,
    # eBay
    EbayCredentials,
    EbayProductMarketplace,
    EbayPromotedListing,
    EbayOrder,
    EbayOrderProduct,
    # Etsy
    EtsyCredentials,
)

__all__ = [
    # ===== PUBLIC SCHEMA =====
    # Users & Subscriptions
    "User",
    "UserRole",
    "SubscriptionTier",
    "SubscriptionQuota",
    # Pricing & Credits
    "ClothingPrice",
    "AICredit",
    # eBay Configuration
    "MarketplaceConfig",
    "AspectMapping",
    "ExchangeRate",
    # Vinted Job System (public)
    "VintedActionType",
    # ===== VINTED SCHEMA =====
    "VintedCategory",
    "VintedMapping",
    # Product Attributes
    "Brand",
    "Category",
    "Closure",
    "Color",
    "Condition",
    "ConditionSup",
    "Decade",
    "Fit",
    "GenderAttribute",
    "Length",
    "Material",
    "Neckline",
    "Origin",
    "Pattern",
    "Rise",
    "Season",
    "SizeNormalized",
    "SizeOriginal",
    "SleeveLength",
    "Sport",
    "Trend",
    "UniqueFeature",
    # ===== USER SCHEMA =====
    # Products
    "Product",
    "ProductStatus",
    # Publications
    "PublicationHistory",
    "PublicationStatus",
    # AI
    "AIGenerationLog",
    # Plugin removed (2026-01-09): Replaced by WebSocket communication
    # "PluginTask",
    # "TaskStatus",
    # Vinted
    "VintedProduct",
    "VintedConnection",
    "VintedOrder",
    "VintedOrderProduct",
    "VintedDeletion",
    # Vinted Job System (user)
    "MarketplaceJob",
    "JobStatus",
    "VintedJobStats",
    # eBay
    "EbayCredentials",
    "EbayProductMarketplace",
    "EbayPromotedListing",
    "EbayOrder",
    "EbayOrderProduct",
    # Etsy
    "EtsyCredentials",
]
