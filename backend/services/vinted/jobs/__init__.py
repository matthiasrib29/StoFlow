"""
Vinted Job Handlers - Un handler par type d'action

Chaque handler encapsule la logique métier d'une action spécifique.
Le MarketplaceJobProcessor utilise ces handlers pour exécuter les jobs.

Note: Sync is handled by Temporal workflow (VintedSyncWorkflow) since 2026-01-22.

Author: Claude
Date: 2025-12-19
Updated: 2026-01-22 - Removed SyncJobHandler (now Temporal), updated to MarketplaceJobProcessor
"""

from .base_job_handler import BaseJobHandler
from .publish_job_handler import PublishJobHandler
from .update_job_handler import UpdateJobHandler
from .delete_job_handler import DeleteJobHandler
from .orders_job_handler import OrdersJobHandler
from .message_job_handler import MessageJobHandler
from .link_product_job_handler import LinkProductJobHandler
from .fetch_users_job_handler import FetchUsersJobHandler
from .check_connection_job_handler import CheckConnectionJobHandler

__all__ = [
    'BaseJobHandler',
    'PublishJobHandler',
    'UpdateJobHandler',
    'DeleteJobHandler',
    'OrdersJobHandler',
    'MessageJobHandler',
    'LinkProductJobHandler',
    'FetchUsersJobHandler',
    'CheckConnectionJobHandler',
    'HANDLERS',
]

# Mapping action_code -> Handler class
# Format: {action}_{marketplace} for unified system (2026-01-09)
HANDLERS = {
    "publish_vinted": PublishJobHandler,
    "update_vinted": UpdateJobHandler,
    "delete_vinted": DeleteJobHandler,
    "orders_vinted": OrdersJobHandler,
    "message_vinted": MessageJobHandler,
    "link_product_vinted": LinkProductJobHandler,
    "fetch_users_vinted": FetchUsersJobHandler,
    "check_connection_vinted": CheckConnectionJobHandler,
}
