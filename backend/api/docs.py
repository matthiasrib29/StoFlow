"""
Public Documentation API Endpoints

Endpoints that don't require authentication.
Used for displaying documentation to all users.

Author: Claude
Date: 2024-12-24
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from shared.database import get_db
from shared.logging import setup_logging
from models.public.doc_category import DocCategory
from models.public.doc_article import DocArticle
from schemas.docs_schemas import (
    DocCategoryResponse,
    DocArticleSummary,
    DocArticleDetail,
    DocCategoryWithArticles,
    DocsIndexResponse,
)

logger = setup_logging()

router = APIRouter(prefix="/docs", tags=["documentation"])


@router.get("", response_model=DocsIndexResponse)
async def get_documentation_index(db: Session = Depends(get_db)):
    """
    Get documentation index with all active categories and their articles.

    Returns categories ordered by display_order, each with their active articles.
    This endpoint is public and doesn't require authentication.
    """
    logger.info("[API:docs] get_documentation_index")

    categories = (
        db.query(DocCategory)
        .filter(DocCategory.is_active == True)
        .options(joinedload(DocCategory.articles))
        .order_by(DocCategory.display_order)
        .all()
    )

    result = []
    for cat in categories:
        # Filter active articles and sort by display_order
        active_articles = [
            DocArticleSummary(
                id=article.id,
                category_id=article.category_id,
                category_slug=cat.slug,
                category_name=cat.name,
                slug=article.slug,
                title=article.title,
                summary=article.summary,
                display_order=article.display_order,
                is_active=article.is_active,
                created_at=article.created_at,
                updated_at=article.updated_at,
            )
            for article in sorted(cat.articles, key=lambda x: x.display_order)
            if article.is_active
        ]

        result.append(
            DocCategoryWithArticles(
                id=cat.id,
                slug=cat.slug,
                name=cat.name,
                description=cat.description,
                icon=cat.icon,
                display_order=cat.display_order,
                articles=active_articles,
            )
        )

    logger.info(f"[API:docs] get_documentation_index: returning {len(result)} categories")
    return DocsIndexResponse(categories=result)


@router.get("/categories", response_model=List[DocCategoryResponse])
async def get_categories(db: Session = Depends(get_db)):
    """
    Get all active documentation categories.

    Returns categories ordered by display_order.
    This endpoint is public and doesn't require authentication.
    """
    logger.info("[API:docs] get_categories")

    categories = (
        db.query(DocCategory)
        .filter(DocCategory.is_active == True)
        .order_by(DocCategory.display_order)
        .all()
    )

    result = []
    for cat in categories:
        article_count = (
            db.query(DocArticle)
            .filter(DocArticle.category_id == cat.id, DocArticle.is_active == True)
            .count()
        )
        result.append(
            DocCategoryResponse(
                id=cat.id,
                slug=cat.slug,
                name=cat.name,
                description=cat.description,
                icon=cat.icon,
                display_order=cat.display_order,
                is_active=cat.is_active,
                article_count=article_count,
                created_at=cat.created_at,
                updated_at=cat.updated_at,
            )
        )

    logger.info(f"[API:docs] get_categories: returning {len(result)} categories")
    return result


@router.get("/{category_slug}", response_model=DocCategoryWithArticles)
async def get_category_articles(category_slug: str, db: Session = Depends(get_db)):
    """
    Get a category with all its active articles.

    Args:
        category_slug: The category slug (e.g., 'guide', 'faq')

    Returns:
        Category with its articles (summaries, not full content)

    Raises:
        404: Category not found or inactive
    """
    logger.info(f"[API:docs] get_category_articles: category_slug={category_slug}")

    category = (
        db.query(DocCategory)
        .filter(DocCategory.slug == category_slug, DocCategory.is_active == True)
        .options(joinedload(DocCategory.articles))
        .first()
    )

    if not category:
        logger.warning(f"[API:docs] Category not found: {category_slug}")
        raise HTTPException(status_code=404, detail="Category not found")

    # Filter active articles and sort by display_order
    active_articles = [
        DocArticleSummary(
            id=article.id,
            category_id=article.category_id,
            category_slug=category.slug,
            category_name=category.name,
            slug=article.slug,
            title=article.title,
            summary=article.summary,
            display_order=article.display_order,
            is_active=article.is_active,
            created_at=article.created_at,
            updated_at=article.updated_at,
        )
        for article in sorted(category.articles, key=lambda x: x.display_order)
        if article.is_active
    ]

    logger.info(f"[API:docs] get_category_articles: returning {len(active_articles)} articles")
    return DocCategoryWithArticles(
        id=category.id,
        slug=category.slug,
        name=category.name,
        description=category.description,
        icon=category.icon,
        display_order=category.display_order,
        articles=active_articles,
    )


@router.get("/{category_slug}/{article_slug}", response_model=DocArticleDetail)
async def get_article(category_slug: str, article_slug: str, db: Session = Depends(get_db)):
    """
    Get a specific article with full content.

    Args:
        category_slug: The category slug (e.g., 'guide')
        article_slug: The article slug (e.g., 'premiers-pas')

    Returns:
        Full article detail including Markdown content

    Raises:
        404: Article or category not found
    """
    logger.info(f"[API:docs] get_article: category={category_slug}, article={article_slug}")

    # First verify category exists and is active
    category = (
        db.query(DocCategory)
        .filter(DocCategory.slug == category_slug, DocCategory.is_active == True)
        .first()
    )

    if not category:
        logger.warning(f"[API:docs] Category not found: {category_slug}")
        raise HTTPException(status_code=404, detail="Category not found")

    # Get the article
    article = (
        db.query(DocArticle)
        .filter(
            DocArticle.slug == article_slug,
            DocArticle.category_id == category.id,
            DocArticle.is_active == True,
        )
        .first()
    )

    if not article:
        logger.warning(f"[API:docs] Article not found: {article_slug}")
        raise HTTPException(status_code=404, detail="Article not found")

    logger.info(f"[API:docs] get_article: returning article id={article.id}")
    return DocArticleDetail(
        id=article.id,
        category_id=article.category_id,
        category_slug=category.slug,
        category_name=category.name,
        slug=article.slug,
        title=article.title,
        summary=article.summary,
        content=article.content,
        display_order=article.display_order,
        is_active=article.is_active,
        created_at=article.created_at,
        updated_at=article.updated_at,
    )
