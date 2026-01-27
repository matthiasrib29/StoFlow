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
    BulkStatusUpdateRequest,
    BulkStatusUpdateResponse,
    BulkStatusUpdateResult,
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
)
from models.user.pending_action import PendingActionType
from services.product_service import ProductService
from services.pending_action_service import PendingActionService
from shared.subscription_limits import check_product_limit
from shared.access_control import ensure_user_owns_resource, ensure_can_modify
from shared.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


def _create_vinted_cleanup_pending_action(db: Session, product_id: int) -> None:
    """
    Create a DELETE_VINTED_LISTING pending action if the product has a Vinted listing.

    The user will need to confirm the pending action to trigger the actual deletion.

    Args:
        db: SQLAlchemy session (already configured for user schema)
        product_id: StoFlow product ID just marked SOLD
    """
    from models.user.vinted_product import VintedProduct

    vinted_product = db.query(VintedProduct).filter_by(product_id=product_id).first()
    if not vinted_product:
        return

    service = PendingActionService(db)
    service.create_pending_action(
        product_id=product_id,
        action_type=PendingActionType.DELETE_VINTED_LISTING,
        marketplace="vinted",
        reason=f"Product marked SOLD — Vinted listing {vinted_product.vinted_id} still active",
    )


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


@router.post("/create-draft", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_draft_for_upload(
    user_db: tuple = Depends(get_user_db),
) -> ProductResponse:
    """
    Crée un produit DRAFT minimal pour permettre l'upload instantané d'images.

    Ce endpoint est utilisé quand l'utilisateur drop des images AVANT de remplir
    le formulaire. Le produit créé a des valeurs minimales et sera complété plus tard.

    Business Rules:
    - Authentification requise (JWT token)
    - Vérifie la limite de produits (max_products) AVANT création
    - ADMIN: pas de limite (bypass)
    - Isolation multi-tenant (schema user_X)
    - Status: DRAFT
    - Title: "" (vide pour identifier les drafts auto-créés)
    - Stock: 1
    - Tous les autres champs: NULL

    Le cleanup automatique supprime les produits DRAFT avec title="" > 7 jours.

    Raises:
        401 UNAUTHORIZED: Si pas authentifié
        403 FORBIDDEN: Si limite de produits atteinte ou si SUPPORT
    """
    db, current_user = user_db

    logger.info(
        f"[API:products] create_draft_for_upload: user_id={current_user.id}"
    )

    try:
        # SUPPORT ne peut pas créer de produits (lecture seule)
        ensure_can_modify(current_user, "produit")

        # Vérifier la limite de produits (sauf pour ADMIN)
        if current_user.role != UserRole.ADMIN:
            check_product_limit(current_user, db)

        # Créer produit minimal en DRAFT
        db_product = ProductService.create_draft_for_upload(db, current_user.id)

        logger.info(
            f"[API:products] create_draft_for_upload success: user_id={current_user.id}, "
            f"product_id={db_product.id}"
        )

        return db_product
    except ValueError as e:
        logger.error(
            f"[API:products] create_draft_for_upload failed: user_id={current_user.id}, error={e}",
            exc_info=True
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=ProductListResponse, status_code=status.HTTP_200_OK)
def list_products(
    page: int = Query(1, ge=1, description="Numéro de page (1-indexed, défaut: 1)"),
    limit: int = Query(20, ge=1, le=100, description="Nombre max de résultats (max 100)"),
    status_filter: ProductStatus | None = Query(None, alias="status", description="Filtre par status"),
    category: str | None = Query(None, description="Filtre par catégorie"),
    brand: str | None = Query(None, description="Filtre par marque"),
    search: str | None = Query(None, description="Recherche par ID, titre ou marque"),
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
    - Pagination: page/limit (max 100 items par page)

    Query Parameters:
        - page: Numéro de page (1-indexed, défaut: 1)
        - limit: Nombre max de résultats (défaut: 20, max: 100)
        - status: Filtre par status (DRAFT, PUBLISHED, SOLD, ARCHIVED)
        - category: Filtre par catégorie (ex: "Jeans")
        - brand: Filtre par marque (ex: "Levi's")
    """
    db, current_user = user_db  # search_path already set by get_user_db

    # Convertir page (1-indexed) en skip (0-indexed)
    skip = (page - 1) * limit

    # Si USER, filtrer par user_id (isolation stricte)
    # Note: Le filtrage par user est géré automatiquement via le search_path (schema user_X)
    # Pas besoin de passer user_id explicitement
    products, total = ProductService.list_products(
        db, skip=skip, limit=limit, status=status_filter, category=category, brand=brand, search=search
    )

    # Calculer pagination
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


@router.patch("/bulk/status", response_model=BulkStatusUpdateResponse, status_code=status.HTTP_200_OK)
def bulk_update_status(
    request: BulkStatusUpdateRequest,
    user_db: tuple = Depends(get_user_db),
) -> BulkStatusUpdateResponse:
    """
    Met à jour le statut de plusieurs produits en une seule requête.

    Business Rules:
    - Authentification requise
    - USER: peut uniquement modifier SES produits
    - ADMIN: peut modifier tous les produits
    - SUPPORT: lecture seule (ne peut pas modifier)
    - Validation pour PUBLISHED: stock > 0, images >= 1
    - Transitions MVP autorisées (voir update_product_status)
    - Retourne succès/erreur pour chaque produit
    - SOLD: crée une Pending Action si le produit a un listing Vinted actif

    Raises:
        403 FORBIDDEN: Si SUPPORT essaie de modifier
        401 UNAUTHORIZED: Si pas authentifié
    """
    db, current_user = user_db

    logger.info(
        f"[API:products] bulk_update_status: user_id={current_user.id}, "
        f"product_count={len(request.product_ids)}, target_status={request.status}"
    )

    # SUPPORT ne peut pas modifier (lecture seule)
    ensure_can_modify(current_user, "produit")

    # Convert string status to enum
    status_map = {
        'draft': ProductStatus.DRAFT,
        'published': ProductStatus.PUBLISHED,
        'sold': ProductStatus.SOLD,
        'archived': ProductStatus.ARCHIVED,
    }
    target_status = status_map[request.status]

    results: list[BulkStatusUpdateResult] = []
    success_count = 0
    error_count = 0
    sold_product_ids: list[int] = []

    for product_id in request.product_ids:
        try:
            # Get product to verify ownership
            product = ProductService.get_product_by_id(db, product_id)

            if not product:
                results.append(BulkStatusUpdateResult(
                    product_id=product_id,
                    success=False,
                    error=f"Produit {product_id} non trouvé"
                ))
                error_count += 1
                continue

            # Verify ownership (ADMIN can modify all, USER only their own)
            try:
                ensure_user_owns_resource(current_user, product, "produit", allow_support=False)
            except HTTPException:
                results.append(BulkStatusUpdateResult(
                    product_id=product_id,
                    success=False,
                    error="Vous n'êtes pas propriétaire de ce produit"
                ))
                error_count += 1
                continue

            # Update status (validates transitions and publication requirements)
            ProductService.update_product_status(db, product_id, target_status)

            results.append(BulkStatusUpdateResult(
                product_id=product_id,
                success=True,
                error=None
            ))
            success_count += 1

            if target_status == ProductStatus.SOLD:
                sold_product_ids.append(product_id)

        except ValueError as e:
            results.append(BulkStatusUpdateResult(
                product_id=product_id,
                success=False,
                error=str(e)
            ))
            error_count += 1

    # Create pending actions for Vinted listings on products marked SOLD
    for pid in sold_product_ids:
        _create_vinted_cleanup_pending_action(db, pid)

    logger.info(
        f"[API:products] bulk_update_status completed: user_id={current_user.id}, "
        f"success={success_count}, errors={error_count}"
    )

    return BulkStatusUpdateResponse(
        total=len(request.product_ids),
        success_count=success_count,
        error_count=error_count,
        results=results
    )


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
    - SOLD: crée une Pending Action si le produit a un listing Vinted actif

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

        # Create pending action if product has a Vinted listing
        if new_status == ProductStatus.SOLD:
            _create_vinted_cleanup_pending_action(db, product_id)

        return updated_product
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
