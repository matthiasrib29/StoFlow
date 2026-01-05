"""
Product CRUD Routes

Basic CRUD operations for products: create, read, update, delete, status.

Author: Claude
Date: 2025-12-09
Refactored: 2026-01-05 - Split from api/products.py
"""

import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_user_db
from models.public.user import User, UserRole
from models.user.product import ProductStatus
from schemas.product_schemas import (
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
)
from services.product_service import ProductService
from shared.subscription_limits import check_product_limit
from shared.ownership import ensure_user_owns_resource, ensure_can_modify
from shared.logging_setup import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    product: ProductCreate,
    user_db: tuple = Depends(get_user_db),
) -> ProductResponse:
    """
    Crée un nouveau produit avec fonctionnalités PostEditFlet.

    Business Rules (Updated 2025-12-09):
    - Authentification requise (JWT token)
    - Vérifie la limite de produits (max_products) AVANT création
    - ADMIN: pas de limite (bypass)
    - Isolation multi-tenant (schema user_X)
    - ID auto-incrémenté comme identifiant unique (PostgreSQL SERIAL)
    - Prix calculé automatiquement si absent (PricingService)
    - Taille ajustée automatiquement selon dimensions (W{dim1}/L{dim6})
    - Auto-création size si manquante
    - Validation stricte brand (doit exister)
    - Status par défaut: DRAFT
    - Stock défaut: 1 (pièce unique)

    Raises:
        400 BAD REQUEST: Si attribut FK invalide
        401 UNAUTHORIZED: Si pas authentifié
        403 FORBIDDEN: Si limite de produits atteinte
    """
    db, current_user = user_db  # search_path already set by get_user_db

    logger.info(
        f"[API:products] create_product: user_id={current_user.id}, "
        f"category={product.category}, brand={product.brand}"
    )

    try:
        # SUPPORT ne peut pas créer de produits (lecture seule)
        ensure_can_modify(current_user, "produit")

        # Vérifier la limite de produits (sauf pour ADMIN)
        if current_user.role != UserRole.ADMIN:
            check_product_limit(current_user, db)

        # Create product with all PostEditFlet features
        db_product = ProductService.create_product(db, product, current_user.id)

        logger.info(
            f"[API:products] create_product success: user_id={current_user.id}, "
            f"product_id={db_product.id}"
        )

        return db_product
    except ValueError as e:
        logger.error(
            f"[API:products] create_product failed: user_id={current_user.id}, error={e}",
            exc_info=True
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=ProductListResponse, status_code=status.HTTP_200_OK)
def list_products(
    skip: int = Query(0, ge=0, description="Nombre de résultats à sauter (pagination)"),
    limit: int = Query(20, ge=1, le=100, description="Nombre max de résultats (max 100)"),
    status_filter: ProductStatus | None = Query(None, alias="status", description="Filtre par status"),
    category: str | None = Query(None, description="Filtre par catégorie"),
    brand: str | None = Query(None, description="Filtre par marque"),
    user_db: tuple = Depends(get_user_db),
) -> ProductListResponse:
    """
    Liste les produits avec filtres et pagination.

    Business Rules (Updated 2025-12-09):
    - Authentification requise
    - USER: ne voit que SES produits
    - ADMIN/SUPPORT: voient tous les produits
    - Ignore les produits supprimés (deleted_at NOT NULL)
    - Tri par défaut: created_at DESC (plus récents en premier)
    - Pagination: skip/limit (max 100 items par page)

    Query Parameters:
        - skip: Nombre de résultats à sauter (défaut: 0)
        - limit: Nombre max de résultats (défaut: 20, max: 100)
        - status: Filtre par status (DRAFT, PUBLISHED, SOLD, ARCHIVED)
        - category: Filtre par catégorie (ex: "Jeans")
        - brand: Filtre par marque (ex: "Levi's")
    """
    db, current_user = user_db  # search_path already set by get_user_db

    # Si USER, filtrer par user_id (isolation stricte)
    # Note: Le filtrage par user est géré automatiquement via le search_path (schema user_X)
    # Pas besoin de passer user_id explicitement
    products, total = ProductService.list_products(
        db, skip=skip, limit=limit, status=status_filter, category=category, brand=brand
    )

    # Calculer pagination
    page = (skip // limit) + 1
    total_pages = math.ceil(total / limit) if total > 0 else 1

    return ProductListResponse(
        products=products, total=total, page=page, page_size=limit, total_pages=total_pages
    )


@router.get("/{product_id}", response_model=ProductResponse, status_code=status.HTTP_200_OK)
def get_product(
    product_id: int,
    user_db: tuple = Depends(get_user_db),
) -> ProductResponse:
    """
    Récupère un produit par ID.

    Business Rules (Updated 2025-12-09):
    - Authentification requise
    - USER: peut uniquement accéder à SES produits
    - ADMIN/SUPPORT: peuvent accéder à tous les produits
    - Ignore les produits supprimés (deleted_at NOT NULL)

    Raises:
        403 FORBIDDEN: Si USER essaie d'accéder au produit d'un autre
        404 NOT FOUND: Si produit non trouvé ou supprimé
        401 UNAUTHORIZED: Si pas authentifié
    """
    db, current_user = user_db  # search_path already set by get_user_db

    product = ProductService.get_product_by_id(db, product_id)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found",
        )

    # Vérifier ownership (ADMIN/SUPPORT bypass, USER doit être propriétaire)
    ensure_user_owns_resource(current_user, product, "produit")

    return product


@router.put("/{product_id}", response_model=ProductResponse, status_code=status.HTTP_200_OK)
def update_product(
    product_id: int,
    product: ProductUpdate,
    user_db: tuple = Depends(get_user_db),
) -> ProductResponse:
    """
    Met à jour un produit.

    Business Rules (Updated 2025-12-09):
    - Authentification requise
    - USER: peut uniquement modifier SES produits
    - ADMIN: peut modifier tous les produits
    - SUPPORT: lecture seule (ne peut pas modifier)
    - Validation des FK si modifiés (brand, category, condition, etc.)
    - updated_at automatiquement mis à jour
    - Ne peut pas modifier un produit supprimé

    Raises:
        400 BAD REQUEST: Si attribut FK invalide
        403 FORBIDDEN: Si USER essaie de modifier le produit d'un autre ou si SUPPORT
        404 NOT FOUND: Si produit non trouvé ou supprimé
        401 UNAUTHORIZED: Si pas authentifié
    """
    db, current_user = user_db  # search_path already set by get_user_db

    logger.info(f"[API:products] update_product: user_id={current_user.id}, product_id={product_id}")

    try:
        # SUPPORT ne peut pas modifier (lecture seule)
        ensure_can_modify(current_user, "produit")

        # Récupérer le produit pour vérifier ownership
        existing_product = ProductService.get_product_by_id(db, product_id)

        if not existing_product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id {product_id} not found",
            )

        # Vérifier ownership (ADMIN peut, USER doit être propriétaire)
        ensure_user_owns_resource(current_user, existing_product, "produit", allow_support=False)

        # Mettre à jour
        updated_product = ProductService.update_product(db, product_id, product)

        logger.info(f"[API:products] update_product success: user_id={current_user.id}, product_id={product_id}")

        return updated_product
    except ValueError as e:
        logger.error(
            f"[API:products] update_product failed: user_id={current_user.id}, "
            f"product_id={product_id}, error={e}",
            exc_info=True
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    user_db: tuple = Depends(get_user_db),
):
    """
    Supprime un produit (soft delete).

    Business Rules (Updated 2025-12-09):
    - Authentification requise
    - USER: peut uniquement supprimer SES produits
    - ADMIN: peut supprimer tous les produits
    - SUPPORT: lecture seule (ne peut pas supprimer)
    - Soft delete: marque deleted_at au lieu de supprimer physiquement
    - Les images restent (pour historique)
    - Le produit devient invisible dans les listes

    Raises:
        403 FORBIDDEN: Si USER essaie de supprimer le produit d'un autre ou si SUPPORT
        404 NOT FOUND: Si produit non trouvé ou déjà supprimé
        401 UNAUTHORIZED: Si pas authentifié
    """
    db, current_user = user_db  # search_path already set by get_user_db

    logger.info(f"[API:products] delete_product: user_id={current_user.id}, product_id={product_id}")

    # SUPPORT ne peut pas supprimer (lecture seule)
    ensure_can_modify(current_user, "produit")

    # Récupérer le produit pour vérifier ownership
    product = ProductService.get_product_by_id(db, product_id)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found",
        )

    # Vérifier ownership (ADMIN peut, USER doit être propriétaire)
    ensure_user_owns_resource(current_user, product, "produit", allow_support=False)

    # Supprimer
    deleted = ProductService.delete_product(db, product_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found",
        )

    logger.info(f"[API:products] delete_product success: user_id={current_user.id}, product_id={product_id}")


@router.patch("/{product_id}/status", response_model=ProductResponse, status_code=status.HTTP_200_OK)
def update_product_status(
    product_id: int,
    new_status: ProductStatus = Query(..., description="Nouveau status"),
    user_db: tuple = Depends(get_user_db),
) -> ProductResponse:
    """
    Met à jour le status d'un produit.

    Business Rules (Updated 2025-12-09):
    - Authentification requise
    - USER: peut uniquement modifier le status de SES produits
    - ADMIN: peut modifier le status de tous les produits
    - SUPPORT: lecture seule (ne peut pas modifier)
    - Transitions MVP autorisées:
      - DRAFT → PUBLISHED
      - PUBLISHED → SOLD
      - PUBLISHED → ARCHIVED
      - SOLD → ARCHIVED
    - Autres transitions non autorisées pour MVP
    - published_at automatiquement rempli lors de la publication
    - sold_at automatiquement rempli lors de la vente

    Raises:
        400 BAD REQUEST: Si status non autorisé ou transition invalide
        403 FORBIDDEN: Si USER essaie de modifier le produit d'un autre ou si SUPPORT
        404 NOT FOUND: Si produit non trouvé
        401 UNAUTHORIZED: Si pas authentifié
    """
    db, current_user = user_db  # search_path already set by get_user_db

    try:
        # SUPPORT ne peut pas modifier le status (lecture seule)
        ensure_can_modify(current_user, "produit")

        # Récupérer le produit pour vérifier ownership
        product = ProductService.get_product_by_id(db, product_id)

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id {product_id} not found",
            )

        # Vérifier ownership (ADMIN peut, USER doit être propriétaire)
        ensure_user_owns_resource(current_user, product, "produit", allow_support=False)

        # Mettre à jour le status
        updated_product = ProductService.update_product_status(db, product_id, new_status)

        return updated_product
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
