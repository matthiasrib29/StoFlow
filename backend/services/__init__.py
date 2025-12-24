"""
Services Package (Simplified - No Tenant)

Ce package contient tous les services metier de l'application.

TEMPORARILY DISABLED (2025-12-24):
- EbayAdapter, EbayMapper: PlatformMapping model missing
- EtsyAdapter, EtsyMapper: PlatformMapping model missing
"""

from services.auth_service import AuthService
from services.category_service import CategoryService
from services.file_service import FileService
from services.product_service import ProductService
from services.validators import AttributeValidator
from services.vinted.vinted_adapter import VintedAdapter, test_vinted_connection
from services.vinted.vinted_importer import VintedImporter
from services.vinted.vinted_mapper import VintedMapper
from services.vinted.vinted_publisher import VintedPublisher

# TEMPORARILY DISABLED - PlatformMapping model missing
# from services.ebay.ebay_adapter import EbayAdapter
# from services.ebay.ebay_mapper import EbayMapper
# from services.etsy.etsy_adapter import EtsyAdapter
# from services.etsy.etsy_mapper import EtsyMapper

__all__ = [
    "AttributeValidator",
    "AuthService",
    "CategoryService",
    # "EbayAdapter",  # DISABLED
    # "EbayMapper",   # DISABLED
    # "EtsyAdapter",  # DISABLED
    # "EtsyMapper",   # DISABLED
    "FileService",
    "ProductService",
    "VintedAdapter",
    "VintedImporter",
    "VintedMapper",
    "VintedPublisher",
    "test_vinted_connection",
]
