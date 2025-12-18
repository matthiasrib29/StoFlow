"""
Shared imports and helpers for Vinted API modules.
"""

from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_db, get_user_db
from models.public.user import User
from models.user.vinted_connection import VintedConnection


class VintedConnectRequest(BaseModel):
    """Request body pour /connect"""
    vinted_user_id: int
    login: str


def get_active_vinted_connection(db: Session, user_id: int) -> VintedConnection:
    """
    Récupère la connexion Vinted active pour un utilisateur.

    Raises:
        HTTPException 400: Si aucune connexion active n'est trouvée
    """
    connection = db.query(VintedConnection).filter(
        VintedConnection.user_id == user_id,
        VintedConnection.is_connected == True
    ).first()

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Compte Vinted non connecté. Utilisez POST /vinted/connect d'abord."
        )

    return connection
