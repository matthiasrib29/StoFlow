"""
Temporal activities for StoFlow.
"""

# ── Sync activities (existing) ──────────────────────────────────

from temporal.activities.ebay_activities import (
    fetch_and_sync_page,
    get_skus_to_delete,
    delete_single_product,
    sync_sold_status,
    get_skus_sold_elsewhere,
    enrich_single_product,
    get_skus_to_enrich,
    detect_ebay_sold_elsewhere,
    delete_ebay_listing,
    apply_policy_to_single_offer,
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
    check_plugin_connection as vinted_check_plugin_connection,
)

from temporal.activities.vinted_sync_reconciliation_activities import (
    sync_sold_status as vinted_sync_sold_status,
    detect_sold_with_active_listing,
    delete_vinted_listing,
)

# ── Action activities (new — MarketplaceJob replacement) ────────

from temporal.activities.vinted_action_activities import (
    vinted_publish_product,
    vinted_update_product,
    vinted_delete_product,
    vinted_sync_orders,
    vinted_send_message,
    vinted_link_product,
    vinted_fetch_users_page,
    vinted_save_prospects_batch,
    vinted_check_connection,
    VINTED_ACTION_ACTIVITIES,
)

from temporal.activities.ebay_action_activities import (
    ebay_publish_product,
    ebay_update_product,
    ebay_delete_product,
    ebay_sync_orders,
    ebay_import_inventory_page,
    ebay_enrich_products_batch,
    ebay_cleanup_orphan_imports,
    EBAY_ACTION_ACTIVITIES,
)

from temporal.activities.etsy_action_activities import (
    etsy_publish_product,
    etsy_update_product,
    etsy_delete_product,
    ETSY_ACTION_ACTIVITIES,
)

__all__ = [
    # eBay sync activities
    "EBAY_ACTIVITIES",
    "fetch_and_sync_page",
    "get_skus_to_delete",
    "delete_single_product",
    "sync_sold_status",
    "get_skus_sold_elsewhere",
    "enrich_single_product",
    "get_skus_to_enrich",
    "detect_ebay_sold_elsewhere",
    "delete_ebay_listing",
    "apply_policy_to_single_offer",
    # Vinted sync activities
    "VINTED_ACTIVITIES",
    "vinted_fetch_and_sync_page",
    "get_vinted_ids_to_enrich",
    "vinted_enrich_single_product",
    "vinted_check_plugin_connection",
    "vinted_sync_sold_status",
    "detect_sold_with_active_listing",
    "delete_vinted_listing",
    "scan_pro_sellers_page",
    "save_pro_sellers_batch",
    "get_keyword_scan_logs",
    "update_keyword_scan_log",
    # Vinted action activities
    "VINTED_ACTION_ACTIVITIES",
    "vinted_publish_product",
    "vinted_update_product",
    "vinted_delete_product",
    "vinted_sync_orders",
    "vinted_send_message",
    "vinted_link_product",
    "vinted_fetch_users_page",
    "vinted_save_prospects_batch",
    "vinted_check_connection",
    # eBay action activities
    "EBAY_ACTION_ACTIVITIES",
    "ebay_publish_product",
    "ebay_update_product",
    "ebay_delete_product",
    "ebay_sync_orders",
    "ebay_import_inventory_page",
    "ebay_enrich_products_batch",
    "ebay_cleanup_orphan_imports",
    # Etsy action activities
    "ETSY_ACTION_ACTIVITIES",
    "etsy_publish_product",
    "etsy_update_product",
    "etsy_delete_product",
]
