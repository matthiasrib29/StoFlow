"""
Vinted Integration Routes

Routes for Vinted platform integration (test, import, publish, delete).

Business Rules (2025-12-06):
- Cookies fournis par le plugin browser
- Test connexion avant import/publish
- Isolation: produits importés dans schema user_X

Author: Claude
Date: 2025-12-17
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_current_user
from models.public.user import User
from services.vinted.vinted_adapter import VintedAdapter, test_vinted_connection
from shared.database import get_db
from shared.ownership import ensure_can_modify, ensure_user_owns_resource

from .schemas import (
    VintedConnectionResponse,
    VintedCookiesRequest,
    VintedImportRequest,
    VintedImportResponse,
    VintedPublishRequest,
    VintedPublishResponse,
)

router = APIRouter()


@router.post(
    "/vinted/test-connection",
    response_model=VintedConnectionResponse,
    status_code=status.HTTP_200_OK,
)
async def test_vinted_connection_endpoint(
    request: VintedCookiesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Teste la connexion à Vinted avec les cookies fournis.

    Business Rules:
    - Vérifie que les cookies sont valides
    - Retourne info utilisateur Vinted si connecté
    - Ne stocke PAS les cookies (test uniquement)

    Args:
        request: Cookies Vinted
        current_user: Utilisateur authentifié
        db: Session DB (pour potentielles futures utilisations)

    Returns:
        VintedConnectionResponse: Résultat du test
    """
    result = await test_vinted_connection(request.cookies)
    return result


@router.post(
    "/vinted/import", response_model=VintedImportResponse, status_code=status.HTTP_200_OK
)
async def import_vinted_products(
    request: VintedImportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Importe des produits depuis Vinted vers Stoflow.

    Business Rules (Updated: 2025-12-08):
    - Import ALL produits actifs si vinted_ids == None
    - Import uniquement produits spécifiques si vinted_ids fourni
    - Détection duplicatas via metadata.vinted_id
    - Télécharge images vers Stoflow CDN
    - Isolation: produits importés dans schema user_X de l'utilisateur authentifié

    Args:
        request: Cookies + IDs optionnels
        db: Session DB
        current_user: Utilisateur authentifié (depuis JWT token)

    Returns:
        VintedImportResponse: Résultat de l'import
    """
    async with VintedAdapter(request.cookies) as adapter:
        # Test connexion d'abord
        connection = await adapter.test_connection()
        if not connection["connected"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Vinted connection failed: {connection['error']}",
            )

        # Import - utiliser l'ID du user authentifié
        user_id = current_user.id

        if request.vinted_ids:
            # Import spécifique
            result = await adapter.import_specific_products(db, user_id, request.vinted_ids)
        else:
            # Import ALL
            result = await adapter.import_all_products(db, user_id)

        return result


@router.post(
    "/vinted/publish", response_model=VintedPublishResponse, status_code=status.HTTP_200_OK
)
async def publish_product_to_vinted(
    request: VintedPublishRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Publie un produit Stoflow sur Vinted.

    Business Rules:
    - Produit doit exister dans Stoflow
    - Catégorie doit être supportée par Vinted
    - Upload images automatique
    - Création listing avec mapping automatique
    - USER ne peut publier que SES produits, ADMIN peut tout publier

    Args:
        request: Cookies + product_id
        current_user: Utilisateur authentifié
        db: Session DB

    Returns:
        VintedPublishResponse: Résultat publication
    """
    # SUPPORT ne peut pas publier sur Vinted (lecture seule)
    ensure_can_modify(current_user, "produit")

    # Récupérer le produit Stoflow
    from services.product_service import ProductService

    product = ProductService.get_product_by_id(db, request.product_id)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {request.product_id} not found",
        )

    # Vérifier ownership (seul le propriétaire ou ADMIN peuvent publier)
    ensure_user_owns_resource(current_user, product, "produit", allow_support=False)

    # Convertir en dict pour l'adapter
    product_data = {
        "title": product.title,
        "description": product.description,
        "price": float(product.price),
        "brand": product.brand,
        "category": product.category,
        "condition": product.condition,
        "size_original": product.size_original,
        "color": product.color,
        "images": [],  # TODO: Récupérer images depuis product_images
    }

    async with VintedAdapter(request.cookies) as adapter:
        result = await adapter.publish_product(product_data)

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"]
            )

        return result


@router.delete("/vinted/{vinted_item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vinted_listing(
    vinted_item_id: int,
    cookies: dict[str, str],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Supprime (cache) un listing Vinted.

    Business Rules:
    - USER ne peut supprimer que SES listings, ADMIN peut tout supprimer
    - TODO: Ajouter vérification ownership via metadata.vinted_id

    Args:
        vinted_item_id: ID du listing Vinted
        cookies: Cookies Vinted
        current_user: Utilisateur authentifié
        db: Session DB

    Returns:
        204 No Content si succès
    """
    # TODO: Vérifier que le listing appartient à current_user
    # en cherchant dans product_metadata où vinted_id = vinted_item_id

    async with VintedAdapter(cookies) as adapter:
        result = await adapter.delete_product(vinted_item_id)

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"]
            )

    return None


@router.get("/vinted/stats", status_code=status.HTTP_200_OK)
async def get_vinted_stats(
    cookies: dict[str, str],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Récupère les stats de l'utilisateur Vinted.

    Business Rules:
    - USER peut consulter SES propres stats, ADMIN peut voir toutes les stats

    Args:
        cookies: Cookies Vinted
        current_user: Utilisateur authentifié
        db: Session DB

    Returns:
        dict: Stats Vinted
    """
    async with VintedAdapter(cookies) as adapter:
        stats = await adapter.get_user_stats()
        return stats
