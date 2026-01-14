"""
Product AI Routes

Routes for AI-powered product features: image analysis.

Author: Claude
Date: 2025-12-09
Refactored: 2026-01-05 - Split from api/products.py
"""

from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from api.dependencies import get_user_db
from services.product_service import ProductService
from shared.ownership import ensure_user_owns_resource, ensure_can_modify
from shared.logging_setup import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    "/{product_id}/analyze-images",
    status_code=status.HTTP_200_OK,
)
async def analyze_product_images(
    product_id: int,
    user_db: tuple = Depends(get_user_db),
):
    """
    Analyse les images d'un produit avec Gemini Vision.

    Extrait automatiquement les attributs visibles sur les images
    (marque, couleur, catégorie, état, etc.) pour remplir le formulaire.

    Business Rules:
    - Authentification requise
    - Requiert au moins 1 image sur le produit
    - USER: peut uniquement analyser SES produits
    - ADMIN: peut analyser tous les produits
    - SUPPORT: lecture seule (ne peut pas analyser)
    - Vérifie les crédits IA avant analyse
    - Décrémente 1 crédit après analyse
    - Log dans AIGenerationLog

    Raises:
        400 BAD REQUEST: Si le produit n'a pas d'images
        402 PAYMENT REQUIRED: Si crédits insuffisants
        403 FORBIDDEN: Si USER essaie d'analyser le produit d'un autre ou si SUPPORT
        404 NOT FOUND: Si produit non trouvé
        401 UNAUTHORIZED: Si pas authentifié
        500 INTERNAL SERVER ERROR: Si erreur API Gemini
    """
    from schemas.ai_schemas import AIVisionAnalysisResponse
    from services.ai import AIVisionService
    from shared.config import settings
    from shared.exceptions import AIGenerationError, AIQuotaExceededError

    db, current_user = user_db

    logger.info(
        f"[API:products] analyze_images: user_id={current_user.id}, product_id={product_id}"
    )

    try:
        # SUPPORT ne peut pas analyser (lecture seule)
        ensure_can_modify(current_user, "produit")

        # Note: schema already configured via schema_translate_map in get_user_db()
        # No need to SET search_path manually

        # Récupérer le produit
        product = ProductService.get_product_by_id(db, product_id)

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id {product_id} not found",
            )

        # Vérifier ownership
        ensure_user_owns_resource(current_user, product, "produit", allow_support=False)

        # Vérifier qu'il y a des images
        if not product.images:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le produit n'a pas d'images à analyser.",
            )

        # Récupérer les limites de l'abonnement
        monthly_credits = 0
        max_images = 5  # Default for users without subscription
        # subscription_quota is always loaded via joinedload in get_current_user()
        if current_user.subscription_quota:
            monthly_credits = current_user.subscription_quota.ai_credits_monthly or 0
            max_images = current_user.subscription_quota.ai_max_images_per_analysis or 5

        # Analyser les images
        attributes, tokens_used, cost, images_analyzed = await AIVisionService.analyze_images(
            db=db,
            product=product,
            user_id=current_user.id,
            monthly_credits=monthly_credits,
            max_images=max_images,
        )

        logger.info(
            f"[API:products] analyze_images success: product_id={product_id}, "
            f"images={images_analyzed}, tokens={tokens_used}"
        )

        return AIVisionAnalysisResponse(
            attributes=attributes,
            model=settings.gemini_model,
            images_analyzed=images_analyzed,
            tokens_used=tokens_used,
            cost=cost,
            processing_time_ms=0,  # Will be set by service
        )

    except AIQuotaExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=str(e),
        )
    except AIGenerationError as e:
        logger.error(f"[API:products] analyze_images failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/analyze-images-direct",
    status_code=status.HTTP_200_OK,
)
async def analyze_images_direct(
    files: Annotated[list[UploadFile], File(description="Images to analyze")],
    user_db: tuple = Depends(get_user_db),
):
    """
    Analyse des images uploadées directement (sans produit existant).

    Utilisé pour la création de produit avec pré-remplissage IA.
    Permet d'analyser les images AVANT de créer le produit.

    Business Rules:
    - Authentification requise
    - Requiert au moins 1 image
    - Vérifie les crédits IA avant analyse
    - Décrémente 1 crédit après analyse
    - Log dans AIGenerationLog (sans product_id)

    Raises:
        400 BAD REQUEST: Si aucune image fournie
        402 PAYMENT REQUIRED: Si crédits insuffisants
        401 UNAUTHORIZED: Si pas authentifié
        500 INTERNAL SERVER ERROR: Si erreur API Gemini
    """
    from schemas.ai_schemas import AIVisionAnalysisResponse
    from services.ai import AIVisionService
    from shared.config import settings
    from shared.exceptions import AIGenerationError, AIQuotaExceededError

    db, current_user = user_db

    logger.info(
        f"[API:products] analyze_images_direct: user_id={current_user.id}, "
        f"files_count={len(files)}"
    )

    try:
        # Vérifier qu'il y a des fichiers
        if not files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Aucune image fournie pour l'analyse.",
            )

        # Filtrer les fichiers valides (images uniquement)
        valid_mime_types = {"image/jpeg", "image/png", "image/gif", "image/webp"}
        image_files: list[tuple[bytes, str]] = []

        for file in files:
            if file.content_type not in valid_mime_types:
                logger.warning(
                    f"[API:products] analyze_images_direct: "
                    f"Skipping invalid file type: {file.content_type}"
                )
                continue

            content = await file.read()
            if content:
                image_files.append((content, file.content_type))

        if not image_files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Aucune image valide fournie. Formats acceptés: JPEG, PNG, GIF, WebP.",
            )

        # Récupérer les limites de l'abonnement
        monthly_credits = 0
        max_images = 5  # Default for users without subscription
        # subscription_quota is always loaded via joinedload in get_current_user()
        if current_user.subscription_quota:
            monthly_credits = current_user.subscription_quota.ai_credits_monthly or 0
            max_images = current_user.subscription_quota.ai_max_images_per_analysis or 5

        # Limiter les images selon l'abonnement
        image_files_limited = image_files[:max_images]

        logger.info(
            f"[API:products] analyze_images_direct: limiting to {len(image_files_limited)}/{len(image_files)} images "
            f"(max_images={max_images} for user subscription)"
        )

        # Analyser les images
        attributes, tokens_used, cost, images_analyzed = await AIVisionService.analyze_images_direct(
            db=db,
            image_files=image_files_limited,
            user_id=current_user.id,
            monthly_credits=monthly_credits,
        )

        logger.info(
            f"[API:products] analyze_images_direct success: user_id={current_user.id}, "
            f"images={images_analyzed}, tokens={tokens_used}"
        )

        return AIVisionAnalysisResponse(
            attributes=attributes,
            model=settings.gemini_model,
            images_analyzed=images_analyzed,
            tokens_used=tokens_used,
            cost=cost,
            processing_time_ms=0,  # Set by service if needed
        )

    except AIQuotaExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=str(e),
        )
    except AIGenerationError as e:
        logger.error(f"[API:products] analyze_images_direct failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
