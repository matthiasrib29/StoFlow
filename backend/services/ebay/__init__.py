"""
eBay Services Package

Ce package contient tous les services et clients pour l'intégration eBay multi-marketplace.

Architecture:
- ebay_base_client.py: Client OAuth2 + api_call() générique
- ebay_inventory_client.py: Inventory API (create/update/delete items)
- ebay_offer_client.py: Offer API (publish listings)
- ebay_account_client.py: Account API (policies, location)
- ebay_fulfillment_client.py: Fulfillment API (orders)
- ebay_marketing_client.py: Marketing API (promoted listings)
- ebay_taxonomy_client.py: Taxonomy API (categories)
- ebay_analytics_client.py: Analytics API (metrics)

Author: Claude
Date: 2025-12-10
"""

from services.ebay.ebay_account_client import EbayAccountClient
from services.ebay.ebay_analytics_client import EbayAnalyticsClient
from services.ebay.ebay_base_client import EbayBaseClient
from services.ebay.ebay_fulfillment_client import EbayFulfillmentClient
from services.ebay.ebay_inventory_client import EbayInventoryClient
from services.ebay.ebay_inventory_group_client import EbayInventoryGroupClient
from services.ebay.ebay_marketing_client import EbayMarketingClient
from services.ebay.ebay_offer_client import EbayOfferClient
from services.ebay.ebay_product_conversion_service import EbayProductConversionService
from shared.exceptions import ProductValidationError
from services.ebay.ebay_publication_service import (
    EbayPublicationError,
    EbayPublicationService,
)
from services.ebay.ebay_taxonomy_client import EbayTaxonomyClient

# GPSR Compliance helpers (Phase 4)
from services.ebay import ebay_gpsr_compliance

__all__ = [
    "EbayBaseClient",
    "EbayInventoryClient",
    "EbayInventoryGroupClient",
    "EbayOfferClient",
    "EbayAccountClient",
    "EbayFulfillmentClient",
    "EbayMarketingClient",
    "EbayAnalyticsClient",
    "EbayTaxonomyClient",
    "EbayProductConversionService",
    "ProductValidationError",
    "EbayPublicationService",
    "EbayPublicationError",
    "ebay_gpsr_compliance",
]
