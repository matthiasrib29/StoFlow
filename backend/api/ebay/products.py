"""
eBay Products API Routes

Endpoints for eBay product management:
- List imported eBay products
- Get single eBay product
- Import products from eBay
- Sync single product

Author: Claude
Date: 2025-12-19
"""

from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_user_db
from models.public.user import User
from models.user.ebay_product import EbayProduct
from services.ebay.ebay_importer import EbayImporter
from shared.database import SessionLocal, get_db, set_user_schema
from shared.logging_setup import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/ebay/products", tags=["eBay Products"])


# ===== SCHEMAS =====

class EbayProductResponse(BaseModel):
    """Response schema for eBay product."""

    id: int
    ebay_sku: str
    product_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    currency: str = "EUR"
    brand: Optional[str] = None
    size: Optional[str] = None
    color: Optional[str] = None
    condition: Optional[str] = None
    quantity: int = 1
    marketplace_id: str = "EBAY_FR"
    ebay_listing_id: Optional[int] = None
    status: str = "active"
    image_urls: Optional[list[str]] = None
    image_url: Optional[str] = None  # First image for preview
    ebay_listing_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_with_parsed_images(cls, obj):
        """Create response with parsed image_urls JSON."""
        import json
        data = {
            "id": obj.id,
            "ebay_sku": obj.ebay_sku,
            "product_id": obj.product_id,
            "title": obj.title,
            "description": obj.description,
            "price": obj.price,
            "currency": obj.currency or "EUR",
            "brand": obj.brand,
            "size": obj.size,
            "color": obj.color,
            "condition": obj.condition,
            "quantity": obj.quantity or 1,
            "marketplace_id": obj.marketplace_id or "EBAY_FR",
            "ebay_listing_id": obj.ebay_listing_id,
            "status": obj.status or "active",
            "image_urls": None,
            "image_url": None,
            "ebay_listing_url": None,
        }
        # Parse image_urls from JSON string
        if obj.image_urls:
            try:
                parsed_urls = json.loads(obj.image_urls)
                data["image_urls"] = parsed_urls
                # Set first image as preview
                if parsed_urls and len(parsed_urls) > 0:
                    data["image_url"] = parsed_urls[0]
            except (json.JSONDecodeError, TypeError):
                data["image_urls"] = None
        # Build eBay listing URL if listing_id exists
        if obj.ebay_listing_id:
            data["ebay_listing_url"] = f"https://www.ebay.fr/itm/{obj.ebay_listing_id}"
        return cls(**data)


class EbayProductListResponse(BaseModel):
    """Response schema for eBay products list."""

    items: list[EbayProductResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ImportRequest(BaseModel):
    """Request schema for import."""

    marketplace_id: str = "EBAY_FR"


class ImportResponse(BaseModel):
    """Response schema for import."""

    imported: int
    updated: int
    skipped: int
    errors: int
    details: list[dict]


class SyncResponse(BaseModel):
    """Response schema for sync."""

    success: bool
    product: Optional[EbayProductResponse] = None
    error: Optional[str] = None


class EnrichRequest(BaseModel):
    """Request schema for enrichment."""

    batch_size: int = 100
    only_without_price: bool = True


class EnrichResponse(BaseModel):
    """Response schema for enrichment."""

    enriched: int
    errors: int
    remaining: int
    details: list[dict]


class RefreshAspectsResponse(BaseModel):
    """Response schema for aspects refresh."""

    updated: int
    errors: int
    remaining: int


# ===== BACKGROUND TASKS =====


def enrich_products_in_background(user_id: int, marketplace_id: str = "EBAY_FR"):
    """
    Enrichit les produits eBay en arrière-plan après l'import.

    Cette fonction est exécutée en arrière-plan par FastAPI BackgroundTasks.
    Elle crée sa propre session DB pour éviter les conflits.

    Args:
        user_id: ID de l'utilisateur
        marketplace_id: Marketplace eBay
    """
    db = SessionLocal()
    try:
        set_user_schema(db, user_id)

        logger.info(f"Starting background enrichment for user {user_id}")

        importer = EbayImporter(
            db=db,
            user_id=user_id,
            marketplace_id=marketplace_id,
        )

        # Enrichir tous les produits sans prix (par batches)
        total_enriched = 0
        total_errors = 0
        remaining = 1  # Initial value to start loop

        while remaining > 0:
            result = importer.enrich_products_batch(
                limit=50,  # Process 50 products at a time
                only_without_price=True,
            )

            total_enriched += result["enriched"]
            total_errors += result["errors"]
            remaining = result["remaining"]

            logger.info(
                f"Background enrichment progress for user {user_id}: "
                f"enriched={total_enriched}, errors={total_errors}, remaining={remaining}"
            )

            # If no more products to enrich, break
            if remaining == 0:
                break

        logger.info(
            f"Background enrichment completed for user {user_id}: "
            f"total_enriched={total_enriched}, total_errors={total_errors}"
        )

    except Exception as e:
        logger.error(f"Background enrichment failed for user {user_id}: {e}", exc_info=True)
    finally:
        db.close()


# ===== ENDPOINTS =====

@router.get("", response_model=EbayProductListResponse)
async def list_ebay_products(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    marketplace_id: Optional[str] = Query(None, description="Filter by marketplace"),
    search: Optional[str] = Query(None, description="Search in title"),
    user_db: tuple = Depends(get_user_db),
):
    """
    Liste les produits eBay importés.

    Args:
        page: Numéro de page (1-indexed)
        page_size: Nombre d'items par page (max 100)
        status: Filtre par statut (active, inactive, sold, ended)
        marketplace_id: Filtre par marketplace (EBAY_FR, EBAY_GB, etc.)
        search: Recherche dans le titre
        user_db: (Session DB, User) avec schema isolé

    Returns:
        EbayProductListResponse: Liste paginée des produits
    """
    db, current_user = user_db

    # Build query
    query = db.query(EbayProduct)

    # Apply filters
    if status:
        query = query.filter(EbayProduct.status == status)

    if marketplace_id:
        query = query.filter(EbayProduct.marketplace_id == marketplace_id)

    if search:
        query = query.filter(EbayProduct.title.ilike(f"%{search}%"))

    # Get total count
    total = query.count()

    # Calculate pagination
    total_pages = (total + page_size - 1) // page_size
    offset = (page - 1) * page_size

    # Fetch items
    items = query.order_by(EbayProduct.created_at.desc()).offset(offset).limit(page_size).all()

    return EbayProductListResponse(
        items=[EbayProductResponse.from_orm_with_parsed_images(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{product_id}", response_model=EbayProductResponse)
async def get_ebay_product(
    product_id: int,
    user_db: tuple = Depends(get_user_db),
):
    """
    Récupère un produit eBay par ID.

    Args:
        product_id: ID du produit eBay
        user_db: (Session DB, User) avec schema isolé

    Returns:
        EbayProductResponse: Détails du produit
    """
    db, current_user = user_db

    product = db.query(EbayProduct).filter(EbayProduct.id == product_id).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"eBay product {product_id} not found",
        )

    return EbayProductResponse.from_orm_with_parsed_images(product)


@router.post("/import", response_model=ImportResponse)
async def import_ebay_products(
    background_tasks: BackgroundTasks,
    request: ImportRequest = Body(default=ImportRequest()),
    user_db: tuple = Depends(get_user_db),
):
    """
    Importe les produits depuis eBay Inventory API.

    Récupère tous les inventory items de l'utilisateur et les stocke
    dans la table ebay_products. Ensuite, lance automatiquement
    l'enrichissement en arrière-plan pour récupérer les prix.

    Args:
        background_tasks: FastAPI background tasks
        request: Paramètres d'import (marketplace_id)
        user_db: (Session DB, User) avec schema isolé

    Returns:
        ImportResponse: Résultat de l'import
    """
    db, current_user = user_db

    try:
        importer = EbayImporter(
            db=db,
            user_id=current_user.id,
            marketplace_id=request.marketplace_id,
        )

        result = importer.import_all_products()

        logger.info(
            f"eBay import for user {current_user.id}: "
            f"imported={result['imported']}, updated={result['updated']}, "
            f"errors={result['errors']}"
        )

        # Lancer l'enrichissement en arrière-plan pour récupérer les prix
        background_tasks.add_task(
            enrich_products_in_background,
            user_id=current_user.id,
            marketplace_id=request.marketplace_id,
        )

        logger.info(
            f"Background enrichment task scheduled for user {current_user.id}"
        )

        return ImportResponse(**result)

    except Exception as e:
        logger.error(f"eBay import failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}",
        )


@router.post("/enrich", response_model=EnrichResponse)
async def enrich_ebay_products(
    request: EnrichRequest = Body(default=EnrichRequest()),
    user_db: tuple = Depends(get_user_db),
):
    """
    Enrichit les produits eBay avec les données des offers (prix, listing, etc.).

    Cette opération récupère les prix et autres infos depuis l'API Offers
    pour les produits qui n'ont pas encore ces données.

    Args:
        request: Paramètres d'enrichissement (batch_size, only_without_price)
        user_db: (Session DB, User) avec schema isolé

    Returns:
        EnrichResponse: Résultat de l'enrichissement
    """
    db, current_user = user_db

    try:
        importer = EbayImporter(
            db=db,
            user_id=current_user.id,
        )

        result = importer.enrich_products_batch(
            limit=request.batch_size,
            only_without_price=request.only_without_price,
        )

        logger.info(
            f"eBay enrichment for user {current_user.id}: "
            f"enriched={result['enriched']}, errors={result['errors']}, "
            f"remaining={result['remaining']}"
        )

        return EnrichResponse(**result)

    except Exception as e:
        logger.error(f"eBay enrichment failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Enrichment failed: {str(e)}",
        )


@router.post("/refresh-aspects", response_model=RefreshAspectsResponse)
async def refresh_ebay_aspects(
    batch_size: int = Query(100, ge=1, le=1000, description="Batch size"),
    user_db: tuple = Depends(get_user_db),
):
    """
    Met à jour les aspects (brand, color, size, material) des produits existants.

    Utile pour corriger les produits importés avant la mise à jour multi-langue.
    Ne fait pas d'appel API eBay, utilise les données déjà stockées.

    Args:
        batch_size: Nombre de produits à traiter (max 1000)
        user_db: (Session DB, User) avec schema isolé

    Returns:
        RefreshAspectsResponse: Résultat de la mise à jour
    """
    db, current_user = user_db

    try:
        importer = EbayImporter(
            db=db,
            user_id=current_user.id,
        )

        result = importer.refresh_aspects_batch(limit=batch_size)

        logger.info(
            f"eBay aspects refresh for user {current_user.id}: "
            f"updated={result['updated']}, errors={result['errors']}, "
            f"remaining={result['remaining']}"
        )

        return RefreshAspectsResponse(**result)

    except Exception as e:
        logger.error(f"eBay aspects refresh failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Refresh failed: {str(e)}",
        )


@router.post("/{sku}/sync", response_model=SyncResponse)
async def sync_ebay_product(
    sku: str,
    marketplace_id: str = Query("EBAY_FR", description="Marketplace ID"),
    user_db: tuple = Depends(get_user_db),
):
    """
    Synchronise un seul produit eBay par SKU.

    Args:
        sku: SKU eBay du produit
        marketplace_id: Marketplace ID
        user_db: (Session DB, User) avec schema isolé

    Returns:
        SyncResponse: Résultat de la synchronisation
    """
    db, current_user = user_db

    try:
        importer = EbayImporter(
            db=db,
            user_id=current_user.id,
            marketplace_id=marketplace_id,
        )

        product = importer.sync_single_product(sku)

        if product:
            return SyncResponse(
                success=True,
                product=EbayProductResponse.from_orm_with_parsed_images(product),
            )
        else:
            return SyncResponse(
                success=False,
                error=f"Product with SKU {sku} not found on eBay",
            )

    except Exception as e:
        logger.error(f"eBay sync failed for SKU {sku}: {e}")
        return SyncResponse(
            success=False,
            error=str(e),
        )


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ebay_product(
    product_id: int,
    user_db: tuple = Depends(get_user_db),
):
    """
    Supprime un produit eBay de la base Stoflow.

    Note: Ne supprime PAS le produit sur eBay, seulement en local.

    Args:
        product_id: ID du produit eBay
        user_db: (Session DB, User) avec schema isolé
    """
    db, current_user = user_db

    product = db.query(EbayProduct).filter(EbayProduct.id == product_id).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"eBay product {product_id} not found",
        )

    db.delete(product)
    db.commit()


@router.get("/stats/summary")
async def get_ebay_stats(
    user_db: tuple = Depends(get_user_db),
):
    """
    Récupère les statistiques des produits eBay.

    Args:
        user_db: (Session DB, User) avec schema isolé

    Returns:
        dict: Statistiques (total, par status, par marketplace)
    """
    db, current_user = user_db

    # Total products
    total = db.query(EbayProduct).count()

    # By status
    status_counts = {}
    for status_value in ["active", "inactive", "sold", "ended"]:
        count = db.query(EbayProduct).filter(EbayProduct.status == status_value).count()
        status_counts[status_value] = count

    # By marketplace
    marketplace_counts = {}
    marketplaces = db.query(EbayProduct.marketplace_id).distinct().all()
    for (marketplace,) in marketplaces:
        count = db.query(EbayProduct).filter(EbayProduct.marketplace_id == marketplace).count()
        marketplace_counts[marketplace] = count

    return {
        "total": total,
        "by_status": status_counts,
        "by_marketplace": marketplace_counts,
    }
