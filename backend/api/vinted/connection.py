"""
Vinted Connection Routes

Endpoints pour la gestion de la connexion au compte Vinted:
- POST /connect: Connecter un compte Vinted
- POST /check-connection: Vérifier via le plugin
- GET /status: Statut de connexion
- DELETE /disconnect: Déconnecter
- POST /notify-disconnect: Notification auto par le plugin

Author: Claude
Date: 2025-12-17
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_user_db
from models.user.vinted_connection import VintedConnection
from .shared import VintedConnectRequest, VintedConnectWithStatsRequest

router = APIRouter()


@router.post("/connect")
async def connect_vinted(
    request: VintedConnectWithStatsRequest,
    user_db: tuple = Depends(get_user_db),
) -> dict:
    """
    Connecte/synchronise le compte Vinted de l'utilisateur.

    Supports two modes:
    - API mode: Plugin calls /api/v2/users/current and sends full profile with stats
    - DOM mode: Plugin extracts userId + login from HTML (legacy fallback)

    Args:
        request: Body JSON avec vinted_user_id, login, et optionnellement stats

    Returns:
        {"success": True, "vinted_user_id": int, "login": str, "stats_updated": bool}
    """
    db, current_user = user_db
    vinted_user_id = request.vinted_user_id
    login = request.login
    stats = request.stats
    source = request.source or "unknown"

    try:
        now = datetime.now(timezone.utc)

        # Chercher connexion existante
        connection = db.query(VintedConnection).filter(
            VintedConnection.vinted_user_id == vinted_user_id
        ).first()

        if connection:
            # Mise à jour: marquer comme connecté
            connection.login = login
            connection.connect()
        else:
            connection = VintedConnection(
                vinted_user_id=vinted_user_id,
                login=login,
                is_connected=True,
                user_id=current_user.id,
                created_at=now,
                last_sync=now
            )
            db.add(connection)

        # Update seller stats if provided (from API call)
        stats_updated = False
        if stats:
            connection.update_seller_stats(stats.model_dump())
            stats_updated = True

        db.commit()

        return {
            "success": True,
            "vinted_user_id": vinted_user_id,
            "login": login,
            "last_sync": now.isoformat(),
            "stats_updated": stats_updated,
            "source": source
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur connexion Vinted: {str(e)}"
        )


@router.post("/check-connection")
async def check_vinted_connection(
    user_db: tuple = Depends(get_user_db),
) -> dict:
    """
    Vérifie la connexion Vinted via le plugin et récupère le profil complet.

    Flow:
    1. Frontend appelle cet endpoint
    2. Backend crée une task get_vinted_user_profile
    3. Plugin récupère la task et appelle l'API /api/v2/users/current
    4. Si l'API échoue, fallback sur extraction DOM
    5. Plugin renvoie userId/login + stats vendeur (si API)
    6. Backend sauvegarde la connexion et les stats

    Returns:
        {
            "connected": bool,
            "vinted_user_id": int | null,
            "login": str | null,
            "source": "api" | "dom",
            "stats_updated": bool,
            "message": str
        }

    Raises:
        408: Timeout si le plugin ne répond pas dans les 30s
        400: Si le plugin n'est pas connecté à Vinted
    """
    from services.plugin_task_helper import verify_vinted_connection_with_profile

    db, current_user = user_db

    try:
        result = await verify_vinted_connection_with_profile(db, timeout=30)

        if result.get("connected"):
            vinted_user_id = result.get("userId")
            login = result.get("login")
            source = result.get("source", "unknown")
            stats = result.get("stats")
            now = datetime.now(timezone.utc)

            connection = db.query(VintedConnection).filter(
                VintedConnection.vinted_user_id == vinted_user_id
            ).first()

            if connection:
                connection.login = login
                connection.connect()
            else:
                connection = VintedConnection(
                    vinted_user_id=vinted_user_id,
                    login=login,
                    is_connected=True,
                    user_id=current_user.id,
                    created_at=now,
                    last_sync=now
                )
                db.add(connection)

            # Update seller stats if available (from API call)
            stats_updated = False
            if stats:
                connection.update_seller_stats(stats)
                stats_updated = True

            db.commit()

            return {
                "connected": True,
                "vinted_user_id": vinted_user_id,
                "login": login,
                "source": source,
                "stats_updated": stats_updated,
                "message": f"Connecté en tant que {login}"
            }
        else:
            return {
                "connected": False,
                "vinted_user_id": None,
                "login": None,
                "source": None,
                "stats_updated": False,
                "message": "Non connecté à Vinted. Ouvrez vinted.fr et connectez-vous."
            }

    except TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Le plugin n'a pas répondu. Vérifiez que le plugin est actif et qu'un onglet Vinted est ouvert."
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur vérification connexion: {str(e)}"
        )


@router.get("/status")
async def get_vinted_status(
    user_db: tuple = Depends(get_user_db),
) -> dict:
    """
    Récupère le statut de connexion Vinted.

    Returns:
        {
            "is_connected": bool,
            "vinted_user_id": int | null,
            "login": str | null,
            "last_sync": str | null,
            "disconnected_at": str | null
        }
    """
    db, current_user = user_db

    try:
        connection = db.query(VintedConnection).filter(
            VintedConnection.user_id == current_user.id
        ).first()

        if connection:
            return {
                "is_connected": connection.is_connected,
                "vinted_user_id": connection.vinted_user_id,
                "login": connection.login,
                "last_sync": connection.last_sync.isoformat() if connection.last_sync else None,
                "disconnected_at": connection.disconnected_at.isoformat() if connection.disconnected_at else None
            }
        else:
            return {
                "is_connected": False,
                "vinted_user_id": None,
                "login": None,
                "last_sync": None,
                "disconnected_at": None
            }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur statut: {str(e)}"
        )


@router.delete("/disconnect")
async def disconnect_vinted(
    user_db: tuple = Depends(get_user_db),
) -> dict:
    """
    Déconnecte le compte Vinted de l'utilisateur.

    Marque la connexion comme inactive (is_connected=False) sans la supprimer.
    L'historique est conservé pour permettre une reconnexion rapide.

    Returns:
        {"success": True, "message": str}
    """
    db, current_user = user_db

    try:
        connection = db.query(VintedConnection).filter(
            VintedConnection.user_id == current_user.id
        ).first()

        if connection:
            login = connection.login
            connection.disconnect()
            db.commit()

            return {
                "success": True,
                "message": f"Compte Vinted {login} déconnecté"
            }
        else:
            return {
                "success": True,
                "message": "Aucun compte Vinted connecté"
            }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur déconnexion: {str(e)}"
        )


@router.post("/notify-disconnect")
async def notify_vinted_disconnect(
    user_db: tuple = Depends(get_user_db),
) -> dict:
    """
    Notification de déconnexion automatique par le plugin.

    Le plugin appelle cet endpoint quand il détecte que l'utilisateur
    n'est plus connecté à Vinted (via polling périodique).

    Returns:
        {"success": True, "message": str}
    """
    db, current_user = user_db

    try:
        connection = db.query(VintedConnection).filter(
            VintedConnection.user_id == current_user.id,
            VintedConnection.is_connected == True
        ).first()

        if connection:
            login = connection.login
            connection.disconnect()
            db.commit()

            return {
                "success": True,
                "message": f"Déconnexion de {login} enregistrée"
            }
        else:
            return {
                "success": True,
                "message": "Aucune connexion active à marquer comme déconnectée"
            }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur notification déconnexion: {str(e)}"
        )
