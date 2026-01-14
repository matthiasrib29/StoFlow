"""
AI Credit Pack Service

Service for AI credit pack operations with in-memory caching.

Architecture:
- Service layer orchestrating repository
- In-memory cache with TTL (5 minutes)
- Thread-safe cache refresh
- Graceful error handling

Created: 2026-01-14
Author: Claude
"""

import threading
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from models.public.ai_credit_pack import AiCreditPack
from repositories.ai_credit_pack_repository import AiCreditPackRepository
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class AiCreditPackService:
    """
    Service for AI credit pack operations.

    Features:
    - In-memory cache with TTL (5 minutes)
    - Thread-safe cache refresh
    - Graceful error handling on cache refresh

    Cache strategy:
    - Cache all active packs in memory (typically 3-5 packs = ~1 KB)
    - Refresh every 5 minutes (acceptable for pricing changes)
    - Thread-safe refresh with double-check pattern
    - Keep stale cache on error (graceful degradation)
    """

    CACHE_TTL_SECONDS = 300  # 5 minutes

    def __init__(self, db: Session, repository: AiCreditPackRepository):
        """
        Initialize AiCreditPackService with dependencies.

        Args:
            db: Database session
            repository: AiCreditPack repository
        """
        self.db = db
        self.repository = repository
        self._cache: Dict[int, AiCreditPack] = {}
        self._cache_timestamp: Optional[datetime] = None
        self._lock = threading.Lock()

    def get_pack_by_credits(self, credits: int) -> Optional[AiCreditPack]:
        """
        Get pack by credits count with caching.

        Cache strategy:
        - First call: queries DB and caches all active packs
        - Subsequent calls: return from cache (no DB query)
        - Cache refreshes every 5 minutes

        Args:
            credits: Number of credits (e.g., 25, 75, 200)

        Returns:
            AiCreditPack if found and active, None otherwise
        """
        if self._is_cache_expired():
            self._refresh_cache()

        return self._cache.get(credits)

    def get_pack_by_id(self, pack_id: int) -> Optional[AiCreditPack]:
        """
        Get pack by ID (bypasses cache, always queries DB).

        Use this when you need the most up-to-date data or when
        working with admin operations that might modify packs.

        Args:
            pack_id: Pack primary key ID

        Returns:
            AiCreditPack if found, None otherwise
        """
        return self.repository.get_by_id(self.db, pack_id)

    def list_active_packs(self) -> List[AiCreditPack]:
        """
        List all active packs (uses same cache as get_pack_by_credits).

        Returns:
            List of active AiCreditPack ordered by display_order
        """
        if self._is_cache_expired():
            self._refresh_cache()

        return sorted(self._cache.values(), key=lambda p: p.display_order)

    def invalidate_cache(self) -> None:
        """
        Manually invalidate the cache.

        Use this after creating/updating/deleting packs to force
        immediate cache refresh on next access.
        """
        with self._lock:
            self._cache_timestamp = None
            logger.info("[AiCreditPackService] Cache manually invalidated")

    def _is_cache_expired(self) -> bool:
        """
        Check if cache needs refresh.

        Returns:
            True if cache is expired or not initialized
        """
        if self._cache_timestamp is None:
            return True

        age_seconds = (
            datetime.now(timezone.utc) - self._cache_timestamp
        ).total_seconds()
        return age_seconds > self.CACHE_TTL_SECONDS

    def _refresh_cache(self) -> None:
        """
        Refresh cache from database (thread-safe).

        Uses double-check locking pattern:
        1. Check expiration without lock (fast path)
        2. Acquire lock
        3. Re-check expiration (another thread may have refreshed)
        4. Refresh cache

        On error: Keep stale cache (graceful degradation)
        """
        with self._lock:
            # Double-check after acquiring lock
            if not self._is_cache_expired():
                return

            try:
                packs = self.repository.list_active(self.db)
                self._cache = {pack.credits: pack for pack in packs}
                self._cache_timestamp = datetime.now(timezone.utc)

                logger.info(
                    f"[AiCreditPackService] Cache refreshed: {len(self._cache)} packs loaded"
                )
            except Exception as e:
                logger.error(
                    f"[AiCreditPackService] Cache refresh failed: {e}", exc_info=True
                )
                # Keep stale cache on error (graceful degradation)
                # If cache was never initialized, set empty cache to prevent retry storm
                if self._cache_timestamp is None:
                    self._cache = {}
                    self._cache_timestamp = datetime.now(timezone.utc)
