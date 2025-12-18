"""
Integrations Status Route

Global status endpoint for all platform integrations.

Author: Claude
Date: 2025-12-17
"""

from fastapi import APIRouter, Depends, status

from api.dependencies import get_user_db
from shared.logging_setup import get_logger

from .schemas import IntegrationsStatusResponse

router = APIRouter()
logger = get_logger(__name__)


@router.get(
    "/status", response_model=IntegrationsStatusResponse, status_code=status.HTTP_200_OK
)
async def get_integrations_status(
    user_db: tuple = Depends(get_user_db),
):
    """
    Récupère le statut de toutes les intégrations pour l'utilisateur.

    Business Rules (2025-12-17):
    - Retourne le statut de connexion pour chaque plateforme
    - Affiche le nombre de publications par plateforme
    - Isolation: données filtrées par user_id via get_user_db dependency

    Args:
        user_db: Tuple (db, current_user) avec search_path configuré

    Returns:
        IntegrationsStatusResponse: Statut de toutes les intégrations
    """
    from models.user.ebay_credentials import EbayCredentials
    from models.user.vinted_connection import VintedConnection
    from models.user.vinted_product import VintedProduct

    db, current_user = user_db

    # Initialiser avec statuts par défaut
    integrations_status = [
        {
            "platform": "vinted",
            "name": "Vinted",
            "is_connected": False,
            "last_sync": None,
            "total_publications": 0,
            "active_publications": 0,
        },
        {
            "platform": "ebay",
            "name": "eBay",
            "is_connected": False,
            "last_sync": None,
            "total_publications": 0,
            "active_publications": 0,
        },
        {
            "platform": "etsy",
            "name": "Etsy",
            "is_connected": False,
            "last_sync": None,
            "total_publications": 0,
            "active_publications": 0,
        },
        {
            "platform": "facebook",
            "name": "Facebook Marketplace",
            "is_connected": False,
            "last_sync": None,
            "total_publications": 0,
            "active_publications": 0,
        },
    ]

    # ===== VINTED =====
    try:
        vinted_connection = db.query(VintedConnection).first()
        if vinted_connection:
            # Compter les produits Vinted
            total_vinted = db.query(VintedProduct).count()
            active_vinted = (
                db.query(VintedProduct).filter(VintedProduct.status == "published").count()
            )

            integrations_status[0] = {
                "platform": "vinted",
                "name": "Vinted",
                "is_connected": True,
                "last_sync": (
                    vinted_connection.last_sync.isoformat()
                    if vinted_connection.last_sync
                    else None
                ),
                "total_publications": total_vinted,
                "active_publications": active_vinted,
            }
    except Exception as e:
        logger.error(f"Erreur récupération statut Vinted: {e}")

    # ===== EBAY =====
    try:
        ebay_creds = db.query(EbayCredentials).first()
        if ebay_creds and ebay_creds.access_token:
            integrations_status[1] = {
                "platform": "ebay",
                "name": "eBay",
                "is_connected": True,
                "last_sync": (
                    ebay_creds.updated_at.isoformat() if ebay_creds.updated_at else None
                ),
                "total_publications": 0,  # TODO: compter depuis ebay_products
                "active_publications": 0,
            }
    except Exception as e:
        logger.error(f"Erreur récupération statut eBay: {e}")

    # ===== ETSY =====
    # TODO: Implémenter quand EtsyCredentials existe

    return {"integrations": integrations_status}
