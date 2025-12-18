"""
Services Vinted - Logique metier pour publication sur Vinted

Architecture:
- Services = logique metier pure (calculs, validations, transformations)
- Pas d'acces direct a l'API Vinted (gere par le plugin navigateur)
- Communication: Backend -> Plugin (ordres) -> Backend (resultats)

Services disponibles:
- VintedSyncService: Orchestrateur principal (publish, update, delete)
- VintedApiSyncService: Synchronisation produits depuis API Vinted
- VintedOrderSyncService: Synchronisation commandes Vinted
- VintedDataExtractor: Extraction/normalisation donnees API + HTML parsing
- VintedImporter: Import produits avec extraction HTML
- VintedPricingService: Calcul prix +10% arrondi x.90
- VintedMappingService: Mapping attributs -> IDs Vinted
- VintedProductValidator: Validation business rules
- VintedProductConverter: Construction payloads API
- VintedTitleService: Generation titres SEO (100 caracteres)
- VintedDescriptionService: Generation descriptions SEO (2000 caracteres + hashtags)
- VintedBordereauService: Gestion bordereaux d'expedition

Created: 2024-12-10
Updated: 2025-12-18 - Added HTML parsing and attribute extraction
"""

from .vinted_sync_service import VintedSyncService
from .vinted_api_sync import VintedApiSyncService
from .vinted_order_sync import VintedOrderSyncService
from .vinted_data_extractor import VintedDataExtractor
from .vinted_importer import VintedImporter
from .vinted_product_helpers import (
    upload_product_images,
    save_new_vinted_product,
    should_delete_product,
)
from .vinted_pricing_service import VintedPricingService
from .vinted_mapping_service import VintedMappingService
from .vinted_mapper import VintedMapper
from .vinted_product_validator import VintedProductValidator
from .vinted_product_converter import VintedProductConverter
from .vinted_title_service import VintedTitleService
from .vinted_description_service import VintedDescriptionService
from .vinted_bordereau_service import VintedBordereauService

__all__ = [
    'VintedSyncService',
    'VintedApiSyncService',
    'VintedOrderSyncService',
    'VintedDataExtractor',
    'VintedImporter',
    'VintedPricingService',
    'VintedMappingService',
    'VintedMapper',
    'VintedProductValidator',
    'VintedProductConverter',
    'VintedTitleService',
    'VintedDescriptionService',
    'VintedBordereauService',
]
