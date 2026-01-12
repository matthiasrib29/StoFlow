"""
Services Vinted - Logique metier pour publication sur Vinted

Architecture:
- Services = logique metier pure (calculs, validations, transformations)
- Pas d'acces direct a l'API Vinted (gere par le plugin navigateur)
- Communication: Backend -> Plugin (ordres) -> Backend (resultats)

Services disponibles:
- VintedJobService: Gestion des jobs (creation, status, priorite, stats)
- VintedJobProcessor: [DEPRECATED] Use MarketplaceJobProcessor instead
- VintedSyncService: Operations Vinted (publish, update, delete)
- VintedApiSyncService: Synchronisation produits depuis API Vinted
- VintedOrderSyncService: Synchronisation commandes Vinted
- VintedItemUploadParser: Parse JSON de /api/v2/item_upload/items/{id} (NEW)
- VintedProductEnricher: Enrichit produits via API item_upload (UPDATED)
- VintedDataExtractor: Extraction/normalisation donnees API (DEPRECATED for HTML)
- VintedImporter: Import produits avec extraction HTML
- VintedPricingService: Calcul prix +10% arrondi x.90
- VintedMappingService: Mapping attributs -> IDs Vinted
- VintedProductValidator: Validation business rules
- VintedProductConverter: Construction payloads API
- VintedTitleService: Generation titres SEO (100 caracteres)
- VintedDescriptionService: Generation descriptions SEO (2000 caracteres + hashtags)
- VintedBordereauService: Gestion bordereaux d'expedition
- VintedLinkService: Liaison produits Vinted ↔ Stoflow

Created: 2024-12-10
Updated: 2025-01-03 - Added VintedLinkService
Updated: 2026-01-05 - Added VintedItemUploadParser, updated VintedProductEnricher
"""

from .vinted_job_service import VintedJobService
from .vinted_link_service import VintedLinkService
from .vinted_job_processor import VintedJobProcessor
from .vinted_sync_service import VintedSyncService
from .vinted_api_sync import VintedApiSyncService
from .vinted_order_sync import VintedOrderSyncService
from .vinted_item_upload_parser import VintedItemUploadParser
from .vinted_product_enricher import VintedProductEnricher
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
    'VintedJobService',
    'VintedJobProcessor',
    'VintedLinkService',
    'VintedSyncService',
    'VintedApiSyncService',
    'VintedOrderSyncService',
    'VintedItemUploadParser',
    'VintedProductEnricher',
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
