"""
AiCreditPack Repository

Repository for managing AiCreditPack entities (CRUD operations).
Responsibility: Data access for ai_credit_packs (schema public).

Architecture:
- Repository pattern for DB isolation
- Standard CRUD operations
- Queries for Stripe checkout

Created: 2026-01-14
Author: Claude
"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.public.ai_credit_pack import AiCreditPack
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class AiCreditPackRepository:
    """
    Repository for managing AiCreditPack entities.

    Provides CRUD operations and specialized queries.
    All methods are static for ease of use.
    """

    @staticmethod
    def get_by_id(db: Session, pack_id: int) -> Optional[AiCreditPack]:
        """
        Retrieve an AiCreditPack by its primary key ID.

        Args:
            db: SQLAlchemy Session
            pack_id: Primary key ID

        Returns:
            AiCreditPack if found, None otherwise
        """
        stmt = select(AiCreditPack).where(AiCreditPack.id == pack_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_credits(db: Session, credits: int) -> Optional[AiCreditPack]:
        """
        Retrieve an active AiCreditPack by credits count.

        Args:
            db: SQLAlchemy Session
            credits: Number of credits (e.g., 25, 75, 200)

        Returns:
            AiCreditPack if found and active, None otherwise
        """
        stmt = select(AiCreditPack).where(
            AiCreditPack.credits == credits, AiCreditPack.is_active == True
        )
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def list_active(db: Session) -> List[AiCreditPack]:
        """
        List all active credit packs.

        Args:
            db: SQLAlchemy Session

        Returns:
            List of active AiCreditPack ordered by display_order
        """
        stmt = (
            select(AiCreditPack)
            .where(AiCreditPack.is_active == True)
            .order_by(AiCreditPack.display_order)
        )

        return db.execute(stmt).scalars().all()

    @staticmethod
    def list_all(db: Session, include_inactive: bool = False) -> List[AiCreditPack]:
        """
        List all credit packs (optionally including inactive).

        Args:
            db: SQLAlchemy Session
            include_inactive: Whether to include inactive packs

        Returns:
            List of AiCreditPack ordered by display_order
        """
        stmt = select(AiCreditPack).order_by(AiCreditPack.display_order)

        if not include_inactive:
            stmt = stmt.where(AiCreditPack.is_active == True)

        return db.execute(stmt).scalars().all()

    @staticmethod
    def create(db: Session, pack: AiCreditPack) -> AiCreditPack:
        """
        Create a new AiCreditPack.

        Args:
            db: SQLAlchemy Session
            pack: AiCreditPack entity to create

        Returns:
            Created AiCreditPack with ID populated
        """
        db.add(pack)
        db.commit()
        db.refresh(pack)

        logger.info(
            f"[AiCreditPackRepository] Created pack: {pack.credits} credits @ {pack.price}€"
        )

        return pack

    @staticmethod
    def update(db: Session, pack: AiCreditPack) -> AiCreditPack:
        """
        Update an existing AiCreditPack.

        Args:
            db: SQLAlchemy Session
            pack: AiCreditPack entity with updated values

        Returns:
            Updated AiCreditPack
        """
        db.commit()
        db.refresh(pack)

        logger.info(
            f"[AiCreditPackRepository] Updated pack: {pack.credits} credits @ {pack.price}€"
        )

        return pack

    @staticmethod
    def delete(db: Session, pack_id: int) -> bool:
        """
        Delete an AiCreditPack by ID (hard delete).

        Args:
            db: SQLAlchemy Session
            pack_id: Primary key ID

        Returns:
            True if deleted, False if not found
        """
        pack = AiCreditPackRepository.get_by_id(db, pack_id)

        if not pack:
            return False

        db.delete(pack)
        db.commit()

        logger.info(f"[AiCreditPackRepository] Deleted pack ID: {pack_id}")

        return True
