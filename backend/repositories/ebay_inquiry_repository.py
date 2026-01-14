"""
eBay Inquiry Repository

Repository for managing eBay INR inquiries (CRUD operations).
Responsibility: Data access for ebay_inquiries table (schema user_{id}).

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

from models.user.ebay_inquiry import EbayInquiry
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class EbayInquiryRepository:
    """
    Repository for managing EbayInquiry entities.

    Provides all CRUD operations and specialized queries.
    All methods are static for ease of use.
    """

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    @staticmethod
    def create(db: Session, inquiry: EbayInquiry) -> EbayInquiry:
        """
        Create a new eBay inquiry.

        Args:
            db: SQLAlchemy Session
            inquiry: EbayInquiry instance to create

        Returns:
            EbayInquiry: Created instance with ID assigned
        """
        db.add(inquiry)
        db.flush()  # Get ID without committing (caller manages transaction)

        logger.debug(
            f"[EbayInquiryRepository] Inquiry created: id={inquiry.id}, "
            f"inquiry_id={inquiry.inquiry_id}"
        )

        return inquiry

    @staticmethod
    def get_by_id(db: Session, inquiry_pk: int) -> Optional[EbayInquiry]:
        """
        Get an inquiry by its internal ID.

        Args:
            db: SQLAlchemy Session
            inquiry_pk: Internal inquiry ID

        Returns:
            EbayInquiry if found, None otherwise
        """
        return db.query(EbayInquiry).filter(EbayInquiry.id == inquiry_pk).first()

    @staticmethod
    def get_by_ebay_inquiry_id(db: Session, ebay_inquiry_id: str) -> Optional[EbayInquiry]:
        """
        Get an inquiry by its eBay inquiry ID (unique key).

        Args:
            db: SQLAlchemy Session
            ebay_inquiry_id: eBay inquiry ID (e.g., "5000012345")

        Returns:
            EbayInquiry if found, None otherwise
        """
        return (
            db.query(EbayInquiry)
            .filter(EbayInquiry.inquiry_id == ebay_inquiry_id)
            .first()
        )

    @staticmethod
    def get_by_order_id(db: Session, order_id: str) -> List[EbayInquiry]:
        """
        Get all inquiries for a specific order.

        Args:
            db: SQLAlchemy Session
            order_id: eBay order ID

        Returns:
            List of EbayInquiry instances
        """
        inquiries = (
            db.query(EbayInquiry)
            .filter(EbayInquiry.order_id == order_id)
            .order_by(EbayInquiry.creation_date.desc())
            .all()
        )

        logger.debug(
            f"[EbayInquiryRepository] get_by_order_id: order_id={order_id}, "
            f"returned={len(inquiries)}"
        )

        return inquiries

    @staticmethod
    def update(db: Session, inquiry: EbayInquiry) -> EbayInquiry:
        """
        Update an existing inquiry.

        Args:
            db: SQLAlchemy Session
            inquiry: EbayInquiry instance to update

        Returns:
            EbayInquiry: Updated instance
        """
        db.flush()

        logger.debug(
            f"[EbayInquiryRepository] Inquiry updated: id={inquiry.id}, "
            f"inquiry_id={inquiry.inquiry_id}"
        )

        return inquiry

    @staticmethod
    def delete(db: Session, inquiry: EbayInquiry) -> bool:
        """
        Delete an inquiry (hard delete).

        Args:
            db: SQLAlchemy Session
            inquiry: EbayInquiry instance to delete

        Returns:
            bool: True if deletion successful
        """
        db.delete(inquiry)
        db.flush()

        logger.debug(
            f"[EbayInquiryRepository] Inquiry deleted: id={inquiry.id}, "
            f"inquiry_id={inquiry.inquiry_id}"
        )

        return True

    # =========================================================================
    # Query Operations
    # =========================================================================

    @staticmethod
    def list_inquiries(
        db: Session,
        skip: int = 0,
        limit: int = 50,
        state: Optional[str] = None,
        status: Optional[str] = None,
        order_id: Optional[str] = None,
    ) -> Tuple[List[EbayInquiry], int]:
        """
        List inquiries with filters and pagination.

        Args:
            db: SQLAlchemy Session
            skip: Number of results to skip (pagination)
            limit: Max number of results
            state: Filter by state (OPEN, CLOSED)
            status: Filter by status
            order_id: Filter by order ID

        Returns:
            Tuple[List[EbayInquiry], int]: (list of inquiries, total count)
        """
        query = db.query(EbayInquiry)

        # Apply filters
        if state:
            query = query.filter(EbayInquiry.inquiry_state == state)

        if status:
            query = query.filter(EbayInquiry.inquiry_status == status)

        if order_id:
            query = query.filter(EbayInquiry.order_id == order_id)

        # Count total
        total = query.count()

        # Apply pagination and ordering
        inquiries = (
            query.order_by(EbayInquiry.creation_date.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        logger.debug(
            f"[EbayInquiryRepository] list_inquiries: skip={skip}, limit={limit}, "
            f"total={total}, returned={len(inquiries)}"
        )

        return inquiries, total

    @staticmethod
    def list_by_state(db: Session, state: str, limit: int = 100) -> List[EbayInquiry]:
        """
        List inquiries by state.

        Args:
            db: SQLAlchemy Session
            state: Inquiry state (OPEN, CLOSED)
            limit: Max number of results

        Returns:
            List[EbayInquiry]: List of inquiries
        """
        inquiries = (
            db.query(EbayInquiry)
            .filter(EbayInquiry.inquiry_state == state)
            .order_by(EbayInquiry.creation_date.desc())
            .limit(limit)
            .all()
        )

        logger.debug(
            f"[EbayInquiryRepository] list_by_state: state={state}, "
            f"returned={len(inquiries)}"
        )

        return inquiries

    @staticmethod
    def list_needs_action(db: Session, limit: int = 100) -> List[EbayInquiry]:
        """
        List inquiries requiring seller action.

        Action-needed statuses:
        - INR_WAITING_FOR_SELLER: Awaiting seller response

        Args:
            db: SQLAlchemy Session
            limit: Max number of results

        Returns:
            List[EbayInquiry]: List of inquiries needing action
        """
        action_statuses = [
            "INR_WAITING_FOR_SELLER",
        ]

        inquiries = (
            db.query(EbayInquiry)
            .filter(
                and_(
                    EbayInquiry.inquiry_state == "OPEN",
                    EbayInquiry.inquiry_status.in_(action_statuses),
                )
            )
            .order_by(EbayInquiry.respond_by_date.asc())  # Most urgent first
            .limit(limit)
            .all()
        )

        logger.debug(
            f"[EbayInquiryRepository] list_needs_action: returned={len(inquiries)}"
        )

        return inquiries

    @staticmethod
    def list_past_deadline(db: Session, limit: int = 100) -> List[EbayInquiry]:
        """
        List inquiries past their response deadline.

        Args:
            db: SQLAlchemy Session
            limit: Max number of results

        Returns:
            List[EbayInquiry]: List of inquiries past deadline
        """
        now = datetime.now(timezone.utc)

        inquiries = (
            db.query(EbayInquiry)
            .filter(
                and_(
                    EbayInquiry.inquiry_state == "OPEN",
                    EbayInquiry.respond_by_date.isnot(None),
                    EbayInquiry.respond_by_date < now,
                )
            )
            .order_by(EbayInquiry.respond_by_date.asc())
            .limit(limit)
            .all()
        )

        logger.debug(
            f"[EbayInquiryRepository] list_past_deadline: returned={len(inquiries)}"
        )

        return inquiries

    @staticmethod
    def list_escalated(db: Session, limit: int = 100) -> List[EbayInquiry]:
        """
        List inquiries that have been escalated to cases.

        Args:
            db: SQLAlchemy Session
            limit: Max number of results

        Returns:
            List[EbayInquiry]: List of escalated inquiries
        """
        inquiries = (
            db.query(EbayInquiry)
            .filter(EbayInquiry.inquiry_status == "INR_ESCALATED")
            .order_by(EbayInquiry.escalation_date.desc())
            .limit(limit)
            .all()
        )

        logger.debug(
            f"[EbayInquiryRepository] list_escalated: returned={len(inquiries)}"
        )

        return inquiries

    # =========================================================================
    # Aggregation Operations
    # =========================================================================

    @staticmethod
    def count_by_state(db: Session, state: str) -> int:
        """
        Count inquiries by state.

        Args:
            db: SQLAlchemy Session
            state: Inquiry state (OPEN, CLOSED)

        Returns:
            int: Number of inquiries
        """
        count = (
            db.query(func.count(EbayInquiry.id))
            .filter(EbayInquiry.inquiry_state == state)
            .scalar()
            or 0
        )

        logger.debug(
            f"[EbayInquiryRepository] count_by_state: state={state}, count={count}"
        )

        return count

    @staticmethod
    def count_needs_action(db: Session) -> int:
        """
        Count inquiries needing seller action.

        Args:
            db: SQLAlchemy Session

        Returns:
            int: Number of inquiries needing action
        """
        action_statuses = [
            "INR_WAITING_FOR_SELLER",
        ]

        count = (
            db.query(func.count(EbayInquiry.id))
            .filter(
                and_(
                    EbayInquiry.inquiry_state == "OPEN",
                    EbayInquiry.inquiry_status.in_(action_statuses),
                )
            )
            .scalar()
            or 0
        )

        logger.debug(
            f"[EbayInquiryRepository] count_needs_action: count={count}"
        )

        return count

    @staticmethod
    def count_past_deadline(db: Session) -> int:
        """
        Count inquiries past their response deadline.

        Args:
            db: SQLAlchemy Session

        Returns:
            int: Number of inquiries past deadline
        """
        now = datetime.now(timezone.utc)

        count = (
            db.query(func.count(EbayInquiry.id))
            .filter(
                and_(
                    EbayInquiry.inquiry_state == "OPEN",
                    EbayInquiry.respond_by_date.isnot(None),
                    EbayInquiry.respond_by_date < now,
                )
            )
            .scalar()
            or 0
        )

        logger.debug(
            f"[EbayInquiryRepository] count_past_deadline: count={count}"
        )

        return count

    @staticmethod
    def exists(db: Session, ebay_inquiry_id: str) -> bool:
        """
        Check if an inquiry exists by its eBay inquiry ID.

        Args:
            db: SQLAlchemy Session
            ebay_inquiry_id: eBay inquiry ID (e.g., "5000012345")

        Returns:
            bool: True if exists, False otherwise
        """
        count = (
            db.query(func.count(EbayInquiry.id))
            .filter(EbayInquiry.inquiry_id == ebay_inquiry_id)
            .scalar()
            or 0
        )

        return count > 0
