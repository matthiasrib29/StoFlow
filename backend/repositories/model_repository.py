"""Repository for Model data access."""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from models.public.model import Model


class ModelRepository:
    """Repository for Model data access."""

    def __init__(self, db: Session):
        self.db = db

    def find_by_brand_group_model(self, brand: str, group: str, model: str) -> Optional[Model]:
        """
        Find model by exact brand, group, and model name match.

        Args:
            brand: Brand name
            group: Group name
            model: Model name

        Returns:
            Model if found, None otherwise
        """
        stmt = select(Model).where(
            Model.brand == brand,
            Model.group_name == group,
            Model.model == model
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def find_by_brand_and_group(self, brand: str, group: str) -> list[Model]:
        """
        Find all models for a brand and group combination.

        Args:
            brand: Brand name
            group: Group name

        Returns:
            List of Model instances ordered by model name
        """
        stmt = select(Model).where(
            Model.brand == brand,
            Model.group_name == group
        ).order_by(Model.model)
        return list(self.db.execute(stmt).scalars().all())

    def create(self, model: Model) -> Model:
        """
        Create a new model entry.

        Args:
            model: Model instance to create

        Returns:
            The created Model with ID populated
        """
        self.db.add(model)
        self.db.flush()
        return model

    def get_all(self, limit: int = 100, offset: int = 0) -> list[Model]:
        """
        Get all models with pagination.

        Args:
            limit: Maximum number of results (default 100)
            offset: Number of results to skip (default 0)

        Returns:
            List of Model instances
        """
        stmt = select(Model).order_by(Model.created_at.desc()).limit(limit).offset(offset)
        return list(self.db.execute(stmt).scalars().all())

    def count(self) -> int:
        """
        Count total models.

        Returns:
            Total count of models
        """
        stmt = select(func.count(Model.id))
        return self.db.execute(stmt).scalar()
