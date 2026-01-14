"""
Models User Schema

Ce package contient tous les modeles SQLAlchemy des schemas users (user_{id}).
Ces tables sont isolees par utilisateur et contiennent les donnees specifiques a chaque user.
"""

from models.user.ai_generation_log import AIGenerationLog
from models.user.ebay_credentials import EbayCredentials
from models.user.ebay_order import EbayOrder, EbayOrderProduct
from models.user.ebay_inquiry import EbayInquiry
from models.user.etsy_credentials import EtsyCredentials
from models.user.ebay_product import EbayProduct
from models.user.ebay_product_marketplace import EbayProductMarketplace
from models.user.ebay_promoted_listing import EbayPromotedListing
# PluginTask removed (2026-01-09): Replaced by WebSocket communication
from models.user.product import Product, ProductStatus
from models.user.product_attributes_m2m import (
    ProductColor,
    ProductMaterial,
    ProductConditionSup,
)
from models.user.publication_history import PublicationHistory, PublicationStatus
from models.user.vinted_connection import VintedConnection, DataDomeStatus
from models.user.vinted_conversation import VintedConversation, VintedMessage
from models.user.vinted_product import VintedProduct
# Vinted schema models (re-exported for compatibility)
from models.vinted.vinted_order import VintedOrder, VintedOrderProduct
from models.vinted.vinted_deletion import VintedDeletion
from models.user.batch_job import BatchJob
from models.user.marketplace_job import MarketplaceJob, JobStatus
from models.user.vinted_job_stats import VintedJobStats

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
    "EtsyCredentials",
    "EbayProduct",
    "PublicationHistory",
    "PublicationStatus",
    "AIGenerationLog",
    # "PluginTask",  # Removed (2026-01-09): Replaced by WebSocket
    # "TaskStatus",  # Removed (2026-01-09): Replaced by WebSocket
    "EbayProductMarketplace",
    "EbayPromotedListing",
    "EbayOrder",
    "EbayOrderProduct",
    "EbayInquiry",
    "VintedOrder",
    "VintedOrderProduct",
    "VintedDeletion",
    "BatchJob",
    "MarketplaceJob",
    "JobStatus",
    "VintedJobStats",
]
