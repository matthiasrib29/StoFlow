"""
Etsy Job Handlers - Handlers for Etsy marketplace jobs

Author: Claude
Date: 2026-01-09
"""

from .etsy_publish_job_handler import EtsyPublishJobHandler
from .etsy_update_job_handler import EtsyUpdateJobHandler
from .etsy_delete_job_handler import EtsyDeleteJobHandler
from .etsy_sync_job_handler import EtsySyncJobHandler
from .etsy_orders_sync_job_handler import EtsyOrdersSyncJobHandler

__all__ = [
    'EtsyPublishJobHandler',
    'EtsyUpdateJobHandler',
    'EtsyDeleteJobHandler',
    'EtsySyncJobHandler',
    'EtsyOrdersSyncJobHandler',
    'ETSY_HANDLERS',
]

# Mapping action_code -> Handler class
ETSY_HANDLERS = {
    "publish_etsy": EtsyPublishJobHandler,
    "update_etsy": EtsyUpdateJobHandler,
    "delete_etsy": EtsyDeleteJobHandler,
    "sync_etsy": EtsySyncJobHandler,
    "sync_orders_etsy": EtsyOrdersSyncJobHandler,
}
