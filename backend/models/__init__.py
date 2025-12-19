"""
Models Package

Ce package contient tous les modeles SQLAlchemy pour l'application Stoflow.

Structure:
- models/public: Modeles du schema 'public' (partages entre tous les users)
- models/user: Modeles des schemas users (isoles par user, user_{id})

Updated (2025-12-12): Tous les modeles sont maintenant exportes.
"""

# ===== PUBLIC SCHEMA MODELS =====
from models.public import (
    # Users & Subscriptions
    User,
    UserRole,
    SubscriptionTier,
    SubscriptionQuota,
    # Platforms
    Platform,
    PlatformMapping,
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
    Size,
    SleeveLength,
    Sport,
    Trend,
    UniqueFeature,
)

# ===== USER SCHEMA MODELS (user_{id}) =====
from models.user import (
    # Products
    Product,
    ProductStatus,
    ProductImage,
    # Publications
    PublicationHistory,
    PublicationStatus,
    # AI
    AIGenerationLog,
    # Plugin
    PluginTask,
    TaskStatus,
    # Vinted
    VintedProduct,
    VintedConnection,
    VintedOrder,
    VintedOrderProduct,
    VintedDeletion,
    # Vinted Job System
    VintedJob,
    JobStatus,
    VintedJobStats,
    # eBay
    EbayCredentials,
    EbayProductMarketplace,
    EbayPromotedListing,
    EbayOrder,
    EbayOrderProduct,
)

__all__ = [
    # ===== PUBLIC SCHEMA =====
    # Users & Subscriptions
    "User",
    "UserRole",
    "SubscriptionTier",
    "SubscriptionQuota",
    # Platforms
    "Platform",
    "PlatformMapping",
    # Pricing & Credits
    "ClothingPrice",
    "AICredit",
    # eBay Configuration
    "MarketplaceConfig",
    "AspectMapping",
    "ExchangeRate",
    # Vinted Job System (public)
    "VintedActionType",
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
    "Size",
    "SleeveLength",
    "Sport",
    "Trend",
    "UniqueFeature",
    # ===== USER SCHEMA =====
    # Products
    "Product",
    "ProductStatus",
    "ProductImage",
    # Publications
    "PublicationHistory",
    "PublicationStatus",
    # AI
    "AIGenerationLog",
    # Plugin
    "PluginTask",
    "TaskStatus",
    # Vinted
    "VintedProduct",
    "VintedConnection",
    "VintedOrder",
    "VintedOrderProduct",
    "VintedDeletion",
    # Vinted Job System (user)
    "VintedJob",
    "JobStatus",
    "VintedJobStats",
    # eBay
    "EbayCredentials",
    "EbayProductMarketplace",
    "EbayPromotedListing",
    "EbayOrder",
    "EbayOrderProduct",
]
