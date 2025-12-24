"""
Documentation Category Model

Table for organizing documentation articles into categories.

Business Rules:
- Categories group articles (e.g., "Guide", "FAQ")
- Each category has a unique slug for URLs
- display_order controls the order in navigation
- is_active allows hiding categories without deleting

Author: Claude
Date: 2024-12-24
"""

from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func
from sqlalchemy.orm import relationship, Mapped

from shared.database import Base

if TYPE_CHECKING:
    from models.public.doc_article import DocArticle


class DocCategory(Base):
    """
    Documentation category model.

    Groups articles for navigation (e.g., Guide, FAQ).
    Stored in public schema (shared across all tenants).
    """

    __tablename__ = "doc_categories"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="URL-friendly identifier (e.g., 'guide', 'faq')"
    )
    name = Column(
        String(100),
        nullable=False,
        comment="Display name (e.g., 'Guide d'utilisation')"
    )
    description = Column(
        Text,
        nullable=True,
        comment="Short description of the category"
    )
    icon = Column(
        String(50),
        nullable=True,
        comment="PrimeIcons class (e.g., 'pi-book')"
    )
    display_order = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Order in navigation (lower = first)"
    )
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether category is visible"
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    articles: Mapped[List["DocArticle"]] = relationship(
        "DocArticle",
        back_populates="category",
        cascade="all, delete-orphan",
        order_by="DocArticle.display_order"
    )

    def __repr__(self) -> str:
        return f"<DocCategory(slug='{self.slug}', name='{self.name}')>"

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "slug": self.slug,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "display_order": self.display_order,
            "is_active": self.is_active,
            "article_count": len(self.articles) if self.articles else 0,
        }
