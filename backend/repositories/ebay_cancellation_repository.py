"""
eBay Cancellation Repository

Repository for managing eBay cancellations (CRUD operations).
Responsibility: Data access for ebay_cancellations table (schema user_{id}).

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

from models.user.ebay_cancellation import EbayCancellation
from shared.logging import get_logger

logger = get_logger(__name__)


class EbayCancellationRepository:
    """
    Repository for managing EbayCancellation entities.

    Provides all CRUD operations and specialized queries.
    All methods are static for ease of use.
    """

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    @staticmethod
    def create(db: Session, cancellation: EbayCancellation) -> EbayCancellation:
        """
        Create a new eBay cancellation.

        Args:
            db: SQLAlchemy Session
            cancellation: EbayCancellation instance to create

        Returns:
            EbayCancellation: Created instance with ID assigned
        """
        db.add(cancellation)
        db.flush()  # Get ID without committing (caller manages transaction)

        logger.debug(
            f"[EbayCancellationRepository] Cancellation created: id={cancellation.id}, "
            f"cancel_id={cancellation.cancel_id}"
        )

        return cancellation

    @staticmethod
    def get_by_id(db: Session, cancellation_id: int) -> Optional[EbayCancellation]:
        """
        Get a cancellation by its internal ID.

        Args:
            db: SQLAlchemy Session
            cancellation_id: Internal cancellation ID

        Returns:
            EbayCancellation if found, None otherwise
        """
        return (
            db.query(EbayCancellation)
            .filter(EbayCancellation.id == cancellation_id)
            .first()
        )

    @staticmethod
    def get_by_cancel_id(db: Session, cancel_id: str) -> Optional[EbayCancellation]:
        """
        Get a cancellation by its eBay cancel ID (unique key).

        Args:
            db: SQLAlchemy Session
            cancel_id: eBay cancellation ID (e.g., "5000012345")

        Returns:
            EbayCancellation if found, None otherwise
        """
        return (
            db.query(EbayCancellation)
            .filter(EbayCancellation.cancel_id == cancel_id)
            .first()
        )

    @staticmethod
    def get_by_order_id(db: Session, order_id: str) -> List[EbayCancellation]:
        """
        Get all cancellations for a specific order.

        Args:
            db: SQLAlchemy Session
            order_id: eBay order ID

        Returns:
            List of EbayCancellation instances
        """
        cancellations = (
            db.query(EbayCancellation)
            .filter(EbayCancellation.order_id == order_id)
            .order_by(EbayCancellation.creation_date.desc())
            .all()
        )

        logger.debug(
            f"[EbayCancellationRepository] get_by_order_id: order_id={order_id}, "
            f"returned={len(cancellations)}"
        )

        return cancellations

    @staticmethod
    def update(db: Session, cancellation: EbayCancellation) -> EbayCancellation:
        """
        Update an existing cancellation.

        Args:
            db: SQLAlchemy Session
            cancellation: EbayCancellation instance to update

        Returns:
            EbayCancellation: Updated instance
        """
        db.flush()

        logger.debug(
            f"[EbayCancellationRepository] Cancellation updated: id={cancellation.id}, "
            f"cancel_id={cancellation.cancel_id}"
        )

        return cancellation

    @staticmethod
    def delete(db: Session, cancellation: EbayCancellation) -> bool:
        """
        Delete a cancellation (hard delete).

        Args:
            db: SQLAlchemy Session
            cancellation: EbayCancellation instance to delete

        Returns:
            bool: True if deletion successful
        """
        db.delete(cancellation)
        db.flush()

        logger.debug(
            f"[EbayCancellationRepository] Cancellation deleted: id={cancellation.id}, "
            f"cancel_id={cancellation.cancel_id}"
        )

        return True

    # =========================================================================
    # Query Operations
    # =========================================================================

    @staticmethod
    def list_cancellations(
        db: Session,
        skip: int = 0,
        limit: int = 50,
        cancel_state: Optional[str] = None,
        cancel_status: Optional[str] = None,
        order_id: Optional[str] = None,
    ) -> Tuple[List[EbayCancellation], int]:
        """
        List cancellations with filters and pagination.

        Args:
            db: SQLAlchemy Session
            skip: Number of results to skip (pagination)
            limit: Max number of results
            cancel_state: Filter by state (CLOSED)
            cancel_status: Filter by status
            order_id: Filter by order ID

        Returns:
            Tuple[List[EbayCancellation], int]: (list of cancellations, total count)
        """
        query = db.query(EbayCancellation)

        # Apply filters
        if cancel_state:
            query = query.filter(EbayCancellation.cancel_state == cancel_state)

        if cancel_status:
            query = query.filter(EbayCancellation.cancel_status == cancel_status)

        if order_id:
            query = query.filter(EbayCancellation.order_id == order_id)

        # Count total
        total = query.count()

        # Apply pagination and ordering
        cancellations = (
            query.order_by(EbayCancellation.creation_date.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        logger.debug(
            f"[EbayCancellationRepository] list_cancellations: skip={skip}, limit={limit}, "
            f"total={total}, returned={len(cancellations)}"
        )

        return cancellations, total

    @staticmethod
    def list_by_status(
        db: Session, status: str, limit: int = 100
    ) -> List[EbayCancellation]:
        """
        List cancellations by status.

        Args:
            db: SQLAlchemy Session
            status: Cancellation status
            limit: Max number of results

        Returns:
            List[EbayCancellation]: List of cancellations
        """
        cancellations = (
            db.query(EbayCancellation)
            .filter(EbayCancellation.cancel_status == status)
            .order_by(EbayCancellation.creation_date.desc())
            .limit(limit)
            .all()
        )

        logger.debug(
            f"[EbayCancellationRepository] list_by_status: status={status}, "
            f"returned={len(cancellations)}"
        )

        return cancellations

    @staticmethod
    def list_needs_action(db: Session, limit: int = 100) -> List[EbayCancellation]:
        """
        List cancellations requiring seller action.

        Action-needed: Buyer-initiated cancellations that are pending.

        Args:
            db: SQLAlchemy Session
            limit: Max number of results

        Returns:
            List[EbayCancellation]: List of cancellations needing action
        """
        pending_statuses = ["CANCEL_REQUESTED", "CANCEL_PENDING"]

        cancellations = (
            db.query(EbayCancellation)
            .filter(
                and_(
                    EbayCancellation.requestor_role == "BUYER",
                    EbayCancellation.cancel_status.in_(pending_statuses),
                )
            )
            .order_by(EbayCancellation.response_due_date.asc())  # Most urgent first
            .limit(limit)
            .all()
        )

        logger.debug(
            f"[EbayCancellationRepository] list_needs_action: returned={len(cancellations)}"
        )

        return cancellations

    @staticmethod
    def list_past_response_due(db: Session, limit: int = 100) -> List[EbayCancellation]:
        """
        List cancellations past their response deadline.

        Args:
            db: SQLAlchemy Session
            limit: Max number of results

        Returns:
            List[EbayCancellation]: List of cancellations past deadline
        """
        now = datetime.now(timezone.utc)
        pending_statuses = ["CANCEL_REQUESTED", "CANCEL_PENDING"]

        cancellations = (
            db.query(EbayCancellation)
            .filter(
                and_(
                    EbayCancellation.cancel_status.in_(pending_statuses),
                    EbayCancellation.response_due_date.isnot(None),
                    EbayCancellation.response_due_date < now,
                )
            )
            .order_by(EbayCancellation.response_due_date.asc())
            .limit(limit)
            .all()
        )

        logger.debug(
            f"[EbayCancellationRepository] list_past_response_due: returned={len(cancellations)}"
        )

        return cancellations

    # =========================================================================
    # Aggregation Operations
    # =========================================================================

    @staticmethod
    def count_by_status(db: Session, status: str) -> int:
        """
        Count cancellations by status.

        Args:
            db: SQLAlchemy Session
            status: Cancellation status

        Returns:
            int: Number of cancellations
        """
        count = (
            db.query(func.count(EbayCancellation.id))
            .filter(EbayCancellation.cancel_status == status)
            .scalar()
            or 0
        )

        logger.debug(
            f"[EbayCancellationRepository] count_by_status: status={status}, count={count}"
        )

        return count

    @staticmethod
    def count_needs_action(db: Session) -> int:
        """
        Count cancellations needing seller action.

        Args:
            db: SQLAlchemy Session

        Returns:
            int: Number of cancellations needing action
        """
        pending_statuses = ["CANCEL_REQUESTED", "CANCEL_PENDING"]

        count = (
            db.query(func.count(EbayCancellation.id))
            .filter(
                and_(
                    EbayCancellation.requestor_role == "BUYER",
                    EbayCancellation.cancel_status.in_(pending_statuses),
                )
            )
            .scalar()
            or 0
        )

        logger.debug(
            f"[EbayCancellationRepository] count_needs_action: count={count}"
        )

        return count

    @staticmethod
    def count_past_response_due(db: Session) -> int:
        """
        Count cancellations past their response deadline.

        Args:
            db: SQLAlchemy Session

        Returns:
            int: Number of cancellations past deadline
        """
        now = datetime.now(timezone.utc)
        pending_statuses = ["CANCEL_REQUESTED", "CANCEL_PENDING"]

        count = (
            db.query(func.count(EbayCancellation.id))
            .filter(
                and_(
                    EbayCancellation.cancel_status.in_(pending_statuses),
                    EbayCancellation.response_due_date.isnot(None),
                    EbayCancellation.response_due_date < now,
                )
            )
            .scalar()
            or 0
        )

        logger.debug(
            f"[EbayCancellationRepository] count_past_response_due: count={count}"
        )

        return count

    @staticmethod
    def count_pending(db: Session) -> int:
        """
        Count pending cancellations.

        Args:
            db: SQLAlchemy Session

        Returns:
            int: Number of pending cancellations
        """
        pending_statuses = ["CANCEL_REQUESTED", "CANCEL_PENDING"]

        count = (
            db.query(func.count(EbayCancellation.id))
            .filter(EbayCancellation.cancel_status.in_(pending_statuses))
            .scalar()
            or 0
        )

        logger.debug(
            f"[EbayCancellationRepository] count_pending: count={count}"
        )

        return count

    @staticmethod
    def count_closed(db: Session) -> int:
        """
        Count closed cancellations.

        Args:
            db: SQLAlchemy Session

        Returns:
            int: Number of closed cancellations
        """
        count = (
            db.query(func.count(EbayCancellation.id))
            .filter(EbayCancellation.cancel_state == "CLOSED")
            .scalar()
            or 0
        )

        logger.debug(
            f"[EbayCancellationRepository] count_closed: count={count}"
        )

        return count

    @staticmethod
    def exists(db: Session, cancel_id: str) -> bool:
        """
        Check if a cancellation exists by its eBay cancel ID.

        Args:
            db: SQLAlchemy Session
            cancel_id: eBay cancellation ID (e.g., "5000012345")

        Returns:
            bool: True if exists, False otherwise
        """
        count = (
            db.query(func.count(EbayCancellation.id))
            .filter(EbayCancellation.cancel_id == cancel_id)
            .scalar()
            or 0
        )

        return count > 0
