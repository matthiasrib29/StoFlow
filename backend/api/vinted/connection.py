"""
Vinted Connection Routes

Endpoints pour la gestion de la connexion au compte Vinted:
- POST /check-connection: Obtenir instruction pour connexion via plugin
- POST /check-connection/callback: Recevoir résultat d'exécution plugin
- GET /status: Statut de connexion
- DELETE /disconnect: Déconnecter
- POST /notify-disconnect: Notification auto par le plugin

Flow orchestré (100% API Vinted):
1. Frontend → POST /check-connection → Backend retourne instruction
2. Frontend → Plugin exécute VINTED_GET_USER_PROFILE (API Vinted)
3. Frontend → POST /check-connection/callback → Backend valide et sauvegarde

Author: Claude
Date: 2025-12-17
Updated: 2026-01-06 (100% API flow, removed DOM extraction)
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_user_db
from models.user.vinted_connection import VintedConnection
from .shared import VintedConnectionCallbackRequest

router = APIRouter()


@router.post("/check-connection")
async def check_vinted_connection(
    user_db: tuple = Depends(get_user_db),
) -> dict:
    """
    Crée une instruction pour vérifier la connexion Vinted via le plugin.

    **Nouveau flow orchestré par le backend:**
    1. Frontend appelle cet endpoint
    2. Backend crée une PendingInstruction et la retourne
    3. Frontend exécute l'instruction via le plugin
    4. Frontend renvoie le résultat au callback /check-connection/callback
    5. Backend valide et sauvegarde la connexion

    Returns:
        {
            "instruction": "call_plugin",
            "action": "VINTED_GET_USER_PROFILE",
            "requestId": "abc-123-...",
            "timeout": 30
        }

    Raises:
        500: Erreur lors de la création de l'instruction
    """
    import uuid
    from models.user.pending_instruction import PendingInstruction

    db, current_user = user_db

    try:
        # Générer un UUID unique pour cette instruction
        instruction_id = str(uuid.uuid4())

        # Créer l'instruction en attente
        pending = PendingInstruction(
            id=instruction_id,
            user_id=current_user.id,
            action="check_vinted_connection",
            status="pending",
            created_at=datetime.now(timezone.utc)
        )
        db.add(pending)
        db.commit()

        # Retourner l'instruction au frontend
        return {
            "instruction": "call_plugin",
            "action": "VINTED_GET_USER_PROFILE",  # API Vinted avec stats
            "requestId": instruction_id,
            "timeout": 30
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur création instruction: {str(e)}"
        )


@router.post("/check-connection/callback")
async def vinted_connection_callback(
    request: VintedConnectionCallbackRequest,
    user_db: tuple = Depends(get_user_db),
) -> dict:
    """
    Callback appelé par le frontend après exécution de l'instruction plugin.

    **Nouveau flow orchestré par le backend:**
    1. Frontend reçoit instruction de /check-connection
    2. Frontend exécute l'action via le plugin
    3. Frontend envoie le résultat à ce callback
    4. Backend valide, sauvegarde la connexion, et retourne le statut final

    Args:
        request: Body contenant requestId, success, result (userId, login), error

    Returns:
        {
            "connected": bool,
            "vinted_user_id": int | None,
            "login": str | None,
            "message": str
        }

    Raises:
        404: Instruction non trouvée ou déjà traitée
        500: Erreur lors de la sauvegarde
    """
    from models.user.pending_instruction import PendingInstruction

    db, current_user = user_db

    try:
        # 1. Vérifier que l'instruction existe et appartient à l'utilisateur
        instruction = db.query(PendingInstruction).filter(
            PendingInstruction.id == request.requestId,
            PendingInstruction.user_id == current_user.id,
            PendingInstruction.status == "pending"
        ).first()

        if not instruction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instruction non trouvée ou déjà traitée"
            )

        now = datetime.now(timezone.utc)

        # 2. Marquer l'instruction comme completed/failed
        if request.success:
            instruction.status = "completed"
            instruction.result = request.result
            instruction.completed_at = now
        else:
            instruction.status = "failed"
            instruction.error = request.error
            instruction.completed_at = now

        # 3. Si succès, sauvegarder la connexion Vinted
        if request.success and request.result:
            # Format API uniquement (pas de fallback DOM)
            vinted_user_id = request.result.get("id")
            login = request.result.get("login")

            # Validation stricte des champs requis
            if not vinted_user_id or not login:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Missing required fields: id and login from plugin result"
                )

            vinted_user_id = int(vinted_user_id)

            # Réutiliser la logique de /connect
            connection = db.query(VintedConnection).filter(
                VintedConnection.vinted_user_id == vinted_user_id
            ).first()

            if connection:
                # Mise à jour: marquer comme connecté
                connection.login = login
                connection.connect()
            else:
                # Création: nouveau VintedConnection
                connection = VintedConnection(
                    vinted_user_id=vinted_user_id,
                    login=login,
                    is_connected=True,
                    user_id=current_user.id,
                    created_at=now,
                    last_synced_at=now
                )
                db.add(connection)

            # Sauvegarder les stats vendeur si présentes (de l'API Vinted)
            if request.result.get("stats"):
                connection.update_seller_stats(request.result["stats"])

            db.commit()

            return {
                "connected": True,
                "vinted_user_id": vinted_user_id,
                "login": login,
                "message": f"Connecté en tant que {login}"
            }
        else:
            # Échec de la connexion
            db.commit()

            return {
                "connected": False,
                "vinted_user_id": None,
                "login": None,
                "message": request.error or "Échec de la connexion Vinted"
            }

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur callback connexion: {str(e)}"
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
                "login": connection.login,
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
