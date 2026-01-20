"""
eBay Refund Repository

Repository for managing eBay refunds (CRUD operations).
Responsibility: Data access for ebay_refunds table (schema user_{id}).

Architecture:
- Repository pattern for DB isolation
- Standard CRUD operations
- Optimized queries with indexes
- No business logic (pure data access)

Created: 2026-01-14
Author: Claude
"""

from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from models.user.ebay_refund import EbayRefund
from shared.logging import get_logger

logger = get_logger(__name__)


class EbayRefundRepository:
    """
    Repository for managing EbayRefund entities.

    Provides all CRUD operations and specialized queries.
    All methods are static for ease of use.
    """

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    @staticmethod
    def create(db: Session, refund: EbayRefund) -> EbayRefund:
        """
        Create a new eBay refund.

        Args:
            db: SQLAlchemy Session
            refund: EbayRefund instance to create

        Returns:
            EbayRefund: Created instance with ID assigned
        """
        db.add(refund)
        db.flush()  # Get ID without committing (caller manages transaction)

        logger.debug(
            f"[EbayRefundRepository] Refund created: id={refund.id}, "
            f"refund_id={refund.refund_id}"
        )

        return refund

    @staticmethod
    def get_by_id(db: Session, refund_id: int) -> Optional[EbayRefund]:
        """
        Get a refund by its internal ID.

        Args:
            db: SQLAlchemy Session
            refund_id: Internal refund ID

        Returns:
            EbayRefund if found, None otherwise
        """
        return db.query(EbayRefund).filter(EbayRefund.id == refund_id).first()

    @staticmethod
    def get_by_ebay_refund_id(db: Session, ebay_refund_id: str) -> Optional[EbayRefund]:
        """
        Get a refund by its eBay refund ID (unique key).

        Args:
            db: SQLAlchemy Session
            ebay_refund_id: eBay refund ID

        Returns:
            EbayRefund if found, None otherwise
        """
        return (
            db.query(EbayRefund)
            .filter(EbayRefund.refund_id == ebay_refund_id)
            .first()
        )

    @staticmethod
    def get_by_order_id(db: Session, order_id: str) -> List[EbayRefund]:
        """
        Get all refunds for a specific order.

        Args:
            db: SQLAlchemy Session
            order_id: eBay order ID

        Returns:
            List of EbayRefund instances
        """
        refunds = (
            db.query(EbayRefund)
            .filter(EbayRefund.order_id == order_id)
            .order_by(EbayRefund.refund_date.desc())
            .all()
        )

        logger.debug(
            f"[EbayRefundRepository] get_by_order_id: order_id={order_id}, "
            f"returned={len(refunds)}"
        )

        return refunds

    @staticmethod
    def get_by_return_id(db: Session, return_id: str) -> List[EbayRefund]:
        """
        Get all refunds associated with a return.

        Args:
            db: SQLAlchemy Session
            return_id: eBay return ID

        Returns:
            List of EbayRefund instances
        """
        return (
            db.query(EbayRefund)
            .filter(EbayRefund.return_id == return_id)
            .order_by(EbayRefund.refund_date.desc())
            .all()
        )

    @staticmethod
    def get_by_cancel_id(db: Session, cancel_id: str) -> List[EbayRefund]:
        """
        Get all refunds associated with a cancellation.

        Args:
            db: SQLAlchemy Session
            cancel_id: eBay cancellation ID

        Returns:
            List of EbayRefund instances
        """
        return (
            db.query(EbayRefund)
            .filter(EbayRefund.cancel_id == cancel_id)
            .order_by(EbayRefund.refund_date.desc())
            .all()
        )

    @staticmethod
    def update(db: Session, refund: EbayRefund) -> EbayRefund:
        """
        Update an existing refund.

        Args:
            db: SQLAlchemy Session
            refund: EbayRefund instance to update

        Returns:
            EbayRefund: Updated instance
        """
        db.flush()

        logger.debug(
            f"[EbayRefundRepository] Refund updated: id={refund.id}, "
            f"refund_id={refund.refund_id}"
        )

        return refund

    @staticmethod
    def delete(db: Session, refund: EbayRefund) -> bool:
        """
        Delete a refund (hard delete).

        Args:
            db: SQLAlchemy Session
            refund: EbayRefund instance to delete

        Returns:
            bool: True if deletion successful
        """
        db.delete(refund)
        db.flush()

        logger.debug(
            f"[EbayRefundRepository] Refund deleted: id={refund.id}, "
            f"refund_id={refund.refund_id}"
        )

        return True

    # =========================================================================
    # Query Operations
    # =========================================================================

    @staticmethod
    def list_refunds(
        db: Session,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
        source: Optional[str] = None,
        order_id: Optional[str] = None,
    ) -> Tuple[List[EbayRefund], int]:
        """
        List refunds with filters and pagination.

        Args:
            db: SQLAlchemy Session
            skip: Number of results to skip (pagination)
            limit: Max number of results
            status: Filter by status (PENDING, REFUNDED, FAILED)
            source: Filter by source (RETURN, CANCELLATION, MANUAL, OTHER)
            order_id: Filter by order ID

        Returns:
            Tuple[List[EbayRefund], int]: (list of refunds, total count)
        """
        query = db.query(EbayRefund)

        # Apply filters
        if status:
            query = query.filter(EbayRefund.refund_status == status)

        if source:
            query = query.filter(EbayRefund.refund_source == source)

        if order_id:
            query = query.filter(EbayRefund.order_id == order_id)

        # Count total
        total = query.count()

        # Apply pagination and ordering
        refunds = (
            query.order_by(EbayRefund.refund_date.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        logger.debug(
            f"[EbayRefundRepository] list_refunds: skip={skip}, limit={limit}, "
            f"total={total}, returned={len(refunds)}"
        )

        return refunds, total

    @staticmethod
    def list_by_status(db: Session, status: str, limit: int = 100) -> List[EbayRefund]:
        """
        List refunds by status.

        Args:
            db: SQLAlchemy Session
            status: Refund status (PENDING, REFUNDED, FAILED)
            limit: Max number of results

        Returns:
            List[EbayRefund]: List of refunds
        """
        refunds = (
            db.query(EbayRefund)
            .filter(EbayRefund.refund_status == status)
            .order_by(EbayRefund.refund_date.desc())
            .limit(limit)
            .all()
        )

        logger.debug(
            f"[EbayRefundRepository] list_by_status: status={status}, "
            f"returned={len(refunds)}"
        )

        return refunds

    @staticmethod
    def list_by_source(db: Session, source: str, limit: int = 100) -> List[EbayRefund]:
        """
        List refunds by source.

        Args:
            db: SQLAlchemy Session
            source: Refund source (RETURN, CANCELLATION, MANUAL, OTHER)
            limit: Max number of results

        Returns:
            List[EbayRefund]: List of refunds
        """
        refunds = (
            db.query(EbayRefund)
            .filter(EbayRefund.refund_source == source)
            .order_by(EbayRefund.refund_date.desc())
            .limit(limit)
            .all()
        )

        logger.debug(
            f"[EbayRefundRepository] list_by_source: source={source}, "
            f"returned={len(refunds)}"
        )

        return refunds

    @staticmethod
    def list_pending(db: Session, limit: int = 100) -> List[EbayRefund]:
        """
        List pending refunds.

        Args:
            db: SQLAlchemy Session
            limit: Max number of results

        Returns:
            List[EbayRefund]: List of pending refunds
        """
        return EbayRefundRepository.list_by_status(db, "PENDING", limit)

    @staticmethod
    def list_failed(db: Session, limit: int = 100) -> List[EbayRefund]:
        """
        List failed refunds.

        Args:
            db: SQLAlchemy Session
            limit: Max number of results

        Returns:
            List[EbayRefund]: List of failed refunds
        """
        return EbayRefundRepository.list_by_status(db, "FAILED", limit)

    # =========================================================================
    # Aggregation Operations
    # =========================================================================

    @staticmethod
    def count_by_status(db: Session, status: str) -> int:
        """
        Count refunds by status.

        Args:
            db: SQLAlchemy Session
            status: Refund status (PENDING, REFUNDED, FAILED)

        Returns:
            int: Number of refunds
        """
        count = (
            db.query(func.count(EbayRefund.id))
            .filter(EbayRefund.refund_status == status)
            .scalar()
            or 0
        )

        logger.debug(
            f"[EbayRefundRepository] count_by_status: status={status}, count={count}"
        )

        return count

    @staticmethod
    def count_by_source(db: Session, source: str) -> int:
        """
        Count refunds by source.

        Args:
            db: SQLAlchemy Session
            source: Refund source (RETURN, CANCELLATION, MANUAL, OTHER)

        Returns:
            int: Number of refunds
        """
        count = (
            db.query(func.count(EbayRefund.id))
            .filter(EbayRefund.refund_source == source)
            .scalar()
            or 0
        )

        logger.debug(
            f"[EbayRefundRepository] count_by_source: source={source}, count={count}"
        )

        return count

    @staticmethod
    def sum_refunded_amount(db: Session, currency: str = "EUR") -> float:
        """
        Sum total refunded amount.

        Args:
            db: SQLAlchemy Session
            currency: Currency to filter by

        Returns:
            float: Total refunded amount
        """
        total = (
            db.query(func.sum(EbayRefund.refund_amount))
            .filter(
                and_(
                    EbayRefund.refund_status == "REFUNDED",
                    EbayRefund.refund_currency == currency,
                )
            )
            .scalar()
            or 0.0
        )

        logger.debug(
            f"[EbayRefundRepository] sum_refunded_amount: currency={currency}, "
            f"total={total}"
        )

        return total

    @staticmethod
    def exists(db: Session, ebay_refund_id: str) -> bool:
        """
        Check if a refund exists by its eBay refund ID.

        Args:
            db: SQLAlchemy Session
            ebay_refund_id: eBay refund ID

        Returns:
            bool: True if exists, False otherwise
        """
        count = (
            db.query(func.count(EbayRefund.id))
            .filter(EbayRefund.refund_id == ebay_refund_id)
            .scalar()
            or 0
        )

        return count > 0

    @staticmethod
    def get_statistics(db: Session) -> dict:
        """
        Get refund statistics.

        Args:
            db: SQLAlchemy Session

        Returns:
            dict with statistics:
            {
                "pending": int,
                "completed": int,
                "failed": int,
                "total_refunded": float,
                "by_source": {"RETURN": int, "CANCELLATION": int, "MANUAL": int}
            }
        """
        pending = EbayRefundRepository.count_by_status(db, "PENDING")
        completed = EbayRefundRepository.count_by_status(db, "REFUNDED")
        failed = EbayRefundRepository.count_by_status(db, "FAILED")
        total_refunded = EbayRefundRepository.sum_refunded_amount(db)

        by_source = {
            "RETURN": EbayRefundRepository.count_by_source(db, "RETURN"),
            "CANCELLATION": EbayRefundRepository.count_by_source(db, "CANCELLATION"),
            "MANUAL": EbayRefundRepository.count_by_source(db, "MANUAL"),
        }

        return {
            "pending": pending,
            "completed": completed,
            "failed": failed,
            "total_refunded": total_refunded,
            "by_source": by_source,
        }
