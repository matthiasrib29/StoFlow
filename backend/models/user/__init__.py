"""
Models User Schema

Ce package contient tous les modeles SQLAlchemy des schemas users (user_{id}).
Ces tables sont isolees par utilisateur et contiennent les donnees specifiques a chaque user.
"""

from models.user.ai_generation_log import AIGenerationLog
from models.user.ebay_credentials import EbayCredentials
from models.user.ebay_marketplace_settings import EbayMarketplaceSettings
from models.user.ebay_order import EbayOrder, EbayOrderProduct
from models.user.ebay_inquiry import EbayInquiry
from models.user.etsy_credentials import EtsyCredentials
from models.user.ebay_product import EbayProduct
# PluginTask removed (2026-01-09): Replaced by WebSocket communication
from models.user.product import Product, ProductStatus
from models.user.product_attributes_m2m import (
    ProductColor,
    ProductMaterial,
    ProductConditionSup,
)
# PublicationHistory removed (2026-01-21): Obsolete, replaced by MarketplaceJob
from models.user.vinted_connection import VintedConnection, DataDomeStatus
from models.user.vinted_conversation import VintedConversation, VintedMessage
from models.user.vinted_product import VintedProduct
# Vinted schema models (re-exported for compatibility)
from models.vinted.vinted_order import VintedOrder, VintedOrderProduct
from models.vinted.vinted_deletion import VintedDeletion
from models.user.marketplace_batch import MarketplaceBatch, MarketplaceBatchStatus, BatchJob, BatchJobStatus
from models.user.marketplace_job import MarketplaceJob, JobStatus
from models.user.pending_action import PendingAction, PendingActionType
# MarketplaceJobStats removed (2026-01-20): Not used

__all__ = [
    "Product",
    "ProductStatus",
    "ProductColor",
    "ProductMaterial",
    "ProductConditionSup",
    "VintedProduct",
    "VintedConnection",
    "DataDomeStatus",
    "VintedConversation",
    "VintedMessage",
    "EbayCredentials",
    "EbayMarketplaceSettings",
    "EtsyCredentials",
    "EbayProduct",
    # "PublicationHistory",  # Removed (2026-01-21): Obsolete, replaced by MarketplaceJob
    # "PublicationStatus",   # Removed (2026-01-21): Obsolete
    "AIGenerationLog",
    # "PluginTask",  # Removed (2026-01-09): Replaced by WebSocket
    # "TaskStatus",  # Removed (2026-01-09): Replaced by WebSocket
    # "EbayPromotedListing",  # Removed (2026-01-20): Merged into EbayProduct
    "EbayOrder",
    "EbayOrderProduct",
    "EbayInquiry",
    "VintedOrder",
    "VintedOrderProduct",
    "VintedDeletion",
    # Marketplace Batch (formerly BatchJob)
    "MarketplaceBatch",
    "MarketplaceBatchStatus",
    "BatchJob",  # Deprecated alias for backward compatibility
    "BatchJobStatus",  # Deprecated alias for backward compatibility
    # Marketplace Job
    "MarketplaceJob",
    "JobStatus",
    # "MarketplaceJobStats",  # Removed (2026-01-20): Not used
    # Pending Actions
    "PendingAction",
    "PendingActionType",
]
