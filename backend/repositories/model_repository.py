"""
Model Repository

Repository for managing Model entities (CRUD operations).
Responsibility: Data access for models (schema public).

Architecture:
- Repository pattern for DB isolation
- Standard CRUD operations
- Queries for pricing algorithm

Created: 2026-01-12
Author: Claude
"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.public.model import Model
from shared.logging import get_logger

logger = get_logger(__name__)


class ModelRepository:
    """
    Repository for managing Model entities.

    Provides CRUD operations and specialized queries.
    All methods are static for ease of use.
    """

    @staticmethod
    def create(db: Session, model: Model) -> Model:
        """
        Create a new Model.

        Args:
            db: SQLAlchemy Session
            model: Model instance to create

        Returns:
            Model: Created instance with assigned ID
        """
        db.add(model)
        db.flush()  # Get ID without committing (caller manages transaction)

        logger.info(
            f"[ModelRepository] Model created: "
            f"brand={model.brand}, group={model.group}, name={model.name}, "
            f"coefficient={model.coefficient}"
        )

        return model

    @staticmethod
    def get_by_id(db: Session, model_id: int) -> Optional[Model]:
        """
        Retrieve a Model by its ID.

        Args:
            db: SQLAlchemy Session
            model_id: Model ID

        Returns:
            Model if found, None otherwise
        """
        stmt = select(Model).where(Model.id == model_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_brand_group_and_name(
        db: Session, brand: str, group: str, name: str
    ) -> Optional[Model]:
        """
        Retrieve a Model by brand, group, and name combination.

        Args:
            db: SQLAlchemy Session
            brand: Brand name
            group: Group name
            name: Model name

        Returns:
            Model if found, None otherwise
        """
        stmt = select(Model).where(
            Model.brand == brand,
            Model.group == group,
            Model.name == name
        )
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_all_by_brand_and_group(
        db: Session, brand: str, group: str
    ) -> List[Model]:
        """
        Retrieve all Models for a brand and group combination.

        Args:
            db: SQLAlchemy Session
            brand: Brand name
            group: Group name

        Returns:
            List of Models
        """
        stmt = select(Model).where(
            Model.brand == brand,
            Model.group == group
        ).order_by(Model.name)
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def update(db: Session, model: Model) -> Model:
        """
        Update an existing Model.

        Args:
            db: SQLAlchemy Session
            model: Model instance with updated values

        Returns:
            Model: Updated instance
        """
        db.flush()  # Persist changes without committing

        logger.info(
            f"[ModelRepository] Model updated: "
            f"id={model.id}, brand={model.brand}, group={model.group}, name={model.name}"
        )

        return model

    @staticmethod
    def delete(db: Session, model: Model) -> None:
        """
        Delete a Model.

        Args:
            db: SQLAlchemy Session
            model: Model instance to delete
        """
        db.delete(model)
        db.flush()  # Apply deletion without committing

        logger.info(
            f"[ModelRepository] Model deleted: "
            f"id={model.id}, brand={model.brand}, group={model.group}, name={model.name}"
        )
