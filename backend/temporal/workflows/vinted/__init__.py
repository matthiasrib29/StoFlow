"""
Vinted Temporal workflows.
"""

from temporal.workflows.vinted.sync_workflow import VintedSyncWorkflow, VintedSyncParams, VintedSyncProgress
from temporal.workflows.vinted.cleanup_workflow import (
    VintedCleanupWorkflow,
    VintedCleanupParams,
    VintedBatchCleanupWorkflow,
    VintedBatchCleanupParams,
)
from temporal.workflows.vinted.pro_seller_scan_workflow import (
    VintedProSellerScanWorkflow,
    VintedProSellerScanParams,
    VintedProSellerScanProgress,
)
from temporal.workflows.vinted.publish_workflow import VintedPublishWorkflow, VintedPublishParams
from temporal.workflows.vinted.update_workflow import VintedUpdateWorkflow, VintedUpdateParams
from temporal.workflows.vinted.delete_workflow import VintedDeleteWorkflow, VintedDeleteParams
from temporal.workflows.vinted.orders_sync_workflow import VintedOrdersSyncWorkflow, VintedOrdersSyncParams
from temporal.workflows.vinted.message_workflow import VintedMessageWorkflow, VintedMessageParams
from temporal.workflows.vinted.link_product_workflow import VintedLinkProductWorkflow, VintedLinkProductParams
from temporal.workflows.vinted.check_connection_workflow import VintedCheckConnectionWorkflow, VintedCheckConnectionParams
from temporal.workflows.vinted.fetch_users_workflow import VintedFetchUsersWorkflow, VintedFetchUsersParams, FetchUsersProgress

# All new action workflows for worker registration
VINTED_ACTION_WORKFLOWS = [
    VintedPublishWorkflow,
    VintedUpdateWorkflow,
    VintedDeleteWorkflow,
    VintedOrdersSyncWorkflow,
    VintedMessageWorkflow,
    VintedLinkProductWorkflow,
    VintedCheckConnectionWorkflow,
    VintedFetchUsersWorkflow,
]

__all__ = [
    # Existing workflows
    "VintedSyncWorkflow",
    "VintedSyncParams",
    "VintedSyncProgress",
    "VintedCleanupWorkflow",
    "VintedCleanupParams",
    "VintedBatchCleanupWorkflow",
    "VintedBatchCleanupParams",
    "VintedProSellerScanWorkflow",
    "VintedProSellerScanParams",
    "VintedProSellerScanProgress",
    # New action workflows
    "VintedPublishWorkflow",
    "VintedPublishParams",
    "VintedUpdateWorkflow",
    "VintedUpdateParams",
    "VintedDeleteWorkflow",
    "VintedDeleteParams",
    "VintedOrdersSyncWorkflow",
    "VintedOrdersSyncParams",
    "VintedMessageWorkflow",
    "VintedMessageParams",
    "VintedLinkProductWorkflow",
    "VintedLinkProductParams",
    "VintedCheckConnectionWorkflow",
    "VintedCheckConnectionParams",
    "VintedFetchUsersWorkflow",
    "VintedFetchUsersParams",
    "FetchUsersProgress",
    "VINTED_ACTION_WORKFLOWS",
]
