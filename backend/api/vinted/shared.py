"""
Shared imports and helpers for Vinted API modules.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_db, get_user_db
from models.public.user import User
from models.user.vinted_connection import VintedConnection


class VintedConnectRequest(BaseModel):
    """Request body pour /connect (legacy - DOM extraction only)"""
    vinted_user_id: int
    login: str


class VintedSellerStats(BaseModel):
    """Seller statistics from Vinted API /api/v2/users/current"""
    item_count: Optional[int] = None
    total_items_count: Optional[int] = None
    given_item_count: Optional[int] = None
    taken_item_count: Optional[int] = None
    followers_count: Optional[int] = None
    feedback_count: Optional[int] = None
    feedback_reputation: Optional[float] = None
    positive_feedback_count: Optional[int] = None
    negative_feedback_count: Optional[int] = None
    is_business: Optional[bool] = None
    is_on_holiday: Optional[bool] = None


class VintedConnectWithStatsRequest(BaseModel):
    """
    Request body pour /connect avec stats vendeur.

    Supports two modes:
    - full_profile: From API /api/v2/users/current (includes stats)
    - dom_extraction: From DOM parsing (legacy, userId + login only)
    """
    vinted_user_id: int
    login: str
    # Optional stats (only present if from API call)
    stats: Optional[VintedSellerStats] = None
    # Source indicator
    source: Optional[str] = None  # "api" or "dom"


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
