"""
eBay Import Workflow — imports products from eBay inventory.

Complex workflow with:
- Pagination through inventory pages
- Parallel enrichment in batches
- Cooperative cancellation
- Progress tracking
- Orphan cleanup after import
"""

import asyncio
from dataclasses import dataclass
from datetime import timedelta
from typing import Optional

from temporalio import workflow
from temporalio.common import RetryPolicy

from temporal.activities.ebay_action_activities import (
    ebay_import_inventory_page,
    ebay_enrich_products_batch,
    ebay_cleanup_orphan_imports,
)

IMPORT_PAGE_SIZE = 100
ENRICHMENT_BATCH_SIZE = 30


@dataclass
class EbayImportParams:
    """Parameters for eBay import workflow."""

    user_id: int
    marketplace_id: str = "EBAY_FR"

    # Continue-as-new support
    start_offset: int = 0
    accumulated_imported: int = 0
    accumulated_enriched: int = 0
    accumulated_errors: int = 0


@dataclass
class ImportProgress:
    """Progress tracking for import workflow."""

    status: str = "initializing"
    phase: str = "import"  # import, enrich, cleanup
    current_offset: int = 0
    total_items: int = 0
    imported: int = 0
    enriched: int = 0
    errors: int = 0
    label: str = "initialisation..."
    error: Optional[str] = None


@workflow.defn
class EbayImportWorkflow:
    """
    Import products from eBay inventory with parallel enrichment.

    Flow:
    1. Paginate through eBay inventory (100 items per page)
    2. Import each page without enrichment (fast)
    3. Enrich imported SKUs in batches (parallel offer fetching)
    4. Cleanup orphan products (no listing_id)
    """

    def __init__(self):
        self._progress = ImportProgress()
        self._cancelled = False

    @workflow.run
    async def run(self, params: EbayImportParams) -> dict:
        self._progress = ImportProgress(
            status="running",
            phase="import",
            imported=params.accumulated_imported,
            enriched=params.accumulated_enriched,
            errors=params.accumulated_errors,
            current_offset=params.start_offset,
        )

        import_options = {
            "start_to_close_timeout": timedelta(minutes=5),
            "retry_policy": RetryPolicy(
                initial_interval=timedelta(seconds=2),
                maximum_interval=timedelta(seconds=60),
                maximum_attempts=3,
            ),
        }

        enrich_options = {
            "start_to_close_timeout": timedelta(minutes=10),
            "retry_policy": RetryPolicy(
                initial_interval=timedelta(seconds=2),
                maximum_interval=timedelta(seconds=60),
                maximum_attempts=3,
            ),
        }

        cleanup_options = {
            "start_to_close_timeout": timedelta(minutes=2),
            "retry_policy": RetryPolicy(
                initial_interval=timedelta(seconds=1),
                maximum_interval=timedelta(seconds=10),
                maximum_attempts=3,
            ),
        }

        try:
            offset = params.start_offset
            all_skus = []

            # Phase 1: Import inventory pages
            while True:
                if self._cancelled:
                    self._progress.status = "cancelled"
                    return self._build_result("cancelled")

                self._progress.current_offset = offset
                self._progress.label = f"Import page {offset // IMPORT_PAGE_SIZE + 1}..."

                # Fetch and import one page
                page_result = await workflow.execute_activity(
                    ebay_import_inventory_page,
                    args=[
                        params.user_id,
                        params.marketplace_id,
                        IMPORT_PAGE_SIZE,
                        offset,
                    ],
                    **import_options,
                )

                self._progress.imported += page_result.get("imported", 0) + page_result.get("updated", 0)
                self._progress.errors += page_result.get("errors", 0)
                self._progress.total_items = page_result.get("total", 0)

                # Collect SKUs for enrichment
                page_skus = page_result.get("skus", [])
                all_skus.extend(page_skus)

                # Enrich in batches as we go
                while len(all_skus) >= ENRICHMENT_BATCH_SIZE:
                    if self._cancelled:
                        self._progress.status = "cancelled"
                        return self._build_result("cancelled")

                    batch = all_skus[:ENRICHMENT_BATCH_SIZE]
                    all_skus = all_skus[ENRICHMENT_BATCH_SIZE:]

                    self._progress.phase = "enrich"
                    self._progress.label = f"Enrichissement... ({self._progress.enriched} produits)"

                    enrich_result = await workflow.execute_activity(
                        ebay_enrich_products_batch,
                        args=[params.user_id, params.marketplace_id, batch],
                        **enrich_options,
                    )

                    self._progress.enriched += enrich_result.get("enriched", 0)
                    self._progress.errors += enrich_result.get("errors", 0)
                    self._progress.phase = "import"

                # Check if more pages
                if not page_result.get("has_more", False):
                    break

                offset += IMPORT_PAGE_SIZE

            # Enrich remaining SKUs
            if all_skus and not self._cancelled:
                self._progress.phase = "enrich"
                self._progress.label = f"Enrichissement final... ({len(all_skus)} restants)"

                enrich_result = await workflow.execute_activity(
                    ebay_enrich_products_batch,
                    args=[params.user_id, params.marketplace_id, all_skus],
                    **enrich_options,
                )
                self._progress.enriched += enrich_result.get("enriched", 0)
                self._progress.errors += enrich_result.get("errors", 0)

            # Phase 3: Cleanup orphan products
            if not self._cancelled:
                self._progress.phase = "cleanup"
                self._progress.label = "Nettoyage..."

                cleanup_result = await workflow.execute_activity(
                    ebay_cleanup_orphan_imports,
                    args=[params.user_id],
                    **cleanup_options,
                )

                deleted = cleanup_result.get("deleted", 0)
                if deleted > 0:
                    workflow.logger.info(f"Cleaned up {deleted} orphan products")

            self._progress.status = "completed"
            self._progress.label = f"{self._progress.enriched} produits importés"
            return self._build_result("completed")

        except Exception as e:
            self._progress.status = "failed"
            self._progress.error = str(e)
            raise

    def _build_result(self, status: str) -> dict:
        return {
            "status": status,
            "imported": self._progress.imported,
            "enriched": self._progress.enriched,
            "errors": self._progress.errors,
            "total_items": self._progress.total_items,
            "error": self._progress.error,
        }

    # ═══════════════════════════════════════════════════════════════
    # SIGNALS
    # ═══════════════════════════════════════════════════════════════

    @workflow.signal
    def cancel(self) -> None:
        self._cancelled = True
        self._progress.status = "cancelling"
        workflow.logger.info("Import cancelled by signal")

    # ═══════════════════════════════════════════════════════════════
    # QUERIES
    # ═══════════════════════════════════════════════════════════════

    @workflow.query
    def get_progress(self) -> dict:
        return {
            "status": self._progress.status,
            "phase": self._progress.phase,
            "current": self._progress.enriched,
            "total": self._progress.total_items,
            "imported": self._progress.imported,
            "enriched": self._progress.enriched,
            "errors": self._progress.errors,
            "label": self._progress.label,
            "error": self._progress.error,
        }
