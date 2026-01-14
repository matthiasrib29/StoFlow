"""
BrandGroup Repository

Repository for managing BrandGroup entities (CRUD operations).
Responsibility: Data access for brand_groups (schema public).

Architecture:
- Repository pattern for DB isolation
- Standard CRUD operations
- Queries for pricing algorithm

Created: 2026-01-12
Author: Claude
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.public.brand_group import BrandGroup
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class BrandGroupRepository:
    """
    Repository for managing BrandGroup entities.

    Provides CRUD operations and specialized queries.
    All methods are static for ease of use.
    """

    @staticmethod
    def create(db: Session, brand_group: BrandGroup) -> BrandGroup:
        """
        Create a new BrandGroup.

        Args:
            db: SQLAlchemy Session
            brand_group: BrandGroup instance to create

        Returns:
            BrandGroup: Created instance with assigned ID
        """
        db.add(brand_group)
        db.flush()  # Get ID without committing (caller manages transaction)

        logger.info(
            f"[BrandGroupRepository] BrandGroup created: "
            f"brand={brand_group.brand}, group={brand_group.group}, "
            f"base_price={brand_group.base_price}"
        )

        return brand_group

    @staticmethod
    def get_by_id(db: Session, brand_group_id: int) -> Optional[BrandGroup]:
        """
        Retrieve a BrandGroup by its ID.

        Args:
            db: SQLAlchemy Session
            brand_group_id: BrandGroup ID

        Returns:
            BrandGroup if found, None otherwise
        """
        stmt = select(BrandGroup).where(BrandGroup.id == brand_group_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_brand_and_group(
        db: Session, brand: str, group: str
    ) -> Optional[BrandGroup]:
        """
        Retrieve a BrandGroup by brand and group combination.

        Args:
            db: SQLAlchemy Session
            brand: Brand name
            group: Group name

        Returns:
            BrandGroup if found, None otherwise
        """
        stmt = select(BrandGroup).where(
            BrandGroup.brand == brand,
            BrandGroup.group == group
        )
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def update(db: Session, brand_group: BrandGroup) -> BrandGroup:
        """
        Update an existing BrandGroup.

        Args:
            db: SQLAlchemy Session
            brand_group: BrandGroup instance with updated values

        Returns:
            BrandGroup: Updated instance
        """
        db.flush()  # Persist changes without committing

        logger.info(
            f"[BrandGroupRepository] BrandGroup updated: "
            f"id={brand_group.id}, brand={brand_group.brand}, group={brand_group.group}"
        )

        return brand_group

    @staticmethod
    def delete(db: Session, brand_group: BrandGroup) -> None:
        """
        Delete a BrandGroup.

        Args:
            db: SQLAlchemy Session
            brand_group: BrandGroup instance to delete
        """
        db.delete(brand_group)
        db.flush()  # Apply deletion without committing

        logger.info(
            f"[BrandGroupRepository] BrandGroup deleted: "
            f"id={brand_group.id}, brand={brand_group.brand}, group={brand_group.group}"
        )
