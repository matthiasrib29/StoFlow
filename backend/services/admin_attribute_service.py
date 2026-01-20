"""
Admin Attribute Service

Service for managing reference data (brands, categories, colors, materials).
Provides generic CRUD operations for product attributes.
"""

from typing import Optional, List, Any, Type

from sqlalchemy.orm import Session
from sqlalchemy import or_

from models.public.brand import Brand
from models.public.category import Category
from models.public.color import Color
from models.public.material import Material
from shared.logging import get_logger

logger = get_logger(__name__)


class AdminAttributeService:
    """Service for admin attribute management operations."""

    # Mapping of attribute types to their models and primary keys
    ATTRIBUTE_CONFIG = {
        "brands": {
            "model": Brand,
            "pk_field": "name",
            "search_fields": ["name", "name_fr"],
            "name_field": "name",
        },
        "categories": {
            "model": Category,
            "pk_field": "name_en",
            "search_fields": ["name_en", "name_fr"],
            "name_field": "name_en",
        },
        "colors": {
            "model": Color,
            "pk_field": "name_en",
            "search_fields": ["name_en", "name_fr"],
            "name_field": "name_en",
        },
        "materials": {
            "model": Material,
            "pk_field": "name_en",
            "search_fields": ["name_en", "name_fr"],
            "name_field": "name_en",
        },
    }

    @classmethod
    def get_model(cls, attr_type: str) -> Type:
        """Get SQLAlchemy model for attribute type."""
        config = cls.ATTRIBUTE_CONFIG.get(attr_type)
        if not config:
            raise ValueError(f"Unknown attribute type: {attr_type}")
        return config["model"]

    @classmethod
    def get_pk_field(cls, attr_type: str) -> str:
        """Get primary key field name for attribute type."""
        config = cls.ATTRIBUTE_CONFIG.get(attr_type)
        if not config:
            raise ValueError(f"Unknown attribute type: {attr_type}")
        return config["pk_field"]

    @classmethod
    def get_name_field(cls, attr_type: str) -> str:
        """Get human-readable name field for attribute type."""
        config = cls.ATTRIBUTE_CONFIG.get(attr_type)
        if not config:
            raise ValueError(f"Unknown attribute type: {attr_type}")
        return config["name_field"]

    @staticmethod
    def list_attributes(
        db: Session,
        attr_type: str,
        skip: int = 0,
        limit: int = 50,
        search: Optional[str] = None,
    ) -> tuple[List[Any], int]:
        """
        List attributes with pagination and optional search.

        Args:
            db: SQLAlchemy session
            attr_type: Attribute type (brands, categories, colors, materials)
            skip: Number of records to skip
            limit: Maximum records to return
            search: Optional search term

        Returns:
            Tuple of (list of attributes, total count)
        """
        config = AdminAttributeService.ATTRIBUTE_CONFIG.get(attr_type)
        if not config:
            raise ValueError(f"Unknown attribute type: {attr_type}")

        model = config["model"]
        pk_field = config["pk_field"]
        query = db.query(model)

        # Apply search
        if search:
            search_term = f"%{search}%"
            search_filters = []
            for field_name in config["search_fields"]:
                field = getattr(model, field_name, None)
                if field is not None:
                    search_filters.append(field.ilike(search_term))
            if search_filters:
                query = query.filter(or_(*search_filters))

        # Get total count
        total = query.count()

        # Apply pagination
        pk_column = getattr(model, pk_field)
        items = query.order_by(pk_column).offset(skip).limit(limit).all()

        logger.debug(f"Admin list {attr_type}: found {total}, returning {len(items)}")
        return items, total

    @staticmethod
    def get_attribute(db: Session, attr_type: str, pk: str) -> Optional[Any]:
        """
        Get a single attribute by primary key.

        Args:
            db: SQLAlchemy session
            attr_type: Attribute type
            pk: Primary key value

        Returns:
            Attribute if found, None otherwise
        """
        model = AdminAttributeService.get_model(attr_type)
        pk_field = AdminAttributeService.get_pk_field(attr_type)
        pk_column = getattr(model, pk_field)

        return db.query(model).filter(pk_column == pk).first()

    @staticmethod
    def create_attribute(db: Session, attr_type: str, data: dict) -> Any:
        """
        Create a new attribute.

        Args:
            db: SQLAlchemy session
            attr_type: Attribute type
            data: Attribute data

        Returns:
            Created attribute

        Raises:
            ValueError: If attribute already exists
        """
        model = AdminAttributeService.get_model(attr_type)
        pk_field = AdminAttributeService.get_pk_field(attr_type)

        # Check if already exists
        pk_value = data.get(pk_field)
        if pk_value:
            existing = AdminAttributeService.get_attribute(db, attr_type, pk_value)
            if existing:
                raise ValueError(f"{attr_type[:-1].title()} '{pk_value}' already exists")

        # Create new attribute
        item = model(**data)
        db.add(item)
        db.commit()
        db.refresh(item)

        logger.info(f"Admin created {attr_type[:-1]}: {pk_value}")
        return item

    @staticmethod
    def update_attribute(db: Session, attr_type: str, pk: str, data: dict) -> Optional[Any]:
        """
        Update an attribute.

        Args:
            db: SQLAlchemy session
            attr_type: Attribute type
            pk: Primary key value
            data: Fields to update

        Returns:
            Updated attribute or None if not found
        """
        item = AdminAttributeService.get_attribute(db, attr_type, pk)
        if not item:
            return None

        pk_field = AdminAttributeService.get_pk_field(attr_type)

        # Update fields
        for key, value in data.items():
            # Cannot change primary key
            if key == pk_field:
                continue
            if hasattr(item, key) and value is not None:
                setattr(item, key, value)

        db.commit()
        db.refresh(item)

        logger.info(f"Admin updated {attr_type[:-1]}: {pk}")
        return item

    @staticmethod
    def delete_attribute(db: Session, attr_type: str, pk: str) -> bool:
        """
        Delete an attribute.

        Args:
            db: SQLAlchemy session
            attr_type: Attribute type
            pk: Primary key value

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If attribute is referenced by products
        """
        item = AdminAttributeService.get_attribute(db, attr_type, pk)
        if not item:
            return False

        # Note: Foreign key constraints in DB will prevent deletion
        # if attribute is in use. We let the DB handle this.
        try:
            db.delete(item)
            db.commit()
            logger.info(f"Admin deleted {attr_type[:-1]}: {pk}")
            return True
        except Exception as e:
            db.rollback()
            if "foreign key" in str(e).lower() or "fk_" in str(e).lower():
                raise ValueError(f"Cannot delete: {attr_type[:-1]} is used by products")
            raise

    @staticmethod
    def attribute_to_dict(item: Any, attr_type: str) -> dict:
        """
        Convert attribute model to dictionary.

        Args:
            item: SQLAlchemy model instance
            attr_type: Attribute type

        Returns:
            Dictionary representation
        """
        pk_field = AdminAttributeService.get_pk_field(attr_type)

        if attr_type == "brands":
            return {
                "pk": getattr(item, pk_field),
                "name": item.name,
                "name_fr": item.name_fr,
                "description": item.description,
                "vinted_id": item.vinted_id,
                "monitoring": item.monitoring,
                "sector_jeans": item.sector_jeans,
                "sector_jacket": item.sector_jacket,
            }
        elif attr_type == "categories":
            return {
                "pk": getattr(item, pk_field),
                "name_en": item.name_en,
                "name_fr": item.name_fr,
                "name_de": getattr(item, "name_de", None),
                "name_it": getattr(item, "name_it", None),
                "name_es": getattr(item, "name_es", None),
                "parent_category": getattr(item, "parent_category", None),
                "genders": getattr(item, "genders", None),
            }
        elif attr_type == "colors":
            return {
                "pk": getattr(item, pk_field),
                "name_en": item.name_en,
                "name_fr": item.name_fr,
                "name_de": getattr(item, "name_de", None),
                "name_it": getattr(item, "name_it", None),
                "name_es": getattr(item, "name_es", None),
                "name_nl": getattr(item, "name_nl", None),
                "name_pl": getattr(item, "name_pl", None),
                "hex_code": item.hex_code,
            }
        elif attr_type == "materials":
            return {
                "pk": getattr(item, pk_field),
                "name_en": item.name_en,
                "name_fr": item.name_fr,
                "name_de": getattr(item, "name_de", None),
                "name_it": getattr(item, "name_it", None),
                "name_es": getattr(item, "name_es", None),
                "name_nl": getattr(item, "name_nl", None),
                "name_pl": getattr(item, "name_pl", None),
                "vinted_id": getattr(item, "vinted_id", None),
            }
        else:
            raise ValueError(f"Unknown attribute type: {attr_type}")
