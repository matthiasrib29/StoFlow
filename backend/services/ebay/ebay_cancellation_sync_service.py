"""
eBay Cancellation Sync Service

Service to synchronize eBay cancellations from the Post-Order API to local database.
Responsibility: Orchestrate fetch, mapping, and create/update of cancellations.

Architecture:
- Fetch cancellations via EbayCancellationClient
- Map API data → DB models
- Create or update via EbayCancellationRepository
- Handle pagination and errors gracefully
- Return detailed statistics

Created: 2026-01-14
Author: Claude
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from models.user.ebay_cancellation import EbayCancellation
from repositories.ebay_cancellation_repository import EbayCancellationRepository
from services.ebay.ebay_cancellation_client import EbayCancellationClient
from shared.logging import get_logger

logger = get_logger(__name__)


class EbayCancellationSyncService:
    """
    Service to sync eBay cancellations to local database.

    Workflow:
    1. Calculate date range (now - N days)
    2. Fetch cancellations from eBay Post-Order API
    3. For each cancellation: check if exists, map data, create or update
    4. Return statistics (created, updated, errors)

    Usage:
        >>> service = EbayCancellationSyncService(db_session, user_id=1)
        >>> stats = service.sync_cancellations(days_back=30)
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
        self.cancellation_client = EbayCancellationClient(db, user_id)

        logger.info(f"[EbayCancellationSyncService] Initialized for user_id={user_id}")

    def sync_cancellations(
        self,
        cancel_state: Optional[str] = None,
        days_back: int = 30,
    ) -> Dict[str, Any]:
        """
        Sync cancellations from eBay to local database.

        Args:
            cancel_state: Optional filter by state (currently only CLOSED)
            days_back: Number of days to look back (default 30, max 120)

        Returns:
            Statistics dict:
            {
                "created": int,        # New cancellations created
                "updated": int,        # Existing cancellations updated
                "skipped": int,        # Cancellations skipped (unchanged)
                "errors": int,         # Number of errors
                "total_fetched": int,  # Total cancellations fetched from eBay
                "details": [           # Per-cancellation details
                    {
                        "cancel_id": str,
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
            f"[EbayCancellationSyncService] Starting sync: user_id={self.user_id}, "
            f"days_back={days_back}, cancel_state={cancel_state}"
        )

        try:
            # Fetch cancellations from eBay API
            api_cancellations = self._fetch_cancellations_from_ebay(
                cancel_state, days_back
            )

            logger.info(
                f"[EbayCancellationSyncService] Fetched {len(api_cancellations)} "
                f"cancellations from eBay"
            )

            # Process cancellations batch
            stats = self._process_cancellations_batch(api_cancellations)
            stats["total_fetched"] = len(api_cancellations)

            # Commit and log summary
            self._finalize_sync(start_time, stats)

        except Exception as e:
            self.db.rollback()
            logger.error(
                f"[EbayCancellationSyncService] Sync failed for user {self.user_id}: {e}",
                exc_info=True,
            )
            raise

        return stats

    def sync_pending_cancellations(self) -> Dict[str, Any]:
        """
        Convenience method to sync and identify pending cancellations.

        Returns:
            Statistics dict
        """
        return self.sync_cancellations(days_back=30)

    def _fetch_cancellations_from_ebay(
        self,
        cancel_state: Optional[str],
        days_back: int,
    ) -> List[Dict[str, Any]]:
        """
        Fetch cancellations from eBay API with date range.

        Args:
            cancel_state: Optional state filter
            days_back: Days to look back

        Returns:
            List of cancellation dicts from eBay API
        """
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days_back)

        logger.debug(
            f"[EbayCancellationSyncService] Fetching cancellations from "
            f"{start_date.isoformat()} to {end_date.isoformat()}"
        )

        return self.cancellation_client.get_cancellations_by_date_range(
            start_date=start_date,
            end_date=end_date,
            cancel_state=cancel_state,
        )

    def _process_cancellations_batch(
        self, api_cancellations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Process batch of cancellations and collect statistics.

        Args:
            api_cancellations: List of cancellations from eBay API

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

        for idx, api_cancel in enumerate(api_cancellations, start=1):
            cancel_id = api_cancel.get("cancelId", "unknown")

            try:
                result = self._process_single_cancellation(api_cancel)

                # Update stats
                action = result.get("action", "error")
                if action == "created":
                    stats["created"] += 1
                elif action == "updated":
                    stats["updated"] += 1
                elif action == "skipped":
                    stats["skipped"] += 1

                stats["details"].append(result)

                # Log progress every 20 cancellations
                if idx % 20 == 0:
                    logger.info(
                        f"[EbayCancellationSyncService] Progress: {idx}/{len(api_cancellations)} "
                        f"cancellations processed"
                    )

            except Exception as e:
                stats["errors"] += 1
                error_msg = str(e)

                logger.error(
                    f"[EbayCancellationSyncService] Error processing cancellation "
                    f"{cancel_id}: {e}",
                    exc_info=True,
                )

                stats["details"].append({
                    "cancel_id": cancel_id,
                    "action": "error",
                    "error": error_msg,
                })

        return stats

    def _process_single_cancellation(
        self, api_cancel: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a single cancellation from eBay API.

        Args:
            api_cancel: Cancellation dict from eBay Post-Order API

        Returns:
            Result dict: {"cancel_id": str, "action": "created|updated|skipped"}

        Raises:
            Exception: If processing fails
        """
        cancel_id = api_cancel.get("cancelId")

        if not cancel_id:
            raise ValueError("Cancellation missing cancelId field")

        logger.debug(f"[EbayCancellationSyncService] Processing cancellation: {cancel_id}")

        # Check if cancellation already exists
        existing_cancel = EbayCancellationRepository.get_by_cancel_id(
            self.db, cancel_id
        )

        # Map API data to model fields
        cancel_data = self._map_api_cancel_to_model(api_cancel)

        if existing_cancel:
            # Update existing cancellation
            for key, value in cancel_data.items():
                setattr(existing_cancel, key, value)

            existing_cancel.updated_at = datetime.now(timezone.utc)

            EbayCancellationRepository.update(self.db, existing_cancel)
            action = "updated"

        else:
            # Create new cancellation
            new_cancel = EbayCancellation(**cancel_data)
            EbayCancellationRepository.create(self.db, new_cancel)
            action = "created"

        logger.debug(
            f"[EbayCancellationSyncService] Cancellation {cancel_id} {action} successfully"
        )

        return {"cancel_id": cancel_id, "action": action}

    def _map_api_cancel_to_model(self, api_cancel: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map eBay API cancellation data to EbayCancellation model fields.

        Args:
            api_cancel: Cancellation dict from eBay Post-Order API

        Returns:
            Dict of fields for EbayCancellation constructor
        """
        # Extract refund info
        refund_info = api_cancel.get("refundInfo", {})
        refund_amount_data = refund_info.get("refundAmount", {})
        refund_amount = self._parse_float(refund_amount_data.get("value"))
        refund_currency = refund_amount_data.get("currency")
        refund_status = refund_info.get("refundStatus")

        # Extract buyer info
        buyer_info = api_cancel.get("buyer", {})
        buyer_username = buyer_info.get("username")

        # Extract seller response info
        seller_response = api_cancel.get("sellerResponse", {})
        seller_comments = seller_response.get("responseText")
        reject_reason = seller_response.get("rejectReason")

        # Extract shipping info (from rejection response)
        shipment_info = seller_response.get("shipmentInfo", {})
        tracking_number = shipment_info.get("trackingNumber")
        carrier = shipment_info.get("carrier")
        shipped_date = self._parse_date(shipment_info.get("shipmentDate"))

        # Extract dates
        creation_date = self._parse_date(api_cancel.get("creationDate"))
        closed_date = self._parse_date(api_cancel.get("closedDate"))
        request_date = self._parse_date(api_cancel.get("requestDate"))
        response_due_date = self._parse_date(api_cancel.get("responseDueDate"))

        # Extract buyer comments
        buyer_request = api_cancel.get("buyerRequest", {})
        buyer_comments = buyer_request.get("requestText")

        # Build cancellation data
        cancel_data = {
            "cancel_id": api_cancel.get("cancelId"),
            "order_id": api_cancel.get("legacyOrderId"),
            "cancel_state": api_cancel.get("cancelState"),
            "cancel_status": api_cancel.get("cancelStatus"),
            "cancel_reason": api_cancel.get("cancelReason"),
            "requestor_role": api_cancel.get("requestorRole"),
            "request_date": request_date,
            "response_due_date": response_due_date,
            "refund_amount": refund_amount,
            "refund_currency": refund_currency,
            "refund_status": refund_status,
            "buyer_username": buyer_username,
            "buyer_comments": buyer_comments,
            "seller_comments": seller_comments,
            "reject_reason": reject_reason,
            "tracking_number": tracking_number,
            "carrier": carrier,
            "shipped_date": shipped_date,
            "creation_date": creation_date,
            "closed_date": closed_date,
            "raw_data": api_cancel,
        }

        return cancel_data

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
            f"[EbayCancellationSyncService] Sync completed: user_id={self.user_id}, "
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
                f"[EbayCancellationSyncService] Failed to parse date: {date_str}"
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
                f"[EbayCancellationSyncService] Failed to parse float: {value_str}"
            )
            return None
