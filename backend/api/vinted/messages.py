"""
Vinted Messages Routes

Endpoints pour la gestion des messages Vinted (inbox):
- GET /conversations/stats: Statistiques conversations
- GET /conversations: Liste des conversations
- POST /conversations/sync: Sync inbox ou conversation (optionnel: conversation_id)
- GET /conversations/{id}: Conversation avec ses messages
- PUT /conversations/{id}/read: Marquer comme lue

Updated: 2026-01-05 - Fusion sync endpoints, suppression search et list_messages

Author: Claude
Date: 2025-12-19
"""

from typing import Optional

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

# IMPORTANT: /conversations/stats MUST be defined BEFORE /conversations/{conversation_id}
# Otherwise FastAPI will try to parse "stats" as an integer conversation_id

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
async def sync_conversations(
    user_db: tuple = Depends(get_user_db),
    conversation_id: Optional[int] = Query(None, description="ID conversation spécifique (optionnel)"),
    page: int = Query(1, ge=1, description="Page to sync (inbox mode)"),
    per_page: int = Query(20, ge=1, le=20, description="Items per page (inbox mode)"),
    sync_all: bool = Query(False, description="Sync all pages (inbox mode)"),
) -> dict:
    """
    Synchronise les conversations Vinted via Temporal workflow.

    - Sans conversation_id : sync inbox (liste des conversations)
    - Avec conversation_id : sync une conversation spécifique (messages)

    Args:
        conversation_id: ID conversation (optionnel)
        page/per_page/sync_all: Options pour sync inbox

    Returns:
        Workflow result dict
    """
    from temporal.client import get_temporal_client
    from temporal.config import get_temporal_config
    from temporal.workflows.vinted.message_workflow import (
        VintedMessageParams,
        VintedMessageWorkflow,
    )

    db, current_user = user_db

    vinted_connection = get_active_vinted_connection(db, current_user.id)
    shop_id = vinted_connection.vinted_user_id

    try:
        config = get_temporal_config()
        client = await get_temporal_client()

        workflow_id = f"vinted-message-user-{current_user.id}-conv-{conversation_id or 'inbox'}"
        params = VintedMessageParams(
            user_id=current_user.id,
            shop_id=shop_id,
            conversation_id=conversation_id or 0,
        )

        handle = await client.start_workflow(
            VintedMessageWorkflow.run,
            params,
            id=workflow_id,
            task_queue=config.temporal_vinted_task_queue,
        )

        # Messages sync is relatively quick, wait for result
        result = await handle.result()

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur sync conversations: {str(e)}"
        )


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: int,
    user_db: tuple = Depends(get_user_db),
) -> dict:
    """
    Récupère une conversation avec ses messages.

    Returns:
        {"conversation": {...}, "messages": [...]}
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






