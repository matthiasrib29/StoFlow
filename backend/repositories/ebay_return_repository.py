"""
eBay Return Repository

Repository for managing eBay returns (CRUD operations).
Responsibility: Data access for ebay_returns table (schema user_{id}).

Architecture:
- Repository pattern for DB isolation
- Standard CRUD operations
- Optimized queries with indexes
- No business logic (pure data access)

Created: 2026-01-13
Author: Claude
"""

from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from models.user.ebay_return import EbayReturn
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class EbayReturnRepository:
    """
    Repository for managing EbayReturn entities.

    Provides all CRUD operations and specialized queries.
    All methods are static for ease of use.
    """

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    @staticmethod
    def create(db: Session, return_: EbayReturn) -> EbayReturn:
        """
        Create a new eBay return.

        Args:
            db: SQLAlchemy Session
            return_: EbayReturn instance to create

        Returns:
            EbayReturn: Created instance with ID assigned
        """
        db.add(return_)
        db.flush()  # Get ID without committing (caller manages transaction)

        logger.debug(
            f"[EbayReturnRepository] Return created: id={return_.id}, "
            f"return_id={return_.return_id}"
        )

        return return_

    @staticmethod
    def get_by_id(db: Session, return_id: int) -> Optional[EbayReturn]:
        """
        Get a return by its internal ID.

        Args:
            db: SQLAlchemy Session
            return_id: Internal return ID

        Returns:
            EbayReturn if found, None otherwise
        """
        return db.query(EbayReturn).filter(EbayReturn.id == return_id).first()

    @staticmethod
    def get_by_ebay_return_id(db: Session, ebay_return_id: str) -> Optional[EbayReturn]:
        """
        Get a return by its eBay return ID (unique key).

        Args:
            db: SQLAlchemy Session
            ebay_return_id: eBay return ID (e.g., "5000012345")

        Returns:
            EbayReturn if found, None otherwise
        """
        return (
            db.query(EbayReturn)
            .filter(EbayReturn.return_id == ebay_return_id)
            .first()
        )

    @staticmethod
    def get_by_order_id(db: Session, order_id: str) -> List[EbayReturn]:
        """
        Get all returns for a specific order.

        Args:
            db: SQLAlchemy Session
            order_id: eBay order ID

        Returns:
            List of EbayReturn instances
        """
        returns = (
            db.query(EbayReturn)
            .filter(EbayReturn.order_id == order_id)
            .order_by(EbayReturn.creation_date.desc())
            .all()
        )

        logger.debug(
            f"[EbayReturnRepository] get_by_order_id: order_id={order_id}, "
            f"returned={len(returns)}"
        )

        return returns

    @staticmethod
    def update(db: Session, return_: EbayReturn) -> EbayReturn:
        """
        Update an existing return.

        Args:
            db: SQLAlchemy Session
            return_: EbayReturn instance to update

        Returns:
            EbayReturn: Updated instance
        """
        db.flush()

        logger.debug(
            f"[EbayReturnRepository] Return updated: id={return_.id}, "
            f"return_id={return_.return_id}"
        )

        return return_

    @staticmethod
    def delete(db: Session, return_: EbayReturn) -> bool:
        """
        Delete a return (hard delete).

        Args:
            db: SQLAlchemy Session
            return_: EbayReturn instance to delete

        Returns:
            bool: True if deletion successful
        """
        db.delete(return_)
        db.flush()

        logger.debug(
            f"[EbayReturnRepository] Return deleted: id={return_.id}, "
            f"return_id={return_.return_id}"
        )

        return True

    # =========================================================================
    # Query Operations
    # =========================================================================

    @staticmethod
    def list_returns(
        db: Session,
        skip: int = 0,
        limit: int = 50,
        state: Optional[str] = None,
        status: Optional[str] = None,
        order_id: Optional[str] = None,
    ) -> Tuple[List[EbayReturn], int]:
        """
        List returns with filters and pagination.

        Args:
            db: SQLAlchemy Session
            skip: Number of results to skip (pagination)
            limit: Max number of results
            state: Filter by state (OPEN, CLOSED)
            status: Filter by status
            order_id: Filter by order ID

        Returns:
            Tuple[List[EbayReturn], int]: (list of returns, total count)
        """
        query = db.query(EbayReturn)

        # Apply filters
        if state:
            query = query.filter(EbayReturn.state == state)

        if status:
            query = query.filter(EbayReturn.status == status)

        if order_id:
            query = query.filter(EbayReturn.order_id == order_id)

        # Count total
        total = query.count()

        # Apply pagination and ordering
        returns = (
            query.order_by(EbayReturn.creation_date.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        logger.debug(
            f"[EbayReturnRepository] list_returns: skip={skip}, limit={limit}, "
            f"total={total}, returned={len(returns)}"
        )

        return returns, total

    @staticmethod
    def list_by_state(db: Session, state: str, limit: int = 100) -> List[EbayReturn]:
        """
        List returns by state.

        Args:
            db: SQLAlchemy Session
            state: Return state (OPEN, CLOSED)
            limit: Max number of results

        Returns:
            List[EbayReturn]: List of returns
        """
        returns = (
            db.query(EbayReturn)
            .filter(EbayReturn.state == state)
            .order_by(EbayReturn.creation_date.desc())
            .limit(limit)
            .all()
        )

        logger.debug(
            f"[EbayReturnRepository] list_by_state: state={state}, "
            f"returned={len(returns)}"
        )

        return returns

    @staticmethod
    def list_needs_action(db: Session, limit: int = 100) -> List[EbayReturn]:
        """
        List returns requiring seller action.

        Action-needed statuses:
        - RETURN_REQUESTED: Buyer requested return, awaiting decision
        - RETURN_WAITING_FOR_RMA: Awaiting RMA number
        - RETURN_ITEM_DELIVERED: Item received, awaiting refund

        Args:
            db: SQLAlchemy Session
            limit: Max number of results

        Returns:
            List[EbayReturn]: List of returns needing action
        """
        action_statuses = [
            "RETURN_REQUESTED",
            "RETURN_WAITING_FOR_RMA",
            "RETURN_ITEM_DELIVERED",
        ]

        returns = (
            db.query(EbayReturn)
            .filter(
                and_(
                    EbayReturn.state == "OPEN",
                    EbayReturn.status.in_(action_statuses),
                )
            )
            .order_by(EbayReturn.deadline_date.asc())  # Most urgent first
            .limit(limit)
            .all()
        )

        logger.debug(
            f"[EbayReturnRepository] list_needs_action: returned={len(returns)}"
        )

        return returns

    @staticmethod
    def list_past_deadline(db: Session, limit: int = 100) -> List[EbayReturn]:
        """
        List returns past their deadline.

        Args:
            db: SQLAlchemy Session
            limit: Max number of results

        Returns:
            List[EbayReturn]: List of returns past deadline
        """
        now = datetime.now(timezone.utc)

        returns = (
            db.query(EbayReturn)
            .filter(
                and_(
                    EbayReturn.state == "OPEN",
                    EbayReturn.deadline_date.isnot(None),
                    EbayReturn.deadline_date < now,
                )
            )
            .order_by(EbayReturn.deadline_date.asc())
            .limit(limit)
            .all()
        )

        logger.debug(
            f"[EbayReturnRepository] list_past_deadline: returned={len(returns)}"
        )

        return returns

    # =========================================================================
    # Aggregation Operations
    # =========================================================================

    @staticmethod
    def count_by_state(db: Session, state: str) -> int:
        """
        Count returns by state.

        Args:
            db: SQLAlchemy Session
            state: Return state (OPEN, CLOSED)

        Returns:
            int: Number of returns
        """
        count = (
            db.query(func.count(EbayReturn.id))
            .filter(EbayReturn.state == state)
            .scalar()
            or 0
        )

        logger.debug(
            f"[EbayReturnRepository] count_by_state: state={state}, count={count}"
        )

        return count

    @staticmethod
    def count_needs_action(db: Session) -> int:
        """
        Count returns needing seller action.

        Args:
            db: SQLAlchemy Session

        Returns:
            int: Number of returns needing action
        """
        action_statuses = [
            "RETURN_REQUESTED",
            "RETURN_WAITING_FOR_RMA",
            "RETURN_ITEM_DELIVERED",
        ]

        count = (
            db.query(func.count(EbayReturn.id))
            .filter(
                and_(
                    EbayReturn.state == "OPEN",
                    EbayReturn.status.in_(action_statuses),
                )
            )
            .scalar()
            or 0
        )

        logger.debug(
            f"[EbayReturnRepository] count_needs_action: count={count}"
        )

        return count

    @staticmethod
    def count_past_deadline(db: Session) -> int:
        """
        Count returns past their deadline.

        Args:
            db: SQLAlchemy Session

        Returns:
            int: Number of returns past deadline
        """
        now = datetime.now(timezone.utc)

        count = (
            db.query(func.count(EbayReturn.id))
            .filter(
                and_(
                    EbayReturn.state == "OPEN",
                    EbayReturn.deadline_date.isnot(None),
                    EbayReturn.deadline_date < now,
                )
            )
            .scalar()
            or 0
        )

        logger.debug(
            f"[EbayReturnRepository] count_past_deadline: count={count}"
        )

        return count

    @staticmethod
    def exists(db: Session, ebay_return_id: str) -> bool:
        """
        Check if a return exists by its eBay return ID.

        Args:
            db: SQLAlchemy Session
            ebay_return_id: eBay return ID (e.g., "5000012345")

        Returns:
            bool: True if exists, False otherwise
        """
        count = (
            db.query(func.count(EbayReturn.id))
            .filter(EbayReturn.return_id == ebay_return_id)
            .scalar()
            or 0
        )

        return count > 0
