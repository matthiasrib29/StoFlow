"""
Vinted Messages Routes

Endpoints pour la gestion des messages Vinted (inbox):
- GET /conversations: Liste des conversations
- POST /conversations/sync: Synchroniser inbox depuis Vinted
- GET /conversations/{id}: Conversation avec ses messages
- POST /conversations/{id}/sync: Synchroniser une conversation
- PUT /conversations/{id}/read: Marquer comme lue
- GET /messages/search: Rechercher dans les messages

Author: Claude
Date: 2025-12-19
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.dependencies import get_user_db
from repositories.vinted_conversation_repository import VintedConversationRepository
from services.vinted.vinted_conversation_service import VintedConversationService
from .shared import get_active_vinted_connection

router = APIRouter()


# =============================================================================
# CONVERSATIONS ENDPOINTS
# =============================================================================

@router.get("/conversations")
async def list_conversations(
    user_db: tuple = Depends(get_user_db),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    per_page: int = Query(20, ge=1, le=50, description="Items per page"),
    unread_only: bool = Query(False, description="Filter to unread only"),
) -> dict:
    """
    Liste les conversations Vinted en BDD.

    Returns:
        {
            "conversations": list,
            "pagination": {page, per_page, total_entries, total_pages},
            "unread_count": int
        }
    """
    db, current_user = user_db

    try:
        service = VintedConversationService()
        result = service.get_conversations(
            db=db,
            page=page,
            per_page=per_page,
            unread_only=unread_only
        )
        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur liste conversations: {str(e)}"
        )


@router.post("/conversations/sync")
async def sync_inbox(
    user_db: tuple = Depends(get_user_db),
    page: int = Query(1, ge=1, description="Page to sync"),
    per_page: int = Query(20, ge=1, le=20, description="Items per page (max 20)"),
    sync_all: bool = Query(False, description="Sync all pages"),
) -> dict:
    """
    Synchronise l'inbox Vinted (liste des conversations).

    Utilise le PluginTask pour appeler l'API Vinted.

    Args:
        page: Page à synchroniser (1-indexed)
        per_page: Items par page (max 20)
        sync_all: Si True, synchronise toutes les pages

    Returns:
        {
            "synced": int,
            "created": int,
            "updated": int,
            "total": int,
            "unread": int,
            "errors": list
        }
    """
    db, current_user = user_db

    # Check Vinted connection
    get_active_vinted_connection(db, current_user.id)

    try:
        service = VintedConversationService()
        result = await service.sync_inbox(
            db=db,
            page=page,
            per_page=per_page,
            sync_all_pages=sync_all
        )
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur sync inbox: {str(e)}"
        )


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: int,
    user_db: tuple = Depends(get_user_db),
) -> dict:
    """
    Récupère une conversation avec ses messages.

    Returns:
        {
            "conversation": {...},
            "messages": [...]
        }
    """
    db, current_user = user_db

    try:
        service = VintedConversationService()
        result = service.get_conversation(db, conversation_id)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} non trouvée"
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur récupération conversation: {str(e)}"
        )


@router.post("/conversations/{conversation_id}/sync")
async def sync_conversation(
    conversation_id: int,
    user_db: tuple = Depends(get_user_db),
) -> dict:
    """
    Synchronise une conversation spécifique (ses messages).

    Utilise le PluginTask pour appeler l'API Vinted.

    Returns:
        {
            "conversation_id": int,
            "messages_synced": int,
            "messages_new": int,
            "transaction_id": int | null,
            "errors": list
        }
    """
    db, current_user = user_db

    # Check Vinted connection
    get_active_vinted_connection(db, current_user.id)

    try:
        service = VintedConversationService()
        result = await service.sync_conversation(db, conversation_id)
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur sync conversation: {str(e)}"
        )


@router.put("/conversations/{conversation_id}/read")
async def mark_as_read(
    conversation_id: int,
    user_db: tuple = Depends(get_user_db),
) -> dict:
    """
    Marque une conversation comme lue (dans la BDD locale).

    Note: Ne marque PAS comme lue sur Vinted (pas d'API call).

    Returns:
        {"success": bool, "conversation_id": int}
    """
    db, current_user = user_db

    try:
        conversation = VintedConversationRepository.mark_as_read(db, conversation_id)

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} non trouvée"
            )

        return {
            "success": True,
            "conversation_id": conversation_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur marquage lu: {str(e)}"
        )


@router.get("/conversations/{conversation_id}/messages")
async def list_messages(
    conversation_id: int,
    user_db: tuple = Depends(get_user_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
) -> dict:
    """
    Liste les messages d'une conversation avec pagination.

    Returns:
        {
            "messages": list,
            "pagination": {page, per_page, total_entries, total_pages}
        }
    """
    db, current_user = user_db

    try:
        # Check if conversation exists
        conversation = VintedConversationRepository.get_by_id(db, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} non trouvée"
            )

        service = VintedConversationService()
        result = service.get_messages(
            db=db,
            conversation_id=conversation_id,
            page=page,
            per_page=per_page
        )
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur liste messages: {str(e)}"
        )


# =============================================================================
# MESSAGES SEARCH ENDPOINT
# =============================================================================

@router.get("/messages/search")
async def search_messages(
    user_db: tuple = Depends(get_user_db),
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(50, ge=1, le=100),
) -> dict:
    """
    Recherche dans les messages (body uniquement).

    Args:
        q: Terme de recherche (minimum 2 caractères)
        limit: Nombre max de résultats

    Returns:
        {
            "query": str,
            "results": list,
            "count": int
        }
    """
    db, current_user = user_db

    try:
        service = VintedConversationService()
        results = service.search_messages(db, query=q, limit=limit)

        return {
            "query": q,
            "results": results,
            "count": len(results),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur recherche messages: {str(e)}"
        )


# =============================================================================
# STATS ENDPOINT
# =============================================================================

@router.get("/conversations/stats")
async def get_conversations_stats(
    user_db: tuple = Depends(get_user_db),
) -> dict:
    """
    Statistiques sur les conversations.

    Returns:
        {
            "total_conversations": int,
            "unread_conversations": int
        }
    """
    db, current_user = user_db

    try:
        total = VintedConversationRepository.count(db, unread_only=False)
        unread = VintedConversationRepository.count(db, unread_only=True)

        return {
            "total_conversations": total,
            "unread_conversations": unread,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur stats conversations: {str(e)}"
        )
