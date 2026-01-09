"""
eBay Job Handlers - Handlers for eBay marketplace jobs

Author: Claude
Date: 2026-01-09
"""

from .ebay_publish_job_handler import EbayPublishJobHandler
from .ebay_update_job_handler import EbayUpdateJobHandler
from .ebay_delete_job_handler import EbayDeleteJobHandler
from .ebay_sync_job_handler import EbaySyncJobHandler
from .ebay_orders_sync_job_handler import EbayOrdersSyncJobHandler

__all__ = [
    'EbayPublishJobHandler',
    'EbayUpdateJobHandler',
    'EbayDeleteJobHandler',
    'EbaySyncJobHandler',
    'EbayOrdersSyncJobHandler',
    'EBAY_HANDLERS',
]

# Mapping action_code -> Handler class
EBAY_HANDLERS = {
    "publish_ebay": EbayPublishJobHandler,
    "update_ebay": EbayUpdateJobHandler,
    "delete_ebay": EbayDeleteJobHandler,
    "sync_ebay": EbaySyncJobHandler,
    "sync_orders_ebay": EbayOrdersSyncJobHandler,
}
