"""
Vinted Message Service - Service wrapper for conversation/message handling

Wraps VintedConversationService to follow standard service pattern.

Author: Claude
Date: 2026-01-15
"""

from typing import Any
from sqlalchemy.orm import Session

from services.vinted.vinted_conversation_service import VintedConversationService


class VintedMessageService:
    """
    Service for handling Vinted messages and conversations.

    Wraps VintedConversationService to provide consistent interface
    with other Vinted services.
    """

    def __init__(self, db: Session):
        """
        Initialize message service.

        Args:
            db: Database session
        """
        self.db = db

    async def handle_message(
        self,
        message_id: int | None,
        user_id: int,
        shop_id: int,
        params: dict | None = None
    ) -> dict[str, Any]:
        """
        Handle message synchronization.

        Args:
            message_id: Conversation ID (if syncing specific conversation)
            user_id: User ID (unused, kept for signature compatibility)
            shop_id: Shop ID (unused, kept for signature compatibility)
            params: Additional parameters:
                - page: int - Page number
                - per_page: int - Items per page
                - sync_all: bool - Sync all pages

        Returns:
            dict: {
                "success": bool,
                "message_handled": bool,
                "mode": "inbox" | "conversation",
                "synced": int,
                "created": int,
                "updated": int,
                "error": str | None
            }
        """
        try:
            conversation_service = VintedConversationService()
            params = params or {}

            # Sync specific conversation
            if message_id:
                result = await conversation_service.sync_conversation(
                    self.db, message_id
                )
                return {
                    "success": True,
                    "message_handled": True,
                    "mode": "conversation",
                    **result
                }

            # Sync inbox (all conversations)
            page = params.get("page", 1)
            per_page = params.get("per_page", 20)
            sync_all = params.get("sync_all", False)

            result = await conversation_service.sync_inbox(
                self.db,
                page=page,
                per_page=per_page,
                sync_all_pages=sync_all
            )

            return {
                "success": True,
                "message_handled": True,
                "mode": "inbox",
                **result
            }

        except Exception as e:
            return {
                "success": False,
                "message_handled": False,
                "error": str(e)
            }
