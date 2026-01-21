"""
Vinted Connection Routes

Endpoints pour la gestion de la connexion au compte Vinted:
- POST /check-connection: Verify connection via MarketplaceJob + WebSocket
- GET /status: Statut de connexion
- DELETE /disconnect: Déconnecter
- POST /notify-disconnect: Notification auto par le plugin

Flow via Jobs (2026-01-21):
1. Frontend → POST /check-connection → Creates MarketplaceJob
2. Backend → WebSocket → Frontend → Plugin → GET /api/v2/users/current
3. Backend processes result and updates VintedConnection
4. Frontend receives job result

Author: Claude
Date: 2025-12-17
Updated: 2026-01-21 (migrated to MarketplaceJob + WebSocket, removed pending_instructions)
"""

from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies import get_user_db
from models.user.vinted_connection import VintedConnection
from services.vinted import VintedJobService
from services.marketplace.marketplace_job_processor import MarketplaceJobProcessor

router = APIRouter()


@router.post("/check-connection")
async def check_vinted_connection(
    user_db: tuple = Depends(get_user_db),
) -> dict:
    """
    Verify Vinted connection via MarketplaceJob system.

    Creates a check_connection job that:
    1. Calls GET /api/v2/users/current via WebSocket → Plugin
    2. Creates/updates VintedConnection based on result
    3. Returns connection status

    Returns:
        {
            "job_id": int,
            "connected": bool,
            "vinted_user_id": int | None,
            "login": str | None,
            "error": str | None
        }

    Raises:
        500: Job execution failed
    """
    db, current_user = user_db

    try:
        # 1. Create check_connection job
        job_service = VintedJobService(db)
        job = job_service.create_job(
            action_code="check_connection",
            product_id=None  # No product for connection check
        )

        # Store values BEFORE commit
        job_id = job.id
        user_id = current_user.id

        db.commit()
        db.refresh(job)

        # 2. Execute job immediately (connection check is quick)
        # shop_id is None because we don't know if user is connected yet
        processor = MarketplaceJobProcessor(
            db,
            user_id=user_id,
            shop_id=None,
            marketplace="vinted"
        )
        result = await processor._execute_job(job)

        # 3. Return result
        return {
            "job_id": job_id,
            "connected": result.get("connected", False),
            "vinted_user_id": result.get("vinted_user_id"),
            "login": result.get("login"),
            "error": result.get("error")
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Connection check failed: {str(e)}"
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
            "last_synced_at": str | null
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
                "login": connection.username,
                "last_synced_at": connection.last_synced_at.isoformat() if connection.last_synced_at else None
            }
        else:
            return {
                "is_connected": False,
                "vinted_user_id": None,
                "login": None,
                "last_synced_at": None
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
            username = connection.username
            connection.disconnect()
            db.commit()

            return {
                "success": True,
                "message": f"Compte Vinted {username} déconnecté"
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
            username = connection.username
            connection.disconnect()
            db.commit()

            return {
                "success": True,
                "message": f"Déconnexion de {username} enregistrée"
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
