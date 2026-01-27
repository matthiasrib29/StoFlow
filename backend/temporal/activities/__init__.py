"""
Temporal activities for StoFlow.
"""

from temporal.activities.ebay_activities import (
    fetch_and_sync_page,
    get_skus_to_delete,
    delete_single_product,
    sync_sold_status,
    get_skus_sold_elsewhere,
    update_job_progress,
    mark_job_completed,
    mark_job_failed,
    enrich_single_product,
    get_skus_to_enrich,
    detect_ebay_sold_elsewhere,
    delete_ebay_listing,
    EBAY_ACTIVITIES,
)

from temporal.activities.vinted_activities import (
    fetch_and_sync_page as vinted_fetch_and_sync_page,
    get_vinted_ids_to_enrich,
    enrich_single_product as vinted_enrich_single_product,
    scan_pro_sellers_page,
    save_pro_sellers_batch,
    get_keyword_scan_logs,
    update_keyword_scan_log,
    VINTED_ACTIVITIES,
)

from temporal.activities.job_state_activities import (
    update_job_progress as vinted_update_job_progress,
    mark_job_completed as vinted_mark_job_completed,
    mark_job_failed as vinted_mark_job_failed,
    check_plugin_connection as vinted_check_plugin_connection,
    mark_job_paused as vinted_mark_job_paused,
)

from temporal.activities.vinted_sync_reconciliation_activities import (
    sync_sold_status as vinted_sync_sold_status,
    detect_sold_with_active_listing,
    delete_vinted_listing,
)

__all__ = [
    # eBay activities
    "EBAY_ACTIVITIES",
    "fetch_and_sync_page",
    "get_skus_to_delete",
    "delete_single_product",
    "sync_sold_status",
    "get_skus_sold_elsewhere",
    "update_job_progress",
    "mark_job_completed",
    "mark_job_failed",
    "enrich_single_product",
    "get_skus_to_enrich",
    "detect_ebay_sold_elsewhere",
    "delete_ebay_listing",
    # Vinted activities
    "VINTED_ACTIVITIES",
    "vinted_fetch_and_sync_page",
    "get_vinted_ids_to_enrich",
    "vinted_enrich_single_product",
    "vinted_update_job_progress",
    "vinted_mark_job_completed",
    "vinted_mark_job_failed",
    "vinted_check_plugin_connection",
    "vinted_mark_job_paused",
    "vinted_sync_sold_status",
    "detect_sold_with_active_listing",
    "delete_vinted_listing",
    "scan_pro_sellers_page",
    "save_pro_sellers_batch",
    "get_keyword_scan_logs",
    "update_keyword_scan_log",
]
