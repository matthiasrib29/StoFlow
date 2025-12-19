"""
Models Public Schema

Ce package contient tous les modeles SQLAlchemy du schema 'public'.
Ces tables sont partagees entre tous les tenants.

Updated (2025-12-10): Les models d'attributs ont été réactivés.
Ils existent maintenant dans le schema product_attributes (créé via migrations Alembic).

Updated (2025-12-10): Ajout des modèles eBay (marketplace_config, aspect_mappings, exchange_rate_config).
"""

# Public schema models
from models.public.ai_credit import AICredit
from models.public.clothing_price import ClothingPrice
from models.public.ebay_aspect_mapping import AspectMapping
from models.public.ebay_exchange_rate import ExchangeRate
from models.public.category_platform_mapping import CategoryPlatformMapping
from models.public.ebay_marketplace_config import MarketplaceConfig
from models.public.platform_mapping import Platform, PlatformMapping
from models.public.subscription_quota import SubscriptionQuota
from models.public.user import User, UserRole, SubscriptionTier
from models.public.permission import Permission, RolePermission, PermissionCategory

# Product attributes models (schema product_attributes)
from models.public.brand import Brand
from models.public.category import Category
from models.public.closure import Closure
from models.public.color import Color
from models.public.condition import Condition
from models.public.condition_sup import ConditionSup
from models.public.decade import Decade
from models.public.fit import Fit
from models.public.gender import Gender as GenderAttribute
from models.public.length import Length
from models.public.material import Material
from models.public.neckline import Neckline
from models.public.origin import Origin
from models.public.pattern import Pattern
from models.public.rise import Rise
from models.public.season import Season
from models.public.size import Size
from models.public.sleeve_length import SleeveLength
from models.public.sport import Sport
from models.public.trend import Trend
from models.public.unique_feature import UniqueFeature
from models.public.vinted_action_type import VintedActionType

__all__ = [
    # Public schema
    "User",
    "UserRole",
    "SubscriptionTier",
    "SubscriptionQuota",
    "Permission",
    "RolePermission",
    "PermissionCategory",
    "PlatformMapping",
    "Platform",
    "ClothingPrice",
    "AICredit",
    "CategoryPlatformMapping",
    # eBay public models
    "MarketplaceConfig",
    "AspectMapping",
    "ExchangeRate",
    # Vinted job system
    "VintedActionType",
    # Product attributes schema
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
]
