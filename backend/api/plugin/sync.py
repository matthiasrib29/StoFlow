"""
Plugin Sync Routes

Routes for platform synchronization from browser plugin.

Business Rules (Updated: 2025-12-06):
- Le plugin envoie les cookies des plateformes (Vinted, eBay, Etsy)
- Authentification via JWT token Stoflow (Bearer)
- Les cookies restent UNIQUEMENT sur la machine de l'utilisateur (chrome.storage)
- Le backend NE STOCKE PAS les cookies (test uniquement)
- Test de connexion automatique lors de la sync

Author: Claude
Date: 2025-12-17
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.dependencies import get_current_user
from models.public.user import User
from services.vinted.vinted_adapter import test_vinted_connection
from shared.database import get_db
from shared.datetime_utils import utc_now

from .schemas import (
    PlatformCookies,
    PlatformStatus,
    PluginSyncRequest,
    PluginSyncResponse,
)

router = APIRouter()


@router.post("/sync", response_model=PluginSyncResponse, status_code=status.HTTP_200_OK)
async def plugin_sync_platforms(
    request: PluginSyncRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Synchronise les cookies des plateformes depuis le plugin.

    Business Rules (Updated: 2025-12-06):
    - Authentification requise (JWT Bearer token)
    - Teste la connexion pour chaque plateforme avec les cookies fournis
    - Les cookies NE SONT PAS stockés côté backend (restent sur la machine utilisateur)
    - Retourne le status de chaque plateforme
    - Auto-refresh token automatique

    Args:
        request: Liste des plateformes + cookies
        current_user: Utilisateur authentifié (via JWT)
        db: Session DB

    Returns:
        PluginSyncResponse: Status + nouveau token si refresh
    """
    platforms_status = []
    platforms_synced = 0

    for platform_data in request.platforms:
        platform_name = platform_data.platform.lower()

        # Test connexion selon la plateforme
        if platform_name == "vinted":
            result = await test_vinted_connection(platform_data.cookies)

            if result["connected"]:
                platforms_synced += 1
                # NOTE: Les cookies NE SONT PAS stockés côté backend
                # Ils restent uniquement sur la machine de l'utilisateur (chrome.storage)

            platforms_status.append(
                PlatformStatus(
                    platform="vinted",
                    connected=result["connected"],
                    user=result.get("user"),
                    error=result.get("error"),
                    last_synced_at=utc_now() if result["connected"] else None,
                )
            )

        elif platform_name == "ebay":
            # eBay nécessite OAuth2, pas de test avec cookies
            platforms_status.append(
                PlatformStatus(
                    platform="ebay",
                    connected=False,
                    user=None,
                    error="eBay requires OAuth2, cookie sync not supported",
                    last_synced_at=None,
                )
            )

        elif platform_name == "etsy":
            # Etsy nécessite OAuth2
            platforms_status.append(
                PlatformStatus(
                    platform="etsy",
                    connected=False,
                    user=None,
                    error="Etsy requires OAuth2, cookie sync not supported",
                    last_synced_at=None,
                )
            )

        else:
            platforms_status.append(
                PlatformStatus(
                    platform=platform_name,
                    connected=False,
                    user=None,
                    error=f"Platform '{platform_name}' not supported",
                    last_synced_at=None,
                )
            )

    return PluginSyncResponse(
        success=platforms_synced > 0,
        platforms_synced=platforms_synced,
        platforms_status=platforms_status,
        message=f"{platforms_synced}/{len(request.platforms)} platforms synced successfully",
    )


@router.get("/platforms", status_code=status.HTTP_200_OK)
async def get_supported_platforms(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retourne la liste des plateformes supportées par le plugin.

    Args:
        current_user: Utilisateur authentifié
        db: Session DB

    Returns:
        dict: Plateformes supportées avec détails
    """
    return {
        "platforms": [
            {
                "name": "vinted",
                "display_name": "Vinted",
                "auth_method": "cookies",
                "supported": True,
                "features": ["import", "publish", "sync", "delete"],
            },
            {
                "name": "ebay",
                "display_name": "eBay",
                "auth_method": "oauth2",
                "supported": False,
                "features": [],
                "note": "OAuth2 integration not implemented in V1",
            },
            {
                "name": "etsy",
                "display_name": "Etsy",
                "auth_method": "oauth2",
                "supported": False,
                "features": [],
                "note": "OAuth2 integration not implemented in V1",
            },
        ]
    }


@router.get("/health", status_code=status.HTTP_200_OK)
async def plugin_health_check():
    """
    Health check pour le plugin.

    Business Rules:
    - Endpoint public (pas d'authentification requise)
    - Utilisé par le plugin pour vérifier la disponibilité de l'API

    Returns:
        dict: Status de l'API
    """
    return {
        "status": "healthy",
        "api_version": "1.0.0",
        "plugin_compatible": ["1.0.0", "1.0.1"],
    }
