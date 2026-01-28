"""
Models Public Schema

Ce package contient tous les modeles SQLAlchemy du schema 'public'.
Ces tables sont partagees entre tous les tenants.

Updated (2025-12-10): Les models d'attributs ont été réactivés.
Ils existent maintenant dans le schema product_attributes (créé via migrations Alembic).

Updated (2025-12-10): Ajout des modèles eBay (marketplace_config, aspect_mappings, exchange_rate_config).

Updated (2024-12-24): Ajout des modèles Documentation (doc_categories, doc_articles).
"""

# Public schema models
from models.public.admin_audit_log import AdminAuditLog
from models.public.doc_article import DocArticle
from models.public.doc_category import DocCategory
from models.public.ebay_aspect_mapping import AspectMapping
from models.public.ebay_category_mapping import EbayCategoryMapping
from models.public.ebay_exchange_rate import ExchangeRate
from models.public.ebay_marketplace_config import MarketplaceConfig
from models.public.subscription_quota import SubscriptionQuota, DEFAULT_QUOTAS, DEFAULT_FEATURES
from models.public.subscription_feature import SubscriptionFeature
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
from models.public.lining import Lining
from models.public.material import Material
from models.public.neckline import Neckline
from models.public.origin import Origin
from models.public.pattern import Pattern
from models.public.rise import Rise
from models.public.season import Season
from models.public.size_length import SizeLength
from models.public.size_normalized import SizeNormalized
from models.public.size_original import SizeOriginal
from models.public.sleeve_length import SleeveLength
from models.public.sport import Sport
from models.public.stretch import Stretch
from models.public.trend import Trend
from models.public.unique_feature import UniqueFeature
# Vinted schema models (re-exported for compatibility)
from models.vinted.vinted_action_type import VintedActionType
from models.vinted.vinted_pro_seller import VintedProSeller
from models.public.vinted_prospect import VintedProspect

__all__ = [
    # Public schema
    "AdminAuditLog",
    "User",
    "UserRole",
    "SubscriptionTier",
    "SubscriptionQuota",
    "SubscriptionFeature",
    "DEFAULT_QUOTAS",
    "DEFAULT_FEATURES",
    "Permission",
    "RolePermission",
    "PermissionCategory",
    # Documentation models
    "DocCategory",
    "DocArticle",
    # eBay public models
    "MarketplaceConfig",
    "AspectMapping",
    "EbayCategoryMapping",
    "ExchangeRate",
    # Vinted job system
    "VintedActionType",
    # Vinted prospection
    "VintedProSeller",
    "VintedProspect",
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
    "Lining",
    "Material",
    "Neckline",
    "Origin",
    "Pattern",
    "Rise",
    "Season",
    "SizeLength",
    "SizeNormalized",
    "SizeOriginal",
    "SleeveLength",
    "Sport",
    "Stretch",
    "Trend",
    "UniqueFeature",
]
