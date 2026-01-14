"""
eBay Cancellation Service

Service for eBay cancellation business operations.
Responsibility: Business logic for cancellation management (read, actions, statistics).

Architecture:
- Read operations via EbayCancellationRepository
- Action operations: eBay API call + local DB update
- Statistics aggregation

Created: 2026-01-14
Author: Claude
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from models.user.ebay_cancellation import EbayCancellation
from repositories.ebay_cancellation_repository import EbayCancellationRepository
from services.ebay.ebay_cancellation_client import EbayCancellationClient
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class EbayCancellationService:
    """
    Service for eBay cancellation business operations.

    Provides:
    - Read operations (get, list, filter)
    - Action operations (approve, reject, create)
    - Statistics aggregation

    Usage:
        >>> service = EbayCancellationService(db_session, user_id=1)
        >>> cancels, total = service.list_cancellations()
        >>> service.approve_cancellation(cancel_id=123, comments="Approved")
    """

    def __init__(self, db: Session, user_id: int):
        """
        Initialize cancellation service.

        Args:
            db: SQLAlchemy Session (with search_path already set)
            user_id: User ID for eBay authentication
        """
        self.db = db
        self.user_id = user_id
        self.cancellation_client = EbayCancellationClient(db, user_id)

        logger.info(f"[EbayCancellationService] Initialized for user_id={user_id}")

    # =========================================================================
    # Read Operations
    # =========================================================================

    def get_cancellation(self, cancellation_id: int) -> Optional[EbayCancellation]:
        """
        Get cancellation by internal ID.

        Args:
            cancellation_id: Internal cancellation ID

        Returns:
            EbayCancellation if found, None otherwise
        """
        return EbayCancellationRepository.get_by_id(self.db, cancellation_id)

    def get_cancellation_by_cancel_id(
        self, cancel_id: str
    ) -> Optional[EbayCancellation]:
        """
        Get cancellation by eBay cancel ID.

        Args:
            cancel_id: eBay cancellation ID (e.g., "5000012345")

        Returns:
            EbayCancellation if found, None otherwise
        """
        return EbayCancellationRepository.get_by_cancel_id(self.db, cancel_id)

    def list_cancellations(
        self,
        skip: int = 0,
        limit: int = 50,
        cancel_state: Optional[str] = None,
        cancel_status: Optional[str] = None,
        order_id: Optional[str] = None,
    ) -> Tuple[List[EbayCancellation], int]:
        """
        List cancellations with pagination and filters.

        Args:
            skip: Number of results to skip
            limit: Max number of results
            cancel_state: Filter by state (CLOSED)
            cancel_status: Filter by status
            order_id: Filter by order ID

        Returns:
            Tuple[List[EbayCancellation], int]: (list of cancellations, total count)
        """
        return EbayCancellationRepository.list_cancellations(
            self.db,
            skip=skip,
            limit=limit,
            cancel_state=cancel_state,
            cancel_status=cancel_status,
            order_id=order_id,
        )

    def get_cancellations_needing_action(
        self, limit: int = 100
    ) -> List[EbayCancellation]:
        """
        Get cancellations requiring seller action.

        Returns:
            List of buyer-initiated cancellations pending response
        """
        return EbayCancellationRepository.list_needs_action(self.db, limit)

    def get_cancellations_past_due(self, limit: int = 100) -> List[EbayCancellation]:
        """
        Get cancellations past their response deadline (urgent).

        Returns:
            List of cancellations past deadline
        """
        return EbayCancellationRepository.list_past_response_due(self.db, limit)

    def get_cancellations_for_order(self, order_id: str) -> List[EbayCancellation]:
        """
        Get all cancellations for a specific order.

        Args:
            order_id: eBay order ID

        Returns:
            List of cancellations for the order
        """
        return EbayCancellationRepository.get_by_order_id(self.db, order_id)

    # =========================================================================
    # Action Operations
    # =========================================================================

    def check_eligibility(self, order_id: str) -> Dict[str, Any]:
        """
        Check if an order is eligible for cancellation.

        Args:
            order_id: eBay order ID

        Returns:
            Eligibility result from eBay API
        """
        logger.info(
            f"[EbayCancellationService] check_eligibility: user_id={self.user_id}, "
            f"order_id={order_id}"
        )

        return self.cancellation_client.check_eligibility(order_id)

    def create_cancellation(
        self,
        order_id: str,
        reason: str,
        comments: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a seller-initiated cancellation request.

        Args:
            order_id: eBay order ID
            reason: Cancellation reason code:
                - "OUT_OF_STOCK"
                - "ADDRESS_ISSUES"
                - "BUYER_ASKED_CANCEL"
                - "ORDER_UNPAID"
                - "OTHER_SELLER_CANCEL_REASON"
            comments: Optional comments

        Returns:
            Result dict: {"success": True, "cancel_id": str, "status": str}

        Raises:
            RuntimeError: If API call fails
        """
        logger.info(
            f"[EbayCancellationService] create_cancellation: user_id={self.user_id}, "
            f"order_id={order_id}, reason={reason}"
        )

        try:
            # Call eBay API
            result = self.cancellation_client.create_cancellation(
                order_id=order_id,
                reason=reason,
                comments=comments,
            )

            cancel_id = result.get("cancelId")
            cancel_status = result.get("cancelStatus")

            # Create local record if we got a cancel_id
            if cancel_id:
                new_cancel = EbayCancellation(
                    cancel_id=cancel_id,
                    order_id=order_id,
                    cancel_status=cancel_status,
                    cancel_reason=reason,
                    requestor_role="SELLER",
                    seller_comments=comments,
                    creation_date=datetime.now(timezone.utc),
                    raw_data=result,
                )
                EbayCancellationRepository.create(self.db, new_cancel)
                self.db.commit()

            logger.info(
                f"[EbayCancellationService] Cancellation created: cancel_id={cancel_id}"
            )

            return {
                "success": True,
                "cancel_id": cancel_id,
                "status": cancel_status,
            }

        except Exception as e:
            self.db.rollback()
            logger.error(
                f"[EbayCancellationService] Failed to create cancellation for "
                f"order {order_id}: {e}",
                exc_info=True,
            )
            raise RuntimeError(f"Failed to create cancellation: {str(e)}") from e

    def approve_cancellation(
        self,
        cancellation_id: int,
        comments: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Approve a buyer's cancellation request.

        Args:
            cancellation_id: Internal cancellation ID
            comments: Optional seller comments

        Returns:
            Result dict: {"success": True, "cancel_id": str, "new_status": str}

        Raises:
            ValueError: If cancellation not found
            RuntimeError: If API call fails
        """
        logger.info(
            f"[EbayCancellationService] approve_cancellation: user_id={self.user_id}, "
            f"cancellation_id={cancellation_id}"
        )

        # Get cancellation
        cancel_obj = self._get_cancellation_or_raise(cancellation_id)

        try:
            # Call eBay API
            self.cancellation_client.approve_cancellation(
                cancel_id=cancel_obj.cancel_id,
                comments=comments,
            )

            # Update local DB
            cancel_obj.cancel_status = "CANCEL_CLOSED_WITH_REFUND"
            cancel_obj.cancel_state = "CLOSED"
            if comments:
                cancel_obj.seller_comments = comments
            cancel_obj.closed_date = datetime.now(timezone.utc)
            cancel_obj.updated_at = datetime.now(timezone.utc)

            EbayCancellationRepository.update(self.db, cancel_obj)
            self.db.commit()

            logger.info(
                f"[EbayCancellationService] Cancellation {cancel_obj.cancel_id} approved"
            )

            return {
                "success": True,
                "cancel_id": cancel_obj.cancel_id,
                "new_status": "CANCEL_CLOSED_WITH_REFUND",
            }

        except Exception as e:
            self.db.rollback()
            logger.error(
                f"[EbayCancellationService] Failed to approve cancellation "
                f"{cancel_obj.cancel_id}: {e}",
                exc_info=True,
            )
            raise RuntimeError(f"Failed to approve cancellation: {str(e)}") from e

    def reject_cancellation(
        self,
        cancellation_id: int,
        reason: str,
        tracking_number: Optional[str] = None,
        carrier: Optional[str] = None,
        shipped_date: Optional[datetime] = None,
        comments: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Reject a buyer's cancellation request.

        Args:
            cancellation_id: Internal cancellation ID
            reason: Rejection reason:
                - "ALREADY_SHIPPED" (requires tracking_number)
                - "OTHER_SELLER_REJECT_REASON"
            tracking_number: Required if reason is "ALREADY_SHIPPED"
            carrier: Shipping carrier
            shipped_date: When item was shipped
            comments: Optional comments

        Returns:
            Result dict: {"success": True, "cancel_id": str, "new_status": str}

        Raises:
            ValueError: If cancellation not found or tracking required but missing
            RuntimeError: If API call fails
        """
        # Validate tracking requirement
        if reason == "ALREADY_SHIPPED" and not tracking_number:
            raise ValueError(
                "Tracking number is required when rejecting with reason ALREADY_SHIPPED"
            )

        logger.info(
            f"[EbayCancellationService] reject_cancellation: user_id={self.user_id}, "
            f"cancellation_id={cancellation_id}, reason={reason}"
        )

        # Get cancellation
        cancel_obj = self._get_cancellation_or_raise(cancellation_id)

        try:
            # Call eBay API
            self.cancellation_client.reject_cancellation(
                cancel_id=cancel_obj.cancel_id,
                reason=reason,
                tracking_number=tracking_number,
                carrier=carrier,
                shipped_date=shipped_date,
                comments=comments,
            )

            # Update local DB
            cancel_obj.cancel_status = "CANCEL_REJECTED"
            cancel_obj.cancel_state = "CLOSED"
            cancel_obj.reject_reason = reason
            if tracking_number:
                cancel_obj.tracking_number = tracking_number
            if carrier:
                cancel_obj.carrier = carrier
            if shipped_date:
                cancel_obj.shipped_date = shipped_date
            if comments:
                cancel_obj.seller_comments = comments
            cancel_obj.closed_date = datetime.now(timezone.utc)
            cancel_obj.updated_at = datetime.now(timezone.utc)

            EbayCancellationRepository.update(self.db, cancel_obj)
            self.db.commit()

            logger.info(
                f"[EbayCancellationService] Cancellation {cancel_obj.cancel_id} rejected"
            )

            return {
                "success": True,
                "cancel_id": cancel_obj.cancel_id,
                "new_status": "CANCEL_REJECTED",
            }

        except Exception as e:
            self.db.rollback()
            logger.error(
                f"[EbayCancellationService] Failed to reject cancellation "
                f"{cancel_obj.cancel_id}: {e}",
                exc_info=True,
            )
            raise RuntimeError(f"Failed to reject cancellation: {str(e)}") from e

    # =========================================================================
    # Statistics
    # =========================================================================

    def get_cancellation_statistics(self) -> Dict[str, Any]:
        """
        Get cancellation statistics.

        Returns:
            Statistics dict:
            {
                "pending": int,
                "closed": int,
                "needs_action": int,
                "past_due": int,
            }
        """
        stats = {
            "pending": EbayCancellationRepository.count_pending(self.db),
            "closed": EbayCancellationRepository.count_closed(self.db),
            "needs_action": EbayCancellationRepository.count_needs_action(self.db),
            "past_due": EbayCancellationRepository.count_past_response_due(self.db),
        }

        logger.debug(
            f"[EbayCancellationService] Statistics: pending={stats['pending']}, "
            f"closed={stats['closed']}, needs_action={stats['needs_action']}, "
            f"past_due={stats['past_due']}"
        )

        return stats

    # =========================================================================
    # Helpers
    # =========================================================================

    def _get_cancellation_or_raise(self, cancellation_id: int) -> EbayCancellation:
        """
        Get cancellation by ID or raise ValueError.

        Args:
            cancellation_id: Internal cancellation ID

        Returns:
            EbayCancellation instance

        Raises:
            ValueError: If cancellation not found
        """
        cancel_obj = EbayCancellationRepository.get_by_id(self.db, cancellation_id)

        if not cancel_obj:
            raise ValueError(f"Cancellation {cancellation_id} not found")

        return cancel_obj
