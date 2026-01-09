"""
Vinted Job Handlers - Un handler par type d'action

Chaque handler encapsule la logique métier d'une action spécifique.
Le VintedJobProcessor utilise ces handlers pour exécuter les jobs.

Author: Claude
Date: 2025-12-19
"""

from .base_job_handler import BaseJobHandler
from .publish_job_handler import PublishJobHandler
from .update_job_handler import UpdateJobHandler
from .delete_job_handler import DeleteJobHandler
from .orders_job_handler import OrdersJobHandler
from .sync_job_handler import SyncJobHandler
from .message_job_handler import MessageJobHandler
from .link_product_job_handler import LinkProductJobHandler

__all__ = [
    'BaseJobHandler',
    'PublishJobHandler',
    'UpdateJobHandler',
    'DeleteJobHandler',
    'OrdersJobHandler',
    'SyncJobHandler',
    'MessageJobHandler',
    'LinkProductJobHandler',
    'HANDLERS',
]

# Mapping action_code -> Handler class
# Format: {action}_{marketplace} for unified system (2026-01-09)
HANDLERS = {
    "publish_vinted": PublishJobHandler,
    "update_vinted": UpdateJobHandler,
    "delete_vinted": DeleteJobHandler,
    "orders_vinted": OrdersJobHandler,
    "sync_vinted": SyncJobHandler,
    "message_vinted": MessageJobHandler,
    "link_product_vinted": LinkProductJobHandler,
}
