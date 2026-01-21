"""
Marketplace services for multi-platform job orchestration.

This package contains services for managing batch operations
across multiple marketplaces (Vinted, eBay, Etsy).

Updated: 2026-01-09 - Added MarketplaceJobProcessor for unified job execution
Updated: 2026-01-20 - Renamed BatchJobService → MarketplaceBatchService
"""

from .marketplace_batch_service import MarketplaceBatchService, BatchJobService
from .marketplace_job_service import MarketplaceJobService
from .marketplace_job_processor import MarketplaceJobProcessor

__all__ = [
    "MarketplaceBatchService",
    "BatchJobService",  # Deprecated alias for backward compatibility
    "MarketplaceJobService",
    "MarketplaceJobProcessor",
]
