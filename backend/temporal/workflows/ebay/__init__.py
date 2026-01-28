"""
eBay-specific Temporal workflows.
"""

from temporal.workflows.ebay.sync_workflow import (
    EbaySyncWorkflow,
    EbaySyncParams,
    SyncProgress,
)
from temporal.workflows.ebay.cleanup_workflow import (
    EbayCleanupWorkflow,
    EbayCleanupParams,
)
from temporal.workflows.ebay.publish_workflow import EbayPublishWorkflow, EbayPublishParams
from temporal.workflows.ebay.update_workflow import EbayUpdateWorkflow, EbayUpdateParams
from temporal.workflows.ebay.delete_workflow import EbayDeleteWorkflow, EbayDeleteParams
from temporal.workflows.ebay.orders_sync_workflow import EbayOrdersSyncWorkflow, EbayOrdersSyncParams
from temporal.workflows.ebay.import_workflow import EbayImportWorkflow, EbayImportParams, ImportProgress

# All new action workflows for worker registration
EBAY_ACTION_WORKFLOWS = [
    EbayPublishWorkflow,
    EbayUpdateWorkflow,
    EbayDeleteWorkflow,
    EbayOrdersSyncWorkflow,
    EbayImportWorkflow,
]

__all__ = [
    # Existing workflows
    "EbaySyncWorkflow",
    "EbaySyncParams",
    "SyncProgress",
    "EbayCleanupWorkflow",
    "EbayCleanupParams",
    # New action workflows
    "EbayPublishWorkflow",
    "EbayPublishParams",
    "EbayUpdateWorkflow",
    "EbayUpdateParams",
    "EbayDeleteWorkflow",
    "EbayDeleteParams",
    "EbayOrdersSyncWorkflow",
    "EbayOrdersSyncParams",
    "EbayImportWorkflow",
    "EbayImportParams",
    "ImportProgress",
    "EBAY_ACTION_WORKFLOWS",
]
