"""
Admin Documentation API Endpoints

CRUD endpoints for managing documentation (admin only).

Author: Claude
Date: 2024-12-24
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.dependencies import require_admin
from shared.database import get_db
from shared.logging import setup_logging
from models.public.doc_category import DocCategory
from models.public.doc_article import DocArticle
from models.public.user import User
from schemas.docs_schemas import (
    DocCategoryCreate,
    DocCategoryUpdate,
    DocCategoryResponse,
    DocArticleCreate,
    DocArticleUpdate,
    DocArticleSummary,
    DocArticleDetail,
)

logger = setup_logging()

router = APIRouter(prefix="/admin/docs", tags=["admin-documentation"])


# ===== CATEGORY ENDPOINTS =====


@router.get("/categories", response_model=List[DocCategoryResponse])
async def admin_list_categories(
    include_inactive: bool = Query(False, description="Include inactive categories"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    List all categories (admin view).

    Unlike public endpoint, can include inactive categories.
    """
    logger.info(f"[API:admin_docs] list_categories: user_id={current_user.id}, include_inactive={include_inactive}")

    query = db.query(DocCategory)
    if not include_inactive:
        query = query.filter(DocCategory.is_active == True)

    categories = query.order_by(DocCategory.display_order).all()

    # ===== PERFORMANCE FIX (Phase 3.4 - 2026-01-12): Avoid N+1 queries =====
    # Count articles per category in a single query (instead of one query per category)
    article_counts = dict(
        db.query(DocArticle.category_id, func.count(DocArticle.id))
        .group_by(DocArticle.category_id)
        .all()
    )

    result = []
    for cat in categories:
        article_count = article_counts.get(cat.id, 0)
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

    logger.info(f"[API:admin_docs] list_categories: returning {len(result)} categories")
    return result


@router.post("/categories", response_model=DocCategoryResponse, status_code=201)
async def admin_create_category(
    category_data: DocCategoryCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Create a new documentation category.
    """
    logger.info(f"[API:admin_docs] create_category: user_id={current_user.id}, slug={category_data.slug}")

    # Check slug uniqueness
    existing = db.query(DocCategory).filter(DocCategory.slug == category_data.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="A category with this slug already exists")

    category = DocCategory(
        slug=category_data.slug,
        name=category_data.name,
        description=category_data.description,
        icon=category_data.icon,
        display_order=category_data.display_order,
        is_active=category_data.is_active,
    )

    db.add(category)
    db.commit()
    db.refresh(category)

    logger.info(f"[API:admin_docs] create_category: created id={category.id}")

    return DocCategoryResponse(
        id=category.id,
        slug=category.slug,
        name=category.name,
        description=category.description,
        icon=category.icon,
        display_order=category.display_order,
        is_active=category.is_active,
        article_count=0,
        created_at=category.created_at,
        updated_at=category.updated_at,
    )


@router.get("/categories/{category_id}", response_model=DocCategoryResponse)
async def admin_get_category(
    category_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Get a specific category by ID (admin view).
    """
    logger.info(f"[API:admin_docs] get_category: user_id={current_user.id}, category_id={category_id}")

    category = db.query(DocCategory).filter(DocCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    article_count = (
        db.query(DocArticle)
        .filter(DocArticle.category_id == category.id)
        .count()
    )

    return DocCategoryResponse(
        id=category.id,
        slug=category.slug,
        name=category.name,
        description=category.description,
        icon=category.icon,
        display_order=category.display_order,
        is_active=category.is_active,
        article_count=article_count,
        created_at=category.created_at,
        updated_at=category.updated_at,
    )


@router.put("/categories/{category_id}", response_model=DocCategoryResponse)
async def admin_update_category(
    category_id: int,
    category_data: DocCategoryUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Update a documentation category.
    """
    logger.info(f"[API:admin_docs] update_category: user_id={current_user.id}, category_id={category_id}")

    category = db.query(DocCategory).filter(DocCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Check slug uniqueness if changing
    if category_data.slug and category_data.slug != category.slug:
        existing = db.query(DocCategory).filter(DocCategory.slug == category_data.slug).first()
        if existing:
            raise HTTPException(status_code=400, detail="A category with this slug already exists")

    # Update fields
    update_data = category_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)

    db.commit()
    db.refresh(category)

    article_count = (
        db.query(DocArticle)
        .filter(DocArticle.category_id == category.id)
        .count()
    )

    logger.info(f"[API:admin_docs] update_category: updated id={category.id}")

    return DocCategoryResponse(
        id=category.id,
        slug=category.slug,
        name=category.name,
        description=category.description,
        icon=category.icon,
        display_order=category.display_order,
        is_active=category.is_active,
        article_count=article_count,
        created_at=category.created_at,
        updated_at=category.updated_at,
    )


@router.delete("/categories/{category_id}", status_code=204)
async def admin_delete_category(
    category_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Delete a documentation category.

    Warning: This will also delete all articles in the category (CASCADE).
    """
    logger.info(f"[API:admin_docs] delete_category: user_id={current_user.id}, category_id={category_id}")

    category = db.query(DocCategory).filter(DocCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    db.delete(category)
    db.commit()

    logger.info(f"[API:admin_docs] delete_category: deleted id={category_id}")


# ===== ARTICLE ENDPOINTS =====


@router.get("/articles", response_model=List[DocArticleSummary])
async def admin_list_articles(
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    include_inactive: bool = Query(False, description="Include inactive articles"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    List all articles (admin view).

    Can filter by category and include inactive articles.
    """
    logger.info(f"[API:admin_docs] list_articles: user_id={current_user.id}, category_id={category_id}")

    query = db.query(DocArticle)

    if category_id:
        query = query.filter(DocArticle.category_id == category_id)
    if not include_inactive:
        query = query.filter(DocArticle.is_active == True)

    articles = query.order_by(DocArticle.category_id, DocArticle.display_order).all()

    # ===== PERFORMANCE FIX (Phase 3.4 - 2026-01-12): Avoid N+1 queries =====
    # Load all categories in a single query (instead of one query per article)
    category_ids = {article.category_id for article in articles}
    categories_dict = {
        cat.id: cat
        for cat in db.query(DocCategory).filter(DocCategory.id.in_(category_ids)).all()
    }

    result = []
    for article in articles:
        category = categories_dict.get(article.category_id)
        result.append(
            DocArticleSummary(
                id=article.id,
                category_id=article.category_id,
                category_slug=category.slug if category else None,
                category_name=category.name if category else None,
                slug=article.slug,
                title=article.title,
                summary=article.summary,
                display_order=article.display_order,
                is_active=article.is_active,
                created_at=article.created_at,
                updated_at=article.updated_at,
            )
        )

    logger.info(f"[API:admin_docs] list_articles: returning {len(result)} articles")
    return result


@router.post("/articles", response_model=DocArticleDetail, status_code=201)
async def admin_create_article(
    article_data: DocArticleCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Create a new documentation article.
    """
    logger.info(f"[API:admin_docs] create_article: user_id={current_user.id}, slug={article_data.slug}")

    # Check category exists
    category = db.query(DocCategory).filter(DocCategory.id == article_data.category_id).first()
    if not category:
        raise HTTPException(status_code=400, detail="Category not found")

    # Check slug uniqueness
    existing = db.query(DocArticle).filter(DocArticle.slug == article_data.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="An article with this slug already exists")

    article = DocArticle(
        category_id=article_data.category_id,
        slug=article_data.slug,
        title=article_data.title,
        summary=article_data.summary,
        content=article_data.content,
        display_order=article_data.display_order,
        is_active=article_data.is_active,
    )

    db.add(article)
    db.commit()
    db.refresh(article)

    logger.info(f"[API:admin_docs] create_article: created id={article.id}")

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


@router.get("/articles/{article_id}", response_model=DocArticleDetail)
async def admin_get_article(
    article_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Get a specific article by ID (admin view, includes full content).
    """
    logger.info(f"[API:admin_docs] get_article: user_id={current_user.id}, article_id={article_id}")

    article = db.query(DocArticle).filter(DocArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    category = db.query(DocCategory).filter(DocCategory.id == article.category_id).first()

    return DocArticleDetail(
        id=article.id,
        category_id=article.category_id,
        category_slug=category.slug if category else None,
        category_name=category.name if category else None,
        slug=article.slug,
        title=article.title,
        summary=article.summary,
        content=article.content,
        display_order=article.display_order,
        is_active=article.is_active,
        created_at=article.created_at,
        updated_at=article.updated_at,
    )


@router.put("/articles/{article_id}", response_model=DocArticleDetail)
async def admin_update_article(
    article_id: int,
    article_data: DocArticleUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Update a documentation article.
    """
    logger.info(f"[API:admin_docs] update_article: user_id={current_user.id}, article_id={article_id}")

    article = db.query(DocArticle).filter(DocArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Check category exists if changing
    if article_data.category_id:
        category = db.query(DocCategory).filter(DocCategory.id == article_data.category_id).first()
        if not category:
            raise HTTPException(status_code=400, detail="Category not found")

    # Check slug uniqueness if changing
    if article_data.slug and article_data.slug != article.slug:
        existing = db.query(DocArticle).filter(DocArticle.slug == article_data.slug).first()
        if existing:
            raise HTTPException(status_code=400, detail="An article with this slug already exists")

    # Update fields
    update_data = article_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(article, field, value)

    db.commit()
    db.refresh(article)

    category = db.query(DocCategory).filter(DocCategory.id == article.category_id).first()

    logger.info(f"[API:admin_docs] update_article: updated id={article.id}")

    return DocArticleDetail(
        id=article.id,
        category_id=article.category_id,
        category_slug=category.slug if category else None,
        category_name=category.name if category else None,
        slug=article.slug,
        title=article.title,
        summary=article.summary,
        content=article.content,
        display_order=article.display_order,
        is_active=article.is_active,
        created_at=article.created_at,
        updated_at=article.updated_at,
    )


@router.delete("/articles/{article_id}", status_code=204)
async def admin_delete_article(
    article_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Delete a documentation article.
    """
    logger.info(f"[API:admin_docs] delete_article: user_id={current_user.id}, article_id={article_id}")

    article = db.query(DocArticle).filter(DocArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    db.delete(article)
    db.commit()

    logger.info(f"[API:admin_docs] delete_article: deleted id={article_id}")
