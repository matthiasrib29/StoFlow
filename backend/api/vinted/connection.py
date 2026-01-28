"""
Vinted Connection Routes

Endpoints pour la gestion de la connexion au compte Vinted:
- POST /check-connection: Verify connection via Temporal workflow
- GET /status: Statut de connexion
- DELETE /disconnect: Déconnecter
- POST /notify-disconnect: Notification auto par le plugin

Flow via Temporal (2026-01-27):
1. Frontend → POST /check-connection → Starts VintedCheckConnectionWorkflow
2. Temporal → Activity → Plugin → GET /api/v2/users/current
3. Activity processes result and updates VintedConnection
4. Frontend receives workflow result

Author: Claude
Date: 2025-12-17
Updated: 2026-01-27 (migrated to Temporal workflows)
"""

from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies import get_user_db
from models.user.vinted_connection import VintedConnection

router = APIRouter()


@router.post("/check-connection")
async def check_vinted_connection(
    user_db: tuple = Depends(get_user_db),
) -> dict:
    """
    Verify Vinted connection via Temporal workflow.

    Starts VintedCheckConnectionWorkflow that:
    1. Calls GET /api/v2/users/current via Plugin
    2. Creates/updates VintedConnection based on result
    3. Returns connection status

    Returns:
        {
            "connected": bool,
            "vinted_user_id": int | None,
            "login": str | None,
            "error": str | None
        }

    Raises:
        500: Workflow execution failed
    """
    from temporal.client import get_temporal_client
    from temporal.config import get_temporal_config
    from temporal.workflows.vinted.check_connection_workflow import (
        VintedCheckConnectionParams,
        VintedCheckConnectionWorkflow,
    )

    db, current_user = user_db

    try:
        config = get_temporal_config()
        client = await get_temporal_client()

        workflow_id = f"vinted-check-connection-user-{current_user.id}"
        params = VintedCheckConnectionParams(user_id=current_user.id)

        handle = await client.start_workflow(
            VintedCheckConnectionWorkflow.run,
            params,
            id=workflow_id,
            task_queue=config.temporal_vinted_task_queue,
        )

        # Connection check is quick, wait for result (1 min timeout)
        result = await handle.result()

        return {
            "connected": result.get("connected", False),
            "vinted_user_id": result.get("vinted_user_id"),
            "login": result.get("login"),
            "error": result.get("error"),
        }

    except Exception as e:
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
