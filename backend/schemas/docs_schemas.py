"""
Documentation Schemas

Pydantic schemas for documentation API request/response validation.

Author: Claude
Date: 2024-12-24
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator
import re


# ===== DOC CATEGORY SCHEMAS =====


class DocCategoryCreate(BaseModel):
    """Schema for creating a documentation category."""

    slug: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="URL-friendly identifier (lowercase, hyphens allowed)"
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Display name"
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Short description"
    )
    icon: Optional[str] = Field(
        None,
        max_length=50,
        description="PrimeIcons class (e.g., 'pi-book')"
    )
    display_order: int = Field(
        default=0,
        ge=0,
        description="Order in navigation (lower = first)"
    )
    is_active: bool = Field(
        default=True,
        description="Whether category is visible"
    )

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Validate slug format (lowercase, alphanumeric, hyphens only)."""
        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError("Slug must contain only lowercase letters, numbers, and hyphens")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "slug": "guide",
                "name": "Guide d'utilisation",
                "description": "Apprenez à utiliser Stoflow",
                "icon": "pi-book",
                "display_order": 0,
                "is_active": True
            }
        }
    }


class DocCategoryUpdate(BaseModel):
    """Schema for updating a documentation category."""

    slug: Optional[str] = Field(None, min_length=1, max_length=100)
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    icon: Optional[str] = Field(None, max_length=50)
    display_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: Optional[str]) -> Optional[str]:
        """Validate slug format if provided."""
        if v is not None and not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError("Slug must contain only lowercase letters, numbers, and hyphens")
        return v


class DocCategoryResponse(BaseModel):
    """Schema for category response."""

    id: int
    slug: str
    name: str
    description: Optional[str]
    icon: Optional[str]
    display_order: int
    is_active: bool
    article_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ===== DOC ARTICLE SCHEMAS =====


class DocArticleCreate(BaseModel):
    """Schema for creating a documentation article."""

    category_id: int = Field(
        ...,
        gt=0,
        description="Parent category ID"
    )
    slug: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="URL-friendly identifier"
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Article title"
    )
    summary: Optional[str] = Field(
        None,
        max_length=500,
        description="Short excerpt for article cards"
    )
    content: str = Field(
        ...,
        min_length=1,
        description="Article content in Markdown format"
    )
    display_order: int = Field(
        default=0,
        ge=0,
        description="Order within category"
    )
    is_active: bool = Field(
        default=True,
        description="Whether article is visible"
    )

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Validate slug format."""
        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError("Slug must contain only lowercase letters, numbers, and hyphens")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "category_id": 1,
                "slug": "premiers-pas",
                "title": "Premiers pas avec Stoflow",
                "summary": "Découvrez comment démarrer avec Stoflow",
                "content": "# Premiers pas\n\nBienvenue sur Stoflow!",
                "display_order": 0,
                "is_active": True
            }
        }
    }


class DocArticleUpdate(BaseModel):
    """Schema for updating a documentation article."""

    category_id: Optional[int] = Field(None, gt=0)
    slug: Optional[str] = Field(None, min_length=1, max_length=200)
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    summary: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = Field(None, min_length=1)
    display_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: Optional[str]) -> Optional[str]:
        """Validate slug format if provided."""
        if v is not None and not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError("Slug must contain only lowercase letters, numbers, and hyphens")
        return v


class DocArticleSummary(BaseModel):
    """Schema for article summary (list views)."""

    id: int
    category_id: int
    category_slug: Optional[str]
    category_name: Optional[str]
    slug: str
    title: str
    summary: Optional[str]
    display_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocArticleDetail(BaseModel):
    """Schema for article detail (includes full content)."""

    id: int
    category_id: int
    category_slug: Optional[str]
    category_name: Optional[str]
    slug: str
    title: str
    summary: Optional[str]
    content: str
    display_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ===== COMBINED RESPONSE SCHEMAS =====


class DocCategoryWithArticles(BaseModel):
    """Schema for category with its articles (for documentation index)."""

    id: int
    slug: str
    name: str
    description: Optional[str]
    icon: Optional[str]
    display_order: int
    articles: List[DocArticleSummary]

    model_config = {"from_attributes": True}


class DocsIndexResponse(BaseModel):
    """Schema for documentation index (all categories with articles)."""

    categories: List[DocCategoryWithArticles]
