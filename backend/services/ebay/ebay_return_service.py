"""
eBay Return Service

Service for eBay return business operations.
Responsibility: Business logic for return management (read, actions, statistics).

Architecture:
- Read operations via EbayReturnRepository
- Action operations: eBay API call + local DB update
- Statistics aggregation

Created: 2026-01-13
Author: Claude
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from models.user.ebay_return import EbayReturn
from repositories.ebay_return_repository import EbayReturnRepository
from services.ebay.ebay_return_client import EbayReturnClient
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class EbayReturnService:
    """
    Service for eBay return business operations.

    Provides:
    - Read operations (get, list, filter)
    - Action operations (accept, decline, refund, etc.)
    - Statistics aggregation

    Usage:
        >>> service = EbayReturnService(db_session, user_id=1)
        >>> returns, total = service.list_returns(state="OPEN")
        >>> service.accept_return(return_id=123, comments="Shipping label sent")
    """

    def __init__(self, db: Session, user_id: int):
        """
        Initialize return service.

        Args:
            db: SQLAlchemy Session (with search_path already set)
            user_id: User ID for eBay authentication
        """
        self.db = db
        self.user_id = user_id
        self.return_client = EbayReturnClient(db, user_id)

        logger.info(f"[EbayReturnService] Initialized for user_id={user_id}")

    # =========================================================================
    # Read Operations
    # =========================================================================

    def get_return(self, return_id: int) -> Optional[EbayReturn]:
        """
        Get return by internal ID.

        Args:
            return_id: Internal return ID

        Returns:
            EbayReturn if found, None otherwise
        """
        return EbayReturnRepository.get_by_id(self.db, return_id)

    def get_return_by_ebay_id(self, ebay_return_id: str) -> Optional[EbayReturn]:
        """
        Get return by eBay return ID.

        Args:
            ebay_return_id: eBay return ID (e.g., "5000012345")

        Returns:
            EbayReturn if found, None otherwise
        """
        return EbayReturnRepository.get_by_ebay_return_id(self.db, ebay_return_id)

    def list_returns(
        self,
        skip: int = 0,
        limit: int = 50,
        state: Optional[str] = None,
        status: Optional[str] = None,
        order_id: Optional[str] = None,
    ) -> Tuple[List[EbayReturn], int]:
        """
        List returns with pagination and filters.

        Args:
            skip: Number of results to skip
            limit: Max number of results
            state: Filter by state (OPEN, CLOSED)
            status: Filter by status
            order_id: Filter by order ID

        Returns:
            Tuple[List[EbayReturn], int]: (list of returns, total count)
        """
        return EbayReturnRepository.list_returns(
            self.db,
            skip=skip,
            limit=limit,
            state=state,
            status=status,
            order_id=order_id,
        )

    def get_returns_needing_action(self, limit: int = 100) -> List[EbayReturn]:
        """
        Get returns requiring seller action.

        Returns:
            List of returns needing action (sorted by deadline)
        """
        return EbayReturnRepository.list_needs_action(self.db, limit)

    def get_returns_past_deadline(self, limit: int = 100) -> List[EbayReturn]:
        """
        Get returns past their deadline (urgent).

        Returns:
            List of returns past deadline
        """
        return EbayReturnRepository.list_past_deadline(self.db, limit)

    def get_returns_for_order(self, order_id: str) -> List[EbayReturn]:
        """
        Get all returns for a specific order.

        Args:
            order_id: eBay order ID

        Returns:
            List of returns for the order
        """
        return EbayReturnRepository.get_by_order_id(self.db, order_id)

    # =========================================================================
    # Action Operations
    # =========================================================================

    def accept_return(
        self,
        return_id: int,
        comments: Optional[str] = None,
        rma_number: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Accept a return request.

        Workflow:
        1. Get return from DB
        2. Call eBay API to accept
        3. Update local DB status
        4. Commit

        Args:
            return_id: Internal return ID
            comments: Optional seller comments
            rma_number: Optional RMA number

        Returns:
            Result dict: {"success": True, "return_id": str, "new_status": str}

        Raises:
            ValueError: If return not found
            RuntimeError: If API call fails
        """
        logger.info(
            f"[EbayReturnService] accept_return: user_id={self.user_id}, "
            f"return_id={return_id}"
        )

        # Get return
        return_obj = self._get_return_or_raise(return_id)

        try:
            # Call eBay API
            self.return_client.decide_return(
                return_id=return_obj.return_id,
                decision="ACCEPT",
                comments=comments,
                rma_number=rma_number,
            )

            # Update local DB
            return_obj.status = "RETURN_ACCEPTED"
            if rma_number:
                return_obj.rma_number = rma_number
            if comments:
                return_obj.seller_comments = comments
            return_obj.updated_at = datetime.now(timezone.utc)

            EbayReturnRepository.update(self.db, return_obj)
            self.db.commit()

            logger.info(
                f"[EbayReturnService] Return {return_obj.return_id} accepted"
            )

            return {
                "success": True,
                "return_id": return_obj.return_id,
                "new_status": "RETURN_ACCEPTED",
            }

        except Exception as e:
            self.db.rollback()
            logger.error(
                f"[EbayReturnService] Failed to accept return {return_obj.return_id}: {e}",
                exc_info=True,
            )
            raise RuntimeError(f"Failed to accept return: {str(e)}") from e

    def decline_return(
        self,
        return_id: int,
        comments: str,
    ) -> Dict[str, Any]:
        """
        Decline a return request.

        **Warning**: Declining returns can negatively impact seller metrics.

        Args:
            return_id: Internal return ID
            comments: Required reason for declining

        Returns:
            Result dict: {"success": True, "return_id": str, "new_status": str}

        Raises:
            ValueError: If return not found or comments missing
            RuntimeError: If API call fails
        """
        if not comments:
            raise ValueError("Comments are required when declining a return")

        logger.info(
            f"[EbayReturnService] decline_return: user_id={self.user_id}, "
            f"return_id={return_id}"
        )

        # Get return
        return_obj = self._get_return_or_raise(return_id)

        try:
            # Call eBay API
            self.return_client.decide_return(
                return_id=return_obj.return_id,
                decision="DECLINE",
                comments=comments,
            )

            # Update local DB
            return_obj.status = "RETURN_DECLINED"
            return_obj.seller_comments = comments
            return_obj.updated_at = datetime.now(timezone.utc)

            EbayReturnRepository.update(self.db, return_obj)
            self.db.commit()

            logger.info(
                f"[EbayReturnService] Return {return_obj.return_id} declined"
            )

            return {
                "success": True,
                "return_id": return_obj.return_id,
                "new_status": "RETURN_DECLINED",
            }

        except Exception as e:
            self.db.rollback()
            logger.error(
                f"[EbayReturnService] Failed to decline return {return_obj.return_id}: {e}",
                exc_info=True,
            )
            raise RuntimeError(f"Failed to decline return: {str(e)}") from e

    def issue_refund(
        self,
        return_id: int,
        refund_amount: Optional[float] = None,
        currency: Optional[str] = None,
        comments: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Issue refund for a return.

        Args:
            return_id: Internal return ID
            refund_amount: Optional partial refund amount (full if None)
            currency: Currency code (e.g., "EUR")
            comments: Optional refund comments

        Returns:
            Result dict: {"success": True, "return_id": str, "refund_status": str}

        Raises:
            ValueError: If return not found
            RuntimeError: If API call fails
        """
        logger.info(
            f"[EbayReturnService] issue_refund: user_id={self.user_id}, "
            f"return_id={return_id}, amount={refund_amount}"
        )

        # Get return
        return_obj = self._get_return_or_raise(return_id)

        try:
            # Call eBay API
            self.return_client.issue_refund(
                return_id=return_obj.return_id,
                refund_amount=refund_amount,
                currency=currency,
                comments=comments,
            )

            # Update local DB
            return_obj.refund_status = "REFUND_ISSUED"
            if refund_amount is not None:
                return_obj.refund_amount = refund_amount
            if currency:
                return_obj.refund_currency = currency
            return_obj.updated_at = datetime.now(timezone.utc)

            EbayReturnRepository.update(self.db, return_obj)
            self.db.commit()

            logger.info(
                f"[EbayReturnService] Refund issued for return {return_obj.return_id}"
            )

            return {
                "success": True,
                "return_id": return_obj.return_id,
                "refund_status": "REFUND_ISSUED",
            }

        except Exception as e:
            self.db.rollback()
            logger.error(
                f"[EbayReturnService] Failed to issue refund for {return_obj.return_id}: {e}",
                exc_info=True,
            )
            raise RuntimeError(f"Failed to issue refund: {str(e)}") from e

    def mark_as_received(
        self,
        return_id: int,
        comments: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Mark return item as received by seller.

        Args:
            return_id: Internal return ID
            comments: Optional comments about item condition

        Returns:
            Result dict: {"success": True, "return_id": str, "new_status": str}

        Raises:
            ValueError: If return not found
            RuntimeError: If API call fails
        """
        logger.info(
            f"[EbayReturnService] mark_as_received: user_id={self.user_id}, "
            f"return_id={return_id}"
        )

        # Get return
        return_obj = self._get_return_or_raise(return_id)

        try:
            # Call eBay API
            self.return_client.mark_as_received(
                return_id=return_obj.return_id,
                comments=comments,
            )

            # Update local DB
            return_obj.status = "RETURN_ITEM_RECEIVED"
            return_obj.received_date = datetime.now(timezone.utc)
            if comments:
                return_obj.seller_comments = comments
            return_obj.updated_at = datetime.now(timezone.utc)

            EbayReturnRepository.update(self.db, return_obj)
            self.db.commit()

            logger.info(
                f"[EbayReturnService] Return {return_obj.return_id} marked as received"
            )

            return {
                "success": True,
                "return_id": return_obj.return_id,
                "new_status": "RETURN_ITEM_RECEIVED",
            }

        except Exception as e:
            self.db.rollback()
            logger.error(
                f"[EbayReturnService] Failed to mark received {return_obj.return_id}: {e}",
                exc_info=True,
            )
            raise RuntimeError(f"Failed to mark as received: {str(e)}") from e

    def send_message(
        self,
        return_id: int,
        message: str,
    ) -> Dict[str, Any]:
        """
        Send message to buyer about return.

        Args:
            return_id: Internal return ID
            message: Message text

        Returns:
            Result dict: {"success": True, "return_id": str}

        Raises:
            ValueError: If return not found or message empty
            RuntimeError: If API call fails
        """
        if not message:
            raise ValueError("Message cannot be empty")

        logger.info(
            f"[EbayReturnService] send_message: user_id={self.user_id}, "
            f"return_id={return_id}"
        )

        # Get return
        return_obj = self._get_return_or_raise(return_id)

        try:
            # Call eBay API
            self.return_client.send_message(
                return_id=return_obj.return_id,
                message=message,
            )

            # Update local DB
            return_obj.seller_comments = message
            return_obj.updated_at = datetime.now(timezone.utc)

            EbayReturnRepository.update(self.db, return_obj)
            self.db.commit()

            logger.info(
                f"[EbayReturnService] Message sent for return {return_obj.return_id}"
            )

            return {
                "success": True,
                "return_id": return_obj.return_id,
            }

        except Exception as e:
            self.db.rollback()
            logger.error(
                f"[EbayReturnService] Failed to send message for {return_obj.return_id}: {e}",
                exc_info=True,
            )
            raise RuntimeError(f"Failed to send message: {str(e)}") from e

    # =========================================================================
    # Statistics
    # =========================================================================

    def get_return_statistics(self) -> Dict[str, Any]:
        """
        Get return statistics.

        Returns:
            Statistics dict:
            {
                "open": int,
                "closed": int,
                "needs_action": int,
                "past_deadline": int,
            }
        """
        stats = {
            "open": EbayReturnRepository.count_by_state(self.db, "OPEN"),
            "closed": EbayReturnRepository.count_by_state(self.db, "CLOSED"),
            "needs_action": EbayReturnRepository.count_needs_action(self.db),
            "past_deadline": EbayReturnRepository.count_past_deadline(self.db),
        }

        logger.debug(
            f"[EbayReturnService] Statistics: open={stats['open']}, "
            f"closed={stats['closed']}, needs_action={stats['needs_action']}, "
            f"past_deadline={stats['past_deadline']}"
        )

        return stats

    # =========================================================================
    # Helpers
    # =========================================================================

    def _get_return_or_raise(self, return_id: int) -> EbayReturn:
        """
        Get return by ID or raise ValueError.

        Args:
            return_id: Internal return ID

        Returns:
            EbayReturn instance

        Raises:
            ValueError: If return not found
        """
        return_obj = EbayReturnRepository.get_by_id(self.db, return_id)

        if not return_obj:
            raise ValueError(f"Return {return_id} not found")

        return return_obj
