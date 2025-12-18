"""
Repositories - Data Access Layer

Repositories pour l'accès aux données (pattern Repository).

Architecture:
- Isolation de la logique DB
- Opérations CRUD standards
- Queries optimisées

Repositories disponibles:
- VintedProductRepository: Gestion VintedProduct (CRUD + analytics)
- VintedErrorLogRepository: Gestion VintedErrorLog (CRUD + statistiques)
- CategoryMappingRepository: Mapping categories -> plateformes (Vinted, Etsy, eBay)
- VintedMappingRepository: Mapping bidirectionnel Stoflow ↔ Vinted (vinted_mapping table)

Created: 2024-12-10
Updated: 2025-12-18 - Ajout VintedMappingRepository
"""

from .category_mapping_repository import CategoryMappingRepository
from .vinted_mapping_repository import VintedMappingRepository
from .vinted_product_repository import VintedProductRepository
from .vinted_error_log_repository import VintedErrorLogRepository

__all__ = [
    'CategoryMappingRepository',
    'VintedMappingRepository',
    'VintedProductRepository',
    'VintedErrorLogRepository',
]
