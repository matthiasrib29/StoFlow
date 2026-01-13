"""
eBay Products API Routes

Endpoints for eBay product management:
- List imported eBay products
- Get single eBay product
- Import products from eBay (with inline enrichment)
- Enrich products with offers data
- Delete local eBay product
- Get eBay stats summary

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
from shared.database import SessionLocal
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


def _run_enrichment_in_background(user_id: int, marketplace_id: str):
    """
    Execute enrichment in background after import completes.
    """
    from sqlalchemy import text

    schema_name = f"user_{user_id}"
    db = SessionLocal()
    try:
        # Use schema_translate_map for ORM queries (survives commit/rollback)
        db = db.execution_options(schema_translate_map={"tenant": schema_name})
        # Also set search_path for text() queries
        db.execute(text(f"SET search_path TO {schema_name}, public"))

        importer = EbayImporter(
            db=db,
            user_id=user_id,
            marketplace_id=marketplace_id,
        )

        # Enrich all products without price
        result = importer.enrich_products_batch(limit=50000, only_without_price=True)

        logger.info(
            f"[Background Enrich] eBay enrichment for user {user_id}: "
            f"enriched={result['enriched']}, errors={result['errors']}, "
            f"remaining={result['remaining']}"
        )

    except Exception as e:
        logger.error(f"[Background Enrich] eBay enrichment failed for user {user_id}: {e}")

    finally:
        db.close()


def _update_job_progress(db, job_id: int, user_id: int, progress_data: dict):
    """Update job progress in database."""
    from sqlalchemy import text
    # Note: schema already configured via schema_translate_map or SET search_path
    db.execute(
        text("UPDATE marketplace_jobs SET result_data = :data WHERE id = :job_id"),
        {"data": str(progress_data).replace("'", '"'), "job_id": job_id}
    )
    db.commit()


def _enrich_products_parallel(importer, products: list, db, schema_name, max_workers: int = 10) -> int:
    """
    Enrich products with offers data in parallel.

    API calls are made in parallel threads, but DB writes happen in main thread
    (SQLAlchemy sessions are not thread-safe).

    Args:
        importer: EbayImporter instance
        products: List of EbayProduct objects to enrich
        db: Database session
        schema_name: User schema name
        max_workers: Number of parallel workers (default 10)

    Returns:
        int: Number of products successfully enriched
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from sqlalchemy import text

    if not products:
        return 0

    # IMPORTANT: Pre-fetch access token BEFORE parallel threads
    # This ensures token refresh (which does db.commit) happens in main thread
    # SQLAlchemy sessions are NOT thread-safe!
    # Note: schema_translate_map persists across commits - no need to re-SET
    try:
        _ = importer.offer_client.get_access_token()
        logger.debug("[Enrich Parallel] Token pre-fetched")
    except Exception as e:
        logger.warning(f"[Enrich Parallel] Token pre-fetch failed: {e}")

    # Build SKU to product mapping
    sku_to_product = {p.ebay_sku: p for p in products}
    skus = list(sku_to_product.keys())

    def fetch_offer_for_sku(sku: str):
        """Fetch offer for a SKU (thread-safe - only API call, no DB)."""
        try:
            offers = importer.fetch_offers_for_sku(sku)
            return (sku, offers)
        except Exception as e:
            logger.warning(f"Failed to fetch offer for SKU {sku}: {e}")
            return (sku, None)

    # Collect results from parallel API calls
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_offer_for_sku, sku): sku for sku in skus}

        for future in as_completed(futures):
            try:
                sku, offers = future.result()
                if offers:
                    results.append((sku, offers))
            except Exception as e:
                logger.warning(f"Error fetching offer: {e}")

    # Apply results in main thread (thread-safe DB access)
    enriched_count = 0
    for sku, offers in results:
        product = sku_to_product.get(sku)
        if product and offers:
            _apply_offer_to_product(product, offers, importer.marketplace_id)
            enriched_count += 1

    # Commit all enrichments at once
    # Note: schema_translate_map persists - no need to re-SET search_path
    db.commit()

    return enriched_count


def _apply_offer_to_product(product, offers: list, marketplace_id: str):
    """Apply offer data to a product."""
    from shared.datetime_utils import utc_now

    if not offers:
        return

    # Select best offer (prefer configured marketplace)
    selected_offer = None
    for offer in offers:
        if offer.get("marketplaceId") == marketplace_id:
            selected_offer = offer
            break
    if not selected_offer:
        selected_offer = offers[0]

    # Update product with offer data
    product.ebay_offer_id = selected_offer.get("offerId")
    product.marketplace_id = selected_offer.get("marketplaceId", marketplace_id)

    # Listing details
    listing = selected_offer.get("listing", {})
    product.ebay_listing_id = listing.get("listingId")
    product.sold_quantity = listing.get("soldQuantity")

    # Price from offer
    pricing = selected_offer.get("pricingSummary", {})
    price_obj = pricing.get("price", {})
    if price_obj:
        product.price = float(price_obj.get("value", 0))
        product.currency = price_obj.get("currency", "EUR")

    # Listing format and duration
    product.listing_format = selected_offer.get("format")
    product.listing_duration = selected_offer.get("listingDuration")

    # Categories
    product.category_id = selected_offer.get("categoryId")
    product.secondary_category_id = selected_offer.get("secondaryCategoryId")

    # Location
    product.merchant_location_key = selected_offer.get("merchantLocationKey")

    # Quantity details
    product.available_quantity = selected_offer.get("availableQuantity")
    product.lot_size = selected_offer.get("lotSize")
    product.quantity_limit_per_buyer = selected_offer.get("quantityLimitPerBuyer")

    # Listing description
    product.listing_description = selected_offer.get("listingDescription")

    # Status from offer
    offer_status = selected_offer.get("status")
    if offer_status == "PUBLISHED":
        product.status = "active"
        product.published_at = utc_now()
    elif offer_status == "ENDED":
        product.status = "ended"


def _run_import_in_background(job_id: int, user_id: int, marketplace_id: str):
    """
    Execute import in background task with its own DB session.

    Optimized: imports products first, then enriches in parallel batches of 10.
    """
    from models.user.marketplace_job import JobStatus, MarketplaceJob
    from sqlalchemy import text

    ENRICHMENT_BATCH_SIZE = 10  # Number of parallel API calls

    schema_name = f"user_{user_id}"
    db = SessionLocal()
    try:
        # Use schema_translate_map for ORM queries (survives commit/rollback)
        db = db.execution_options(schema_translate_map={"tenant": schema_name})
        # Also set search_path for text() queries
        db.execute(text(f"SET search_path TO {schema_name}, public"))

        logger.info(f"[Background Import] Schema configured: {schema_name}")

        # Get the job
        job = db.query(MarketplaceJob).filter(MarketplaceJob.id == job_id).first()
        if not job:
            logger.error(f"[Background Import] Job #{job_id} not found")
            return

        # Initialize progress
        job.result_data = {"current": 0, "label": "initialisation..."}
        db.commit()
        # Note: schema_translate_map persists after commit - no need to re-SET

        # Create importer
        importer = EbayImporter(
            db=db,
            user_id=user_id,
            marketplace_id=marketplace_id,
        )

        # Process inventory page by page
        imported_count = 0
        offset = 0
        limit = 100

        while True:
            # Fetch one page of inventory
            result = importer.inventory_client.get_inventory_items(
                limit=limit,
                offset=offset
            )
            # Note: schema_translate_map persists even after token refresh commits

            items = result.get("inventoryItems", [])
            if not items:
                break

            # Import items WITHOUT enrichment first (fast)
            page_products = []
            logger.info(f"[Background Import] Processing {len(items)} items from API")

            for idx, item in enumerate(items):
                sku = item.get("sku", "unknown")
                logger.debug(f"[Background Import] Item {idx+1}/{len(items)}: SKU={sku}")

                try:
                    import_result = importer._import_single_item(item, enrich=False)
                    logger.debug(f"[Background Import] _import_single_item result: status={import_result['status']}, id={import_result.get('id')}")

                    if import_result["status"] in ["imported", "updated"]:
                        # Use the product object returned directly (no extra ORM query)
                        product = import_result.get("product")
                        if product:
                            page_products.append(product)
                            logger.debug(f"[Background Import] Added product ID={product.id} to batch")
                        else:
                            logger.warning(f"[Background Import] No product object in result for SKU={sku}")

                except Exception as e:
                    logger.error(f"[Background Import] Failed to import item SKU={sku}: {type(e).__name__}: {e}")

            db.commit()

            # Enrich in parallel batches of 10
            for i in range(0, len(page_products), ENRICHMENT_BATCH_SIZE):
                batch = page_products[i:i + ENRICHMENT_BATCH_SIZE]

                # Parallel enrichment (10 API calls at once)
                _enrich_products_parallel(importer, batch, db, schema_name, max_workers=ENRICHMENT_BATCH_SIZE)

                # Update progress after each batch (use direct UPDATE to avoid expired object issues)
                imported_count += len(batch)
                db.execute(
                    text("UPDATE marketplace_jobs SET result_data = :data WHERE id = :job_id"),
                    {"data": f'{{"current": {imported_count}, "label": "produits importés"}}', "job_id": job_id}
                )
                db.commit()

                logger.info(f"[Background Import] Progress: {imported_count} products enriched")

            # Check if more pages
            total = result.get("total", 0)
            logger.info(f"[Background Import] Processed page (offset={offset}), total={total}, imported={imported_count}")

            if offset + limit >= total:
                break

            offset += limit

        # Mark job as completed (use direct UPDATE)
        db.execute(
            text("UPDATE marketplace_jobs SET status = 'completed', result_data = :data WHERE id = :job_id"),
            {"data": f'{{"current": {imported_count}, "label": "produits importés"}}', "job_id": job_id}
        )
        db.commit()

        logger.info(f"[Background Import] eBay import completed for user {user_id}: {imported_count} products (with parallel enrichment)")

    except Exception as e:
        logger.error(f"[Background Import] eBay import failed for user {user_id}: {e}")

        try:
            error_msg = str(e)[:500].replace("'", "''")  # Escape single quotes
            db.execute(
                text("UPDATE marketplace_jobs SET status = 'failed', error_message = :error WHERE id = :job_id"),
                {"error": error_msg, "job_id": job_id}
            )
            db.commit()
        except Exception as inner_e:
            logger.error(f"[Background Import] Could not mark job as failed: {inner_e}")

    finally:
        db.close()


@router.post("/import", response_model=ImportResponse)
async def import_ebay_products(
    background_tasks: BackgroundTasks,
    request: ImportRequest = Body(default=ImportRequest()),
    user_db: tuple = Depends(get_user_db),
):
    """
    Importe les produits depuis eBay Inventory API (en arrière-plan).

    Crée un job de suivi et lance l'import en arrière-plan.
    L'opération est suivie via un MarketplaceJob visible dans le popup tâches.

    Args:
        background_tasks: FastAPI background tasks
        request: Paramètres d'import (marketplace_id)
        user_db: (Session DB, User) avec schema isolé

    Returns:
        ImportResponse: Confirmation du démarrage (imported=0, status=started)
    """
    db, current_user = user_db

    try:
        # Create marketplace job for tracking
        from services.marketplace.marketplace_job_service import MarketplaceJobService
        from models.user.marketplace_job import JobStatus

        job_service = MarketplaceJobService(db)

        job = job_service.create_job(
            marketplace="ebay",
            action_code="import",
            product_id=None,  # Operation-level job (not product-specific)
            input_data={
                "marketplace_id": request.marketplace_id
            },
        )

        # Set job to running
        job.status = JobStatus.RUNNING
        job_id = job.id

        db.commit()

        logger.info(
            f"[POST /products/import] Created job #{job_id} for user {current_user.id}, starting background import"
        )

        # Schedule background task
        background_tasks.add_task(
            _run_import_in_background,
            job_id=job_id,
            user_id=current_user.id,
            marketplace_id=request.marketplace_id,
        )

        # Return immediately with job info
        return ImportResponse(
            imported=0,
            updated=0,
            skipped=0,
            errors=0,
            details=[{"status": "started", "job_id": job_id, "message": "Import started in background"}],
        )

    except Exception as e:
        logger.error(f"eBay import failed to start for user {current_user.id}: {e}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed to start: {str(e)}",
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
