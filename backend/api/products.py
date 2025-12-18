"""
Product Routes

Routes API pour la gestion des produits.

Business Rules (Updated 2025-12-09):
- Authentification requise (JWT token) pour toutes les routes
- Isolation multi-tenant automatique via schema user_X
- ID auto-incrémenté comme identifiant unique, prix calculé automatiquement
- Status MVP: DRAFT, PUBLISHED, SOLD, ARCHIVED
- Pagination: max 100 items par page
"""

import math

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_user_db
from models.public.user import User, UserRole
from models.user.product import ProductStatus
from schemas.product_schemas import (
    ProductCreate,
    ProductImageResponse,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
)
from services.file_service import FileService
from services.product_service import ProductService
from shared.database import get_db
from shared.subscription_limits import check_product_limit
from shared.ownership import ensure_user_owns_resource, ensure_can_modify
from shared.logging_setup import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/products", tags=["Products"])


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


# ===== ROUTES IMAGES =====


@router.post(
    "/{product_id}/images",
    response_model=ProductImageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    display_order: int = Query(0, ge=0, description="Ordre d'affichage (0 = première image)"),
    user_db: tuple = Depends(get_user_db),
) -> ProductImageResponse:
    """
    Upload une image pour un produit.

    Business Rules (Updated 2025-12-09):
    - Authentification requise
    - USER: peut uniquement uploader des images pour SES produits
    - ADMIN: peut uploader pour tous les produits
    - SUPPORT: lecture seule (ne peut pas uploader)
    - Maximum 20 images par produit (limite Vinted)
    - Formats: jpg, jpeg, png
    - Taille max: 5MB
    - Stockage local: uploads/{user_id}/products/{product_id}/filename
    - Validation du format réel (anti-spoofing)

    Raises:
        400 BAD REQUEST: Si format/taille invalide ou limite atteinte
        403 FORBIDDEN: Si USER essaie d'uploader pour le produit d'un autre ou si SUPPORT
        404 NOT FOUND: Si produit non trouvé
        401 UNAUTHORIZED: Si pas authentifié
    """
    db, current_user = user_db  # search_path already set by get_user_db

    # SUPPORT ne peut pas uploader d'images (lecture seule)
    ensure_can_modify(current_user, "produit")

    # Vérifier que le produit existe
    product = ProductService.get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found",
        )

    # Vérifier ownership (ADMIN peut, USER doit être propriétaire)
    ensure_user_owns_resource(current_user, product, "produit", allow_support=False)

    # Récupérer user_id pour isolation du stockage
    user_id = current_user.id

    # Vérifier la limite de 20 images
    try:
        FileService.validate_image_count(db, product_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Sauvegarder l'image sur filesystem
    try:
        image_path = await FileService.save_product_image(user_id, product_id, file)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Créer l'entrée en BDD
    try:
        product_image = ProductService.add_image(db, product_id, image_path, display_order)
        return product_image
    except ValueError as e:
        # Si erreur BDD, supprimer le fichier uploadé
        FileService.delete_product_image(image_path)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{product_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product_image(
    product_id: int,
    image_id: int,
    user_db: tuple = Depends(get_user_db),
):
    """
    Supprime une image d'un produit.

    Business Rules (Updated 2025-12-09):
    - Authentification requise
    - USER: peut uniquement supprimer des images de SES produits
    - ADMIN: peut supprimer des images de tous les produits
    - SUPPORT: lecture seule (ne peut pas supprimer)
    - Suppression physique du fichier + entrée BDD
    - Vérifier que l'image appartient au produit

    Raises:
        403 FORBIDDEN: Si USER essaie de supprimer l'image d'un autre produit ou si SUPPORT
        404 NOT FOUND: Si image non trouvée
        401 UNAUTHORIZED: Si pas authentifié
    """
    db, current_user = user_db  # search_path already set by get_user_db

    # Récupérer l'image pour vérifier qu'elle appartient au produit
    from models.user.product_image import ProductImage

    image = db.query(ProductImage).filter(ProductImage.id == image_id).first()

    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Image with id {image_id} not found"
        )

    if image.product_id != product_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image {image_id} does not belong to product {product_id}",
        )

    # SUPPORT ne peut pas supprimer d'images (lecture seule)
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

    # Supprimer le fichier
    FileService.delete_product_image(image.image_path)

    # Supprimer l'entrée BDD
    deleted = ProductService.delete_image(db, image_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Image with id {image_id} not found"
        )


@router.put(
    "/{product_id}/images/reorder",
    response_model=list[ProductImageResponse],
    status_code=status.HTTP_200_OK,
)
def reorder_product_images(
    product_id: int,
    image_orders: dict[int, int],
    user_db: tuple = Depends(get_user_db),
) -> list[ProductImageResponse]:
    """
    Réordonne les images d'un produit.

    Business Rules (Updated 2025-12-09):
    - Authentification requise
    - USER: peut uniquement réordonner les images de SES produits
    - ADMIN: peut réordonner les images de tous les produits
    - SUPPORT: lecture seule (ne peut pas réordonner)
    - image_orders: {image_id: new_display_order}
    - Vérifie que toutes les images appartiennent au produit

    Request Body Example:
    {
        "1": 0,
        "2": 1,
        "3": 2
    }

    Raises:
        400 BAD REQUEST: Si une image n'appartient pas au produit
        403 FORBIDDEN: Si USER essaie de réordonner les images d'un autre produit ou si SUPPORT
        404 NOT FOUND: Si produit non trouvé
        401 UNAUTHORIZED: Si pas authentifié
    """
    db, current_user = user_db  # search_path already set by get_user_db

    # SUPPORT ne peut pas réordonner les images (lecture seule)
    ensure_can_modify(current_user, "produit")

    # Vérifier que le produit existe
    product = ProductService.get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found",
        )

    # Vérifier ownership (ADMIN peut, USER doit être propriétaire)
    ensure_user_owns_resource(current_user, product, "produit", allow_support=False)

    # Réordonner les images
    try:
        images = ProductService.reorder_images(db, product_id, image_orders)
        return images
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
