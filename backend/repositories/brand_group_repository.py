"""Repository for BrandGroup data access."""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from models.public.brand_group import BrandGroup


class BrandGroupRepository:
    """Repository for BrandGroup data access."""

    def __init__(self, db: Session):
        self.db = db

    def find_by_brand_and_group(self, brand: str, group: str) -> Optional[BrandGroup]:
        """
        Find brand group by exact brand and group name match.

        Args:
            brand: Brand name
            group: Group name

        Returns:
            BrandGroup if found, None otherwise
        """
        stmt = select(BrandGroup).where(
            BrandGroup.brand == brand,
            BrandGroup.group_name == group
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, brand_group: BrandGroup) -> BrandGroup:
        """
        Create a new brand group entry.

        Args:
            brand_group: BrandGroup instance to create

        Returns:
            The created BrandGroup with ID populated
        """
        self.db.add(brand_group)
        self.db.flush()  # Get ID without committing transaction
        return brand_group

    def get_all(self, limit: int = 100, offset: int = 0) -> list[BrandGroup]:
        """
        Get all brand groups with pagination.

        Args:
            limit: Maximum number of results (default 100)
            offset: Number of results to skip (default 0)

        Returns:
            List of BrandGroup instances
        """
        stmt = select(BrandGroup).order_by(BrandGroup.created_at.desc()).limit(limit).offset(offset)
        return list(self.db.execute(stmt).scalars().all())

    def count(self) -> int:
        """
        Count total brand groups.

        Returns:
            Total count of brand groups
        """
        stmt = select(func.count(BrandGroup.id))
        return self.db.execute(stmt).scalar()
