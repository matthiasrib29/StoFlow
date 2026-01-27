"""
Etsy Job Handlers - Handlers for Etsy marketplace jobs

Author: Claude
Date: 2026-01-09
"""

from .etsy_publish_job_handler import EtsyPublishJobHandler
from .etsy_update_job_handler import EtsyUpdateJobHandler
from .etsy_delete_job_handler import EtsyDeleteJobHandler

__all__ = [
    'EtsyPublishJobHandler',
    'EtsyUpdateJobHandler',
    'EtsyDeleteJobHandler',
    'ETSY_HANDLERS',
]

# Mapping action_code -> Handler class
ETSY_HANDLERS = {
    "publish_etsy": EtsyPublishJobHandler,
    "update_etsy": EtsyUpdateJobHandler,
    "delete_etsy": EtsyDeleteJobHandler,
}
