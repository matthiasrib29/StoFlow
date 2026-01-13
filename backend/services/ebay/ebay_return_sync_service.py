"""
eBay Return Sync Service

Service to synchronize eBay returns from the Post-Order API to local database.
Responsibility: Orchestrate fetch, mapping, and create/update of returns.

Architecture:
- Fetch returns via EbayReturnClient
- Map API data → DB models
- Create or update via EbayReturnRepository
- Handle pagination and errors gracefully
- Return detailed statistics

Created: 2026-01-13
Author: Claude
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from models.user.ebay_return import EbayReturn
from repositories.ebay_return_repository import EbayReturnRepository
from services.ebay.ebay_return_client import EbayReturnClient
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class EbayReturnSyncService:
    """
    Service to sync eBay returns to local database.

    Workflow:
    1. Calculate date range (now - N days)
    2. Fetch returns from eBay Post-Order API
    3. For each return: check if exists, map data, create or update
    4. Return statistics (created, updated, errors)

    Usage:
        >>> service = EbayReturnSyncService(db_session, user_id=1)
        >>> stats = service.sync_returns(days_back=30)
        >>> print(f"Created: {stats['created']}, Updated: {stats['updated']}")
    """

    def __init__(self, db: Session, user_id: int):
        """
        Initialize sync service.

        Args:
            db: SQLAlchemy Session (with search_path already set)
            user_id: User ID for eBay authentication
        """
        self.db = db
        self.user_id = user_id
        self.return_client = EbayReturnClient(db, user_id)

        logger.info(f"[EbayReturnSyncService] Initialized for user_id={user_id}")

    def sync_returns(
        self,
        return_state: Optional[str] = None,
        days_back: int = 30,
    ) -> Dict[str, Any]:
        """
        Sync returns from eBay to local database.

        Args:
            return_state: Optional filter by state (OPEN, CLOSED)
            days_back: Number of days to look back (default 30, max 120)

        Returns:
            Statistics dict:
            {
                "created": int,        # New returns created
                "updated": int,        # Existing returns updated
                "skipped": int,        # Returns skipped (unchanged)
                "errors": int,         # Number of errors
                "total_fetched": int,  # Total returns fetched from eBay
                "details": [           # Per-return details
                    {
                        "return_id": str,
                        "action": "created|updated|skipped|error",
                        "error": str (if action == "error")
                    }
                ]
            }

        Raises:
            ValueError: If days_back out of range
        """
        start_time = datetime.now(timezone.utc)

        # Validate parameters
        if not (1 <= days_back <= 120):
            raise ValueError("days_back must be between 1 and 120")

        logger.info(
            f"[EbayReturnSyncService] Starting sync: user_id={self.user_id}, "
            f"days_back={days_back}, return_state={return_state}"
        )

        try:
            # Fetch returns from eBay API
            api_returns = self._fetch_returns_from_ebay(return_state, days_back)

            logger.info(
                f"[EbayReturnSyncService] Fetched {len(api_returns)} returns from eBay"
            )

            # Process returns batch
            stats = self._process_returns_batch(api_returns)
            stats["total_fetched"] = len(api_returns)

            # Commit and log summary
            self._finalize_sync(start_time, stats)

        except Exception as e:
            self.db.rollback()
            logger.error(
                f"[EbayReturnSyncService] Sync failed for user {self.user_id}: {e}",
                exc_info=True,
            )
            raise

        return stats

    def sync_open_returns(self) -> Dict[str, Any]:
        """
        Convenience method to sync only open returns.

        Returns:
            Statistics dict
        """
        return self.sync_returns(return_state="OPEN", days_back=90)

    def _fetch_returns_from_ebay(
        self,
        return_state: Optional[str],
        days_back: int,
    ) -> List[Dict[str, Any]]:
        """
        Fetch returns from eBay API with date range.

        Args:
            return_state: Optional state filter
            days_back: Days to look back

        Returns:
            List of return dicts from eBay API
        """
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days_back)

        logger.debug(
            f"[EbayReturnSyncService] Fetching returns from {start_date.isoformat()} "
            f"to {end_date.isoformat()}"
        )

        return self.return_client.get_returns_by_date_range(
            start_date=start_date,
            end_date=end_date,
            return_state=return_state,
        )

    def _process_returns_batch(self, api_returns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process batch of returns and collect statistics.

        Args:
            api_returns: List of returns from eBay API

        Returns:
            Statistics dict with created/updated/skipped/errors counts
        """
        stats = {
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0,
            "details": [],
        }

        for idx, api_return in enumerate(api_returns, start=1):
            return_id = api_return.get("returnId", "unknown")

            try:
                result = self._process_single_return(api_return)

                # Update stats
                action = result.get("action", "error")
                if action == "created":
                    stats["created"] += 1
                elif action == "updated":
                    stats["updated"] += 1
                elif action == "skipped":
                    stats["skipped"] += 1

                stats["details"].append(result)

                # Log progress every 20 returns
                if idx % 20 == 0:
                    logger.info(
                        f"[EbayReturnSyncService] Progress: {idx}/{len(api_returns)} "
                        f"returns processed"
                    )

            except Exception as e:
                stats["errors"] += 1
                error_msg = str(e)

                logger.error(
                    f"[EbayReturnSyncService] Error processing return {return_id}: {e}",
                    exc_info=True,
                )

                stats["details"].append({
                    "return_id": return_id,
                    "action": "error",
                    "error": error_msg,
                })

        return stats

    def _process_single_return(self, api_return: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single return from eBay API.

        Args:
            api_return: Return dict from eBay Post-Order API

        Returns:
            Result dict: {"return_id": str, "action": "created|updated|skipped"}

        Raises:
            Exception: If processing fails
        """
        return_id = api_return.get("returnId")

        if not return_id:
            raise ValueError("Return missing returnId field")

        logger.debug(f"[EbayReturnSyncService] Processing return: {return_id}")

        # Check if return already exists
        existing_return = EbayReturnRepository.get_by_ebay_return_id(self.db, return_id)

        # Map API data to model fields
        return_data = self._map_api_return_to_model(api_return)

        if existing_return:
            # Update existing return
            for key, value in return_data.items():
                setattr(existing_return, key, value)

            existing_return.updated_at = datetime.now(timezone.utc)

            EbayReturnRepository.update(self.db, existing_return)
            action = "updated"

        else:
            # Create new return
            new_return = EbayReturn(**return_data)
            EbayReturnRepository.create(self.db, new_return)
            action = "created"

        logger.debug(
            f"[EbayReturnSyncService] Return {return_id} {action} successfully"
        )

        return {"return_id": return_id, "action": action}

    def _map_api_return_to_model(self, api_return: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map eBay API return data to EbayReturn model fields.

        Args:
            api_return: Return dict from eBay Post-Order API

        Returns:
            Dict of fields for EbayReturn constructor
        """
        # Extract refund info
        refund_amount_data = api_return.get("refundAmount", {})
        refund_amount = self._parse_float(refund_amount_data.get("value"))
        refund_currency = refund_amount_data.get("currency")

        # Extract buyer info
        buyer = api_return.get("buyer", {})
        buyer_username = buyer.get("username")

        # Extract dates
        creation_date = self._parse_date(api_return.get("creationDate"))
        closed_date = self._parse_date(api_return.get("closedDate"))

        # Extract deadline from sellerResponseDue
        seller_response_due = api_return.get("sellerResponseDue", {})
        deadline_date = self._parse_date(seller_response_due.get("deadline"))

        # Extract tracking info
        return_shipment = api_return.get("returnShipment", {})
        shipment_tracking = return_shipment.get("shipmentTracking", {})
        tracking_number = shipment_tracking.get("trackingNumber")
        carrier = shipment_tracking.get("carrier")

        # Build return data
        return_data = {
            "return_id": api_return.get("returnId"),
            "order_id": api_return.get("orderId"),
            "state": api_return.get("state"),
            "status": api_return.get("status"),
            "return_type": api_return.get("returnType"),
            "reason": api_return.get("returnReason"),
            "reason_detail": api_return.get("returnReasonDescription"),
            "refund_amount": refund_amount,
            "refund_currency": refund_currency,
            "refund_status": api_return.get("refundStatus"),
            "buyer_username": buyer_username,
            "buyer_comments": api_return.get("buyerComments"),
            "seller_comments": api_return.get("sellerComments"),
            "rma_number": api_return.get("RMANumber"),
            "return_tracking_number": tracking_number,
            "return_carrier": carrier,
            "creation_date": creation_date,
            "deadline_date": deadline_date,
            "closed_date": closed_date,
            "raw_data": api_return,
        }

        return return_data

    def _finalize_sync(self, start_time: datetime, stats: Dict[str, Any]) -> None:
        """
        Commit transaction and log summary.

        Args:
            start_time: Sync start timestamp
            stats: Statistics dict
        """
        self.db.commit()

        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()

        logger.info(
            f"[EbayReturnSyncService] Sync completed: user_id={self.user_id}, "
            f"created={stats['created']}, updated={stats['updated']}, "
            f"skipped={stats['skipped']}, errors={stats['errors']}, "
            f"total_fetched={stats['total_fetched']}, duration={elapsed:.2f}s"
        )

    # =========================================================================
    # Helper Methods
    # =========================================================================

    @staticmethod
    def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
        """
        Parse ISO 8601 date string to datetime.

        Args:
            date_str: ISO 8601 date string (e.g., "2026-01-13T10:30:00.000Z")

        Returns:
            Datetime object or None
        """
        if not date_str:
            return None

        try:
            # Parse ISO 8601 format
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            logger.warning(
                f"[EbayReturnSyncService] Failed to parse date: {date_str}"
            )
            return None

    @staticmethod
    def _parse_float(value_str: Optional[str]) -> Optional[float]:
        """
        Parse string value to float.

        Args:
            value_str: String representation of float (e.g., "50.00")

        Returns:
            Float value or None
        """
        if not value_str:
            return None

        try:
            return float(value_str)
        except (ValueError, TypeError):
            logger.warning(
                f"[EbayReturnSyncService] Failed to parse float: {value_str}"
            )
            return None
