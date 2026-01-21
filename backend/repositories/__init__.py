"""
Repositories - Data Access Layer

Repositories pour l'accès aux données (pattern Repository).

Architecture:
- Isolation de la logique DB
- Opérations CRUD standards
- Queries optimisées

Repositories disponibles:
- VintedProductRepository: Gestion VintedProduct (CRUD + analytics)
- VintedMappingRepository: Mapping bidirectionnel Stoflow ↔ Vinted (vinted_mapping table)

DEPRECATED:
- CategoryMappingRepository: Désactivé - modèle CategoryPlatformMapping non implémenté

Created: 2024-12-10
Updated: 2025-12-24 - CategoryMappingRepository désactivé (modèle manquant)
"""

# DEPRECATED: CategoryMappingRepository désactivé - modèle manquant
# from .category_mapping_repository import CategoryMappingRepository
# REMOVED (2026-01-09): PluginTask system replaced by WebSocket communication
# from .plugin_task_repository import PluginTaskRepository
from .product_attribute_repository import ProductAttributeRepository
from .product_repository import ProductRepository
from .user_repository import UserRepository
from .vinted_job_repository import VintedJobRepository
from .vinted_mapping_repository import VintedMappingRepository
from .vinted_product_repository import VintedProductRepository
# VintedErrorLogRepository removed (2026-01-21): Never used
from .ebay_inquiry_repository import EbayInquiryRepository

__all__ = [
    # 'CategoryMappingRepository',  # DEPRECATED
    # 'PluginTaskRepository',  # REMOVED (2026-01-09): Replaced by WebSocket
    'ProductAttributeRepository',
    'ProductRepository',
    'UserRepository',
    'VintedJobRepository',
    'VintedMappingRepository',
    'VintedProductRepository',
    # 'VintedErrorLogRepository',  # REMOVED (2026-01-21): Never used
    'EbayInquiryRepository',
]
