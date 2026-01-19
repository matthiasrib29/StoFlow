"""
Text Generator API Routes

REST API endpoints for generating SEO-optimized titles and descriptions.
Uses ProductTextGeneratorService (pure Python templates, no LLM).

Endpoints:
- POST /products/text/generate - Generate from existing product
- POST /products/text/preview - Preview from raw attributes

Architecture:
- Service layer pattern: route delegates to ProductTextGeneratorService
- Dependency injection for DB session + authentication
- Multi-tenant isolation via get_user_db()

Created: 2026-01-13
Author: Claude
"""

import time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_user_db
from models.public.user import User
from models.user.product import Product
from schemas.text_generator import (
    TextGenerateInput,
    TextGeneratorOutput,
    TextPreviewInput,
)
from services.product_text_generator import ProductTextGeneratorService
from shared.logging_setup import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/products/text", tags=["Text Generation"])


@router.post(
    "/generate",
    response_model=TextGeneratorOutput,
    status_code=status.HTTP_200_OK,
    summary="Generate text for existing product",
    description="Generates SEO titles and descriptions for a product already in the database"
)
async def generate_text(
    input: TextGenerateInput,
    db_user: tuple[Session, User] = Depends(get_user_db),
    current_user: User = Depends(get_current_user)
) -> TextGeneratorOutput:
    """
    Generate SEO titles and descriptions for an existing product.

    Fetches product from database, generates all title formats and description styles.
    Optionally filters to specific format/style if requested.

    Args:
        input: TextGenerateInput with product_id and optional format/style filters
        db_user: Database session with user schema set
        current_user: Authenticated user

    Returns:
        TextGeneratorOutput with generated titles and descriptions

    Raises:
        HTTPException 404: Product not found
        HTTPException 500: Service error
    """
    db, user = db_user
    start_time = time.time()

    logger.info(
        "[API:text_generator] Generate text request",
        extra={
            "user_id": user.id,
            "product_id": input.product_id,
            "title_format": input.title_format,
            "description_style": input.description_style
        }
    )

    # Fetch product from database
    product = db.query(Product).filter(
        Product.id == input.product_id,
        Product.deleted_at.is_(None)
    ).first()

    if not product:
        logger.warning(
            "[API:text_generator] Product not found",
            extra={
                "user_id": user.id,
                "product_id": input.product_id
            }
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {input.product_id} not found"
        )

    try:
        # Generate all texts
        result = ProductTextGeneratorService.generate_all(product)

        # Filter by specific format if requested
        if input.title_format is not None:
            format_keys = {
                1: "minimaliste",
                2: "standard_vinted",
                3: "seo_mots_cles",
                4: "vintage_collectionneur",
                5: "technique_professionnel"
            }
            key = format_keys.get(input.title_format)
            if key and key in result["titles"]:
                result["titles"] = {key: result["titles"][key]}

        # Filter by specific style if requested
        if input.description_style is not None:
            style_keys = {
                1: "catalogue_structure",
                2: "descriptif_redige",
                3: "fiche_technique",
                4: "vendeur_pro",
                5: "visuel_emoji"
            }
            key = style_keys.get(input.description_style)
            if key and key in result["descriptions"]:
                result["descriptions"] = {key: result["descriptions"][key]}

        # Log success
        elapsed_time = time.time() - start_time
        logger.info(
            "[API:text_generator] Generate text successful",
            extra={
                "user_id": user.id,
                "product_id": input.product_id,
                "elapsed_time_ms": round(elapsed_time * 1000, 2),
                "titles_count": len(result["titles"]),
                "descriptions_count": len(result["descriptions"])
            }
        )

        return TextGeneratorOutput(**result)

    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(
            f"[API:text_generator] Generate text failed: {e}",
            exc_info=True,
            extra={
                "user_id": user.id,
                "product_id": input.product_id,
                "elapsed_time_ms": round(elapsed_time * 1000, 2)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating text"
        )


@router.post(
    "/preview",
    response_model=TextGeneratorOutput,
    status_code=status.HTTP_200_OK,
    summary="Preview text from raw attributes",
    description="Generates SEO titles and descriptions from raw product attributes (before save)"
)
async def preview_text(
    input: TextPreviewInput,
    current_user: User = Depends(get_current_user)
) -> TextGeneratorOutput:
    """
    Preview SEO titles and descriptions from raw attributes.

    Used for previewing generated text in the product creation/edit form
    before saving to database. No DB fetch required.

    Args:
        input: TextPreviewInput with raw product attributes
        current_user: Authenticated user (no DB access needed)

    Returns:
        TextGeneratorOutput with generated titles and descriptions

    Raises:
        HTTPException 500: Service error
    """
    start_time = time.time()

    logger.info(
        "[API:text_generator] Preview text request",
        extra={
            "user_id": current_user.id,
            "brand": input.brand,
            "category": input.category
        }
    )

    try:
        # Convert input to dict for preview
        attributes = input.model_dump(exclude_none=True)

        # Generate preview
        result = ProductTextGeneratorService.generate_preview(attributes)

        # Log success
        elapsed_time = time.time() - start_time
        logger.info(
            "[API:text_generator] Preview text successful",
            extra={
                "user_id": current_user.id,
                "elapsed_time_ms": round(elapsed_time * 1000, 2),
                "titles_count": len(result["titles"]),
                "descriptions_count": len(result["descriptions"])
            }
        )

        return TextGeneratorOutput(**result)

    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(
            f"[API:text_generator] Preview text failed: {e}",
            exc_info=True,
            extra={
                "user_id": current_user.id,
                "elapsed_time_ms": round(elapsed_time * 1000, 2)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating preview"
        )
