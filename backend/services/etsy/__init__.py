"""
Etsy Services Package

Ce package contient tous les services et clients pour l'intégration Etsy API v3.

Architecture:
- etsy_base_client.py: Client OAuth2 + api_call() générique
- etsy_listing_client.py: Listing API (create/update/delete listings)
- etsy_product_conversion_service.py: Convert Stoflow → Etsy format
- etsy_publication_service.py: Orchestrator pour publier produits
- etsy_shop_client.py: Shop Management API (shop, sections)
- etsy_receipt_client.py: Receipt/Order Management API
- etsy_shipping_client.py: Shipping API (profiles, templates)
- etsy_taxonomy_client.py: Taxonomy API (categories)
- etsy_polling_service.py: Polling service (alternative aux webhooks)

Note: Etsy n'a PAS de webhooks natifs, utiliser le polling service.

Author: Claude
Date: 2025-12-10
"""

from services.etsy.etsy_adapter import EtsyAdapter
from services.etsy.etsy_base_client import EtsyBaseClient
from services.etsy.etsy_listing_client import EtsyListingClient
from services.etsy.etsy_mapper import EtsyMapper
from services.etsy.etsy_polling_service import EtsyPollingService
from services.etsy.etsy_product_conversion_service import EtsyProductConversionService
from shared.exceptions import ProductValidationError
from services.etsy.etsy_publication_service import (
    EtsyPublicationError,
    EtsyPublicationService,
)
from services.etsy.etsy_receipt_client import EtsyReceiptClient
from services.etsy.etsy_shipping_client import EtsyShippingClient
from services.etsy.etsy_shop_client import EtsyShopClient
from services.etsy.etsy_taxonomy_client import EtsyTaxonomyClient

__all__ = [
    # Legacy (V1)
    "EtsyAdapter",
    "EtsyMapper",
    # V3 Clients
    "EtsyBaseClient",
    "EtsyListingClient",
    "EtsyShopClient",
    "EtsyReceiptClient",
    "EtsyShippingClient",
    "EtsyTaxonomyClient",
    # Services
    "EtsyProductConversionService",
    "ProductValidationError",
    "EtsyPublicationService",
    "EtsyPublicationError",
    "EtsyPollingService",
]
