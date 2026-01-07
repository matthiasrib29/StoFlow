"""
eBay Job Handlers - Handlers for eBay marketplace jobs

Author: Claude
Date: 2026-01-07
"""

from .ebay_orders_sync_job_handler import EbayOrdersSyncJobHandler

__all__ = [
    'EbayOrdersSyncJobHandler',
    'EBAY_HANDLERS',
]

# Mapping action_code -> Handler class
EBAY_HANDLERS = {
    "sync_orders_ebay": EbayOrdersSyncJobHandler,
}
