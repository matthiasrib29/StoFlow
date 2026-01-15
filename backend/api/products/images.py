"""
Product Images Routes

Routes for product image management: upload, delete, reorder.

Author: Claude
Date: 2025-12-09
Refactored: 2026-01-05 - Split from api/products.py
"""

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from api.dependencies import get_user_db
from schemas.product_schemas import ProductImageItem
from services.file_service import FileService
from services.product_service import ProductService
from shared.ownership import ensure_user_owns_resource, ensure_can_modify
from shared.logging_setup import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    "/{product_id}/images",
    response_model=ProductImageItem,
    status_code=status.HTTP_201_CREATED,
)
async def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    display_order: int | None = Query(None, ge=0, description="Ordre d'affichage (auto si non fourni)"),
    user_db: tuple = Depends(get_user_db),
) -> ProductImageItem:
    """
    Upload une image pour un produit.

    Business Rules (Updated 2026-01-15):
    - Authentification requise
    - USER: peut uniquement uploader des images pour SES produits
    - ADMIN: peut uploader pour tous les produits
    - SUPPORT: lecture seule (ne peut pas uploader)
    - Maximum 20 images par produit (limite Vinted)
    - Formats: jpg, jpeg, png
    - Taille max: 10MB (avant optimisation)
    - Stockage: Cloudflare R2
    - Images stockées en table product_images avec metadata (is_label, alt_text, tags, dimensions)

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

    # Sauvegarder l'image sur R2
    try:
        image_url = await FileService.save_product_image(user_id, product_id, file)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Ajouter en table product_images
    try:
        image_dict = ProductService.add_image(db, product_id, image_url, display_order)
        return ProductImageItem(**image_dict)
    except ValueError as e:
        # Si erreur BDD, supprimer le fichier uploadé sur R2
        await FileService.delete_product_image(image_url)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{product_id}/images", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product_image(
    product_id: int,
    image_url: str = Query(..., description="URL de l'image à supprimer"),
    user_db: tuple = Depends(get_user_db),
):
    """
    Supprime une image d'un produit par URL.

    Business Rules (Updated 2026-01-15):
    - Authentification requise
    - USER: peut uniquement supprimer des images de SES produits
    - ADMIN: peut supprimer des images de tous les produits
    - SUPPORT: lecture seule (ne peut pas supprimer)
    - Suppression du fichier R2 + entrée table product_images
    - Réordonnancement automatique des images restantes

    Query Parameters:
        - image_url: URL de l'image à supprimer (URL-encoded)

    Raises:
        403 FORBIDDEN: Si USER essaie de supprimer l'image d'un autre produit ou si SUPPORT
        404 NOT FOUND: Si image non trouvée
        401 UNAUTHORIZED: Si pas authentifié
    """
    db, current_user = user_db  # search_path already set by get_user_db

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

    # Vérifier que l'image existe dans le produit (using service, not JSONB)
    images = ProductService.get_images(db, product_id)
    if not any(img.get("url") == image_url for img in images):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image not found in product {product_id}",
        )

    # Supprimer le fichier R2
    await FileService.delete_product_image(image_url)

    # Supprimer l'entrée table product_images
    deleted = ProductService.delete_image(db, product_id, image_url)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image not found in product {product_id}",
        )


@router.put(
    "/{product_id}/images/reorder",
    response_model=list[ProductImageItem],
    status_code=status.HTTP_200_OK,
)
def reorder_product_images(
    product_id: int,
    ordered_urls: list[str],
    user_db: tuple = Depends(get_user_db),
) -> list[ProductImageItem]:
    """
    Réordonne les images d'un produit.

    Business Rules (Updated 2026-01-15):
    - Authentification requise
    - USER: peut uniquement réordonner les images de SES produits
    - ADMIN: peut réordonner les images de tous les produits
    - SUPPORT: lecture seule (ne peut pas réordonner)
    - ordered_urls: liste d'URLs dans le nouvel ordre souhaité
    - L'ordre dans la liste détermine le display_order (0, 1, 2, ...)
    - Vérifie que toutes les URLs appartiennent au produit

    Request Body Example:
    [
        "https://cdn.stoflow.io/1/products/5/abc.jpg",
        "https://cdn.stoflow.io/1/products/5/def.jpg",
        "https://cdn.stoflow.io/1/products/5/ghi.jpg"
    ]

    Raises:
        400 BAD REQUEST: Si une URL n'appartient pas au produit
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
        images = ProductService.reorder_images(db, product_id, ordered_urls)
        return [ProductImageItem(**img) for img in images]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
