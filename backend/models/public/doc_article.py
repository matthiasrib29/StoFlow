"""
Documentation Article Model

Table for storing documentation articles with Markdown content.

Business Rules:
- Articles belong to a category (FK)
- Content is stored as Markdown
- Each article has a unique slug for URLs
- display_order controls order within category
- is_active allows hiding articles without deleting

Author: Claude
Date: 2024-12-24
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship, Mapped

from shared.database import Base

if TYPE_CHECKING:
    from models.public.doc_category import DocCategory


class DocArticle(Base):
    """
    Documentation article model.

    Stores article content as Markdown.
    Stored in public schema (shared across all tenants).
    """

    __tablename__ = "doc_articles"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(
        Integer,
        ForeignKey("public.doc_categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent category ID"
    )
    slug = Column(
        String(200),
        unique=True,
        nullable=False,
        index=True,
        comment="URL-friendly identifier (e.g., 'premiers-pas')"
    )
    title = Column(
        String(200),
        nullable=False,
        comment="Article title"
    )
    summary = Column(
        String(500),
        nullable=True,
        comment="Short excerpt for article cards"
    )
    content = Column(
        Text,
        nullable=False,
        comment="Article content in Markdown format"
    )
    display_order = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Order within category (lower = first)"
    )
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether article is visible"
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
    category: Mapped["DocCategory"] = relationship(
        "DocCategory",
        back_populates="articles"
    )

    def __repr__(self) -> str:
        return f"<DocArticle(slug='{self.slug}', title='{self.title}')>"

    def to_dict(self, include_content: bool = False) -> dict:
        """
        Convert to dictionary for API responses.

        Args:
            include_content: Whether to include full Markdown content.
                            False for list views, True for detail views.
        """
        result = {
            "id": self.id,
            "category_id": self.category_id,
            "category_slug": self.category.slug if self.category else None,
            "category_name": self.category.name if self.category else None,
            "slug": self.slug,
            "title": self.title,
            "summary": self.summary,
            "display_order": self.display_order,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_content:
            result["content"] = self.content
        return result
