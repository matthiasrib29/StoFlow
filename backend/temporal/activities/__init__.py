"""
Temporal activities for StoFlow.
"""

from temporal.activities.ebay_activities import (
    fetch_and_sync_page,
    cleanup_orphan_products,
    update_job_progress,
    mark_job_completed,
    mark_job_failed,
    enrich_single_product,
    get_skus_to_enrich,
    EBAY_ACTIVITIES,
)

from temporal.activities.vinted_activities import (
    fetch_and_sync_page as vinted_fetch_and_sync_page,
    get_vinted_ids_to_enrich,
    enrich_single_product as vinted_enrich_single_product,
    update_job_progress as vinted_update_job_progress,
    mark_job_completed as vinted_mark_job_completed,
    mark_job_failed as vinted_mark_job_failed,
    VINTED_ACTIVITIES,
)

__all__ = [
    # eBay activities
    "EBAY_ACTIVITIES",
    "fetch_and_sync_page",
    "cleanup_orphan_products",
    "update_job_progress",
    "mark_job_completed",
    "mark_job_failed",
    "enrich_single_product",
    "get_skus_to_enrich",
    # Vinted activities
    "VINTED_ACTIVITIES",
    "vinted_fetch_and_sync_page",
    "get_vinted_ids_to_enrich",
    "vinted_enrich_single_product",
    "vinted_update_job_progress",
    "vinted_mark_job_completed",
    "vinted_mark_job_failed",
]
