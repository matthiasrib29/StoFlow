"""
eBay Category Mapping Model

Maps StoFlow categories to eBay category IDs.
Category IDs are global (same for all EU marketplaces: FR, GB, DE, ES, IT, NL, BE, PL).

Business Rules:
- Composite key: (my_category, my_gender) -> ebay_category_id
- Single table for all marketplaces (IDs are universal)
- Lookup: exact match on (category, gender)

Author: Claude
Date: 2025-12-22
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, Session, mapped_column

from shared.database import Base


class EbayCategoryMapping(Base):
    """
    Mapping from StoFlow categories to eBay category IDs.

    eBay category IDs are global - the same ID works for all EU marketplaces,
    only the category names are translated.

    Example:
        >>> mapping = EbayCategoryMapping(
        ...     my_category="jeans",
        ...     my_gender="men",
        ...     ebay_category_id=11483,
        ...     ebay_name_en="Jeans"
        ... )
    """

    __tablename__ = "category_mapping"
    __table_args__ = (
        UniqueConstraint(
            "my_category", "my_gender",
            name="uq_ebay_category_mapping"
        ),
        Index(
            "idx_ebay_category_lookup",
            "my_category", "my_gender"
        ),
        {"schema": "ebay"}
    )

    # Primary key
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )

    # Lookup key
    my_category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="StoFlow category name (e.g., 'jeans', 't-shirt', 'jacket')"
    )
    my_gender: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Gender: 'men' or 'women'"
    )

    # eBay mapping
    ebay_category_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="eBay category ID (global for all EU marketplaces)"
    )
    ebay_name_en: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="eBay category name in English"
    )

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    @classmethod
    def get_ebay_category(
        cls,
        session: Session,
        category: str,
        gender: str
    ) -> Optional["EbayCategoryMapping"]:
        """
        Get eBay category mapping for a given StoFlow category and gender.

        Args:
            session: SQLAlchemy session
            category: StoFlow category name (e.g., 'jeans', 't-shirt')
            gender: Gender ('men' or 'women')

        Returns:
            EbayCategoryMapping if found, None otherwise

        Examples:
            >>> mapping = EbayCategoryMapping.get_ebay_category(session, "jeans", "men")
            >>> mapping.ebay_category_id
            11483
        """
        return session.query(cls).filter(
            cls.my_category == category.lower(),
            cls.my_gender == gender.lower()
        ).first()

    @classmethod
    def get_ebay_category_id(
        cls,
        session: Session,
        category: str,
        gender: str
    ) -> Optional[int]:
        """
        Get eBay category ID directly.

        Args:
            session: SQLAlchemy session
            category: StoFlow category name
            gender: Gender ('men' or 'women')

        Returns:
            eBay category ID if found, None otherwise
        """
        mapping = cls.get_ebay_category(session, category, gender)
        return mapping.ebay_category_id if mapping else None

    @classmethod
    def get_all_mappings(cls, session: Session) -> dict:
        """
        Get all mappings as a dictionary.

        Args:
            session: SQLAlchemy session

        Returns:
            dict: {(category, gender): ebay_category_id}

        Examples:
            >>> mappings = EbayCategoryMapping.get_all_mappings(session)
            >>> mappings[("jeans", "men")]
            11483
        """
        results = session.query(cls).all()
        return {
            (m.my_category, m.my_gender): m.ebay_category_id
            for m in results
        }

    def __repr__(self) -> str:
        return (
            f"<EbayCategoryMapping("
            f"category='{self.my_category}', "
            f"gender='{self.my_gender}', "
            f"ebay_id={self.ebay_category_id}, "
            f"ebay_name='{self.ebay_name_en}'"
            f")>"
        )
