"""
Etsy Taxonomy & Polling Routes

Endpoints for taxonomy (categories) and polling.

Author: Claude
Date: 2025-12-17
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_db
from models.public.user import User
from services.etsy import EtsyPollingService, EtsyTaxonomyClient
from shared.logging import get_logger

from .schemas import PollingResultsResponse, TaxonomyNodeResponse

router = APIRouter()
logger = get_logger(__name__)


# ========== TAXONOMY (CATEGORIES) ==========


@router.get("/taxonomy/nodes", response_model=List[TaxonomyNodeResponse])
def get_taxonomy_nodes(
    search: Optional[str] = Query(None, description="Recherche par mot-cle"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Recupere les categories Etsy (taxonomy nodes).
    """
    try:
        client = EtsyTaxonomyClient(db, current_user.id)

        if search:
            nodes = client.search_taxonomy(search)
        else:
            nodes = client.get_seller_taxonomy_nodes()

        # Limit to first 100 for performance
        nodes = nodes[:100]

        return [
            TaxonomyNodeResponse(
                id=node["id"],
                level=node["level"],
                name=node["name"],
                parent_id=node.get("parent_id"),
                children=node.get("children", []),
                full_path_taxonomy_ids=node.get("full_path_taxonomy_ids", []),
            )
            for node in nodes
        ]

    except Exception as e:
        logger.error(f"Error getting taxonomy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting taxonomy: {str(e)}",
        )


@router.get("/taxonomy/nodes/{taxonomy_id}/properties")
def get_taxonomy_properties(
    taxonomy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Recupere les proprietes requises pour une categorie.
    """
    try:
        client = EtsyTaxonomyClient(db, current_user.id)
        properties = client.get_properties_by_taxonomy_id(taxonomy_id)

        return properties

    except Exception as e:
        logger.error(f"Error getting taxonomy properties: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting properties: {str(e)}",
        )


# ========== POLLING ==========


@router.get("/polling/status", response_model=PollingResultsResponse)
def poll_etsy_updates(
    check_orders: bool = Query(True, description="Poller les nouvelles commandes"),
    check_listings: bool = Query(True, description="Poller les listings mis a jour"),
    check_stock: bool = Query(True, description="Poller le stock faible"),
    order_interval: int = Query(5, description="Intervalle commandes (minutes)"),
    listing_interval: int = Query(15, description="Intervalle listings (minutes)"),
    stock_threshold: int = Query(5, description="Seuil stock faible"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Execute un cycle de polling Etsy (alternative aux webhooks).

    Note: Etsy n'a pas de webhooks natifs, utiliser polling regulier.
    """
    try:
        service = EtsyPollingService(db, current_user.id)
        results = service.run_polling_cycle(
            check_orders=check_orders,
            check_listings=check_listings,
            check_stock=check_stock,
            order_interval=order_interval,
            listing_interval=listing_interval,
            stock_threshold=stock_threshold,
        )

        return PollingResultsResponse(**results)

    except Exception as e:
        logger.error(f"Error polling Etsy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error polling: {str(e)}",
        )
