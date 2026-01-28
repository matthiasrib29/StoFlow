"""Etsy Temporal workflows."""

from temporal.workflows.etsy.publish_workflow import EtsyPublishWorkflow, EtsyPublishParams
from temporal.workflows.etsy.update_workflow import EtsyUpdateWorkflow, EtsyUpdateParams
from temporal.workflows.etsy.delete_workflow import EtsyDeleteWorkflow, EtsyDeleteParams

# All Etsy action workflows for worker registration
ETSY_ACTION_WORKFLOWS = [
    EtsyPublishWorkflow,
    EtsyUpdateWorkflow,
    EtsyDeleteWorkflow,
]

__all__ = [
    "EtsyPublishWorkflow",
    "EtsyPublishParams",
    "EtsyUpdateWorkflow",
    "EtsyUpdateParams",
    "EtsyDeleteWorkflow",
    "EtsyDeleteParams",
    "ETSY_ACTION_WORKFLOWS",
]
