"""
Vinted Conversation Service - Synchronization of Vinted conversations/messages

Service dedicated to synchronizing conversations and messages from Vinted API.

Methods available:
- sync_inbox(): Sync conversation list (delegates to VintedInboxSyncService)
- sync_conversation(): Sync messages for a specific conversation
- get_conversations(): Get conversations from local DB
- get_messages(): Get messages for a conversation

Refactored: 2026-01-06
- Extracted inbox sync to VintedInboxSyncService

Author: Claude
Date: 2025-12-19
"""

from datetime import datetime
from typing import Any, List, Optional

from dateutil.parser import parse as parse_datetime
from sqlalchemy.orm import Session

from models.user.vinted_conversation import VintedConversation, VintedMessage
from repositories.vinted_conversation_repository import (
    VintedConversationRepository,
    VintedMessageRepository,
)
from services.plugin_websocket_helper import PluginWebSocketHelper  # WebSocket architecture (2026-01-12)
from services.vinted.vinted_inbox_sync_service import VintedInboxSyncService
from shared.vinted_constants import VintedConversationAPI, VintedReferers
from shared.logging_setup import get_logger
from shared.config import settings

logger = get_logger(__name__)


class VintedConversationService:
    """
    Service for Vinted conversation/message operations.

    Methods:
    - sync_inbox: Sync all conversations from Vinted inbox
    - sync_conversation: Sync messages for a specific conversation
    - get_conversations: Get paginated conversations from DB
    - get_messages: Get messages for a conversation from DB
    """

    def __init__(self, user_id: int | None = None):
        """
        Initialize VintedConversationService.

        Args:
            user_id: ID utilisateur (requis pour WebSocket) (2026-01-12)
        """
        self.user_id = user_id
        self._inbox_sync_service = VintedInboxSyncService(user_id=user_id)

    # =========================================================================
    # SYNC INBOX (delegated to VintedInboxSyncService)
    # =========================================================================

    async def sync_inbox(
        self,
        db: Session,
        page: int = 1,
        per_page: int = 20,
        sync_all_pages: bool = False
    ) -> dict[str, Any]:
        """
        Sync conversations from Vinted inbox.

        Delegates to VintedInboxSyncService.

        Args:
            db: SQLAlchemy Session
            page: Page to fetch (1-indexed)
            per_page: Items per page (max 20)
            sync_all_pages: If True, fetch all pages until exhausted

        Returns:
            dict with sync results
        """
        return await self._inbox_sync_service.sync_inbox(
            db, page=page, per_page=per_page, sync_all_pages=sync_all_pages
        )

    # =========================================================================
    # SYNC CONVERSATION (messages for a specific conversation)
    # =========================================================================

    async def sync_conversation(
        self,
        db: Session,
        conversation_id: int
    ) -> dict[str, Any]:
        """
        Sync messages for a specific conversation.

        Uses PluginTask to call GET /api/v2/conversations/{id}.

        Args:
            db: SQLAlchemy Session
            conversation_id: Vinted conversation ID

        Returns:
            dict with:
            - conversation_id: The conversation ID
            - messages_synced: Number of messages synced
            - messages_new: Number of new messages
            - transaction_id: Linked transaction ID (if any)
        """
        result = {
            "conversation_id": conversation_id,
            "messages_synced": 0,
            "messages_new": 0,
            "transaction_id": None,
            "errors": []
        }

        try:
            logger.info(f"[VintedConversationService] Syncing conversation {conversation_id}")

            # Call Vinted API via WebSocket (2026-01-12)
            api_result = await PluginWebSocketHelper.call_plugin_http(
                db=db,
                user_id=self.user_id,
                http_method="GET",
                path=VintedConversationAPI.get_conversation(conversation_id),
                timeout=settings.plugin_timeout_sync,
                description=f"Sync conversation {conversation_id}"
            )

            if not api_result:
                logger.error(f"[VintedConversationService] No result for conversation {conversation_id}")
                result["errors"].append("No API response")
                return result

            conv_data = api_result.get("conversation", {})

            # Update conversation metadata
            self._update_conversation_metadata(db, conversation_id, conv_data, result)

            # Process messages
            messages_data = conv_data.get("messages", [])
            current_user_id = self._get_current_user_id(conv_data)

            for msg_data in messages_data:
                try:
                    msg = self._parse_message(msg_data, conversation_id, current_user_id)

                    # Check if message already exists (by vinted_message_id)
                    if msg.get("vinted_message_id"):
                        exists = VintedMessageRepository.exists_vinted_message_id(
                            db, conversation_id, msg["vinted_message_id"]
                        )
                        if exists:
                            result["messages_synced"] += 1
                            continue

                    # Create new message
                    message = VintedMessage(**msg)
                    VintedMessageRepository.create(db, message)
                    result["messages_synced"] += 1
                    result["messages_new"] += 1

                except (ValueError, KeyError, TypeError) as e:
                    logger.error(f"[VintedConversationService] Error processing message: {e}")
                    result["errors"].append(str(e))

            # Mark conversation as read in local DB
            VintedConversationRepository.mark_as_read(db, conversation_id)

            logger.info(
                f"[VintedConversationService] Conversation {conversation_id} synced: "
                f"messages={result['messages_synced']}, new={result['messages_new']}"
            )

            return result

        except Exception as e:
            logger.error(f"[VintedConversationService] sync_conversation error: {e}")
            # schema_translate_map survives rollback - no need to restore
            raise

    def _update_conversation_metadata(
        self,
        db: Session,
        conversation_id: int,
        conv_data: dict,
        result: dict
    ) -> None:
        """Update conversation with transaction info from API response."""
        transaction = conv_data.get("transaction", {})
        if not transaction:
            return

        result["transaction_id"] = transaction.get("id")

        conversation = VintedConversationRepository.get_by_id(db, conversation_id)
        if not conversation:
            return

        conversation.transaction_id = transaction.get("id")
        conversation.item_id = transaction.get("item_id")
        conversation.item_title = transaction.get("item_title")

        item_photo = transaction.get("item_photo", {})
        if item_photo:
            conversation.item_photo_url = item_photo.get("url")

        conversation.last_synced_at = datetime.utcnow()
        db.commit()

    def _get_current_user_id(self, conv_data: dict) -> Optional[int]:
        """Get current user ID from conversation data."""
        transaction = conv_data.get("transaction", {})
        current_side = transaction.get("current_user_side")

        if current_side == "buyer":
            return transaction.get("buyer_id")
        elif current_side == "seller":
            return transaction.get("seller_id")

        return None

    def _parse_message(
        self,
        data: dict,
        conversation_id: int,
        current_user_id: Optional[int]
    ) -> dict:
        """Parse message data from Vinted API response."""
        entity_type = data.get("entity_type", "message")
        entity = data.get("entity", {})

        # Parse datetime
        created_at_str = data.get("created_at_ts")
        created_at_vinted = None
        if created_at_str:
            try:
                created_at_vinted = parse_datetime(created_at_str)
            except (ValueError, TypeError):
                pass

        # Get message ID based on entity type
        vinted_message_id = None
        sender_id = None
        body = None
        title = None
        subtitle = None
        offer_price = None
        offer_status = None

        if entity_type == "message":
            vinted_message_id = entity.get("id")
            sender_id = entity.get("user_id")
            body = entity.get("body")

        elif entity_type == "offer_request_message":
            vinted_message_id = entity.get("offer_request_id")
            sender_id = entity.get("user_id")
            title = entity.get("title")
            body = entity.get("body")
            offer_price = entity.get("price")
            offer_status = entity.get("status_title")

        elif entity_type in ("status_message", "action_message"):
            title = entity.get("title")
            subtitle = entity.get("subtitle")

        # Determine if from current user
        is_from_current_user = False
        if current_user_id and sender_id:
            is_from_current_user = sender_id == current_user_id

        return {
            "conversation_id": conversation_id,
            "vinted_message_id": vinted_message_id,
            "entity_type": entity_type,
            "sender_id": sender_id,
            "body": body,
            "title": title,
            "subtitle": subtitle,
            "offer_price": offer_price,
            "offer_status": offer_status,
            "is_from_current_user": is_from_current_user,
            "created_at_vinted": created_at_vinted,
        }

    # =========================================================================
    # LOCAL DB OPERATIONS (no API calls)
    # =========================================================================

    def get_conversations(
        self,
        db: Session,
        page: int = 1,
        per_page: int = 20,
        unread_only: bool = False
    ) -> dict[str, Any]:
        """
        Get conversations from local database.

        Args:
            db: SQLAlchemy Session
            page: Page number (1-indexed)
            per_page: Items per page
            unread_only: Filter to unread only

        Returns:
            dict with conversations and pagination
        """
        conversations = VintedConversationRepository.get_all(
            db, page=page, per_page=per_page, unread_only=unread_only
        )
        total = VintedConversationRepository.count(db, unread_only=unread_only)
        unread_total = VintedConversationRepository.get_unread_count(db)

        return {
            "conversations": [self._conversation_to_dict(c) for c in conversations],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_entries": total,
                "total_pages": (total + per_page - 1) // per_page if per_page > 0 else 0,
            },
            "unread_count": unread_total,
        }

    def get_conversation(
        self,
        db: Session,
        conversation_id: int
    ) -> Optional[dict]:
        """
        Get a single conversation with its messages.

        Args:
            db: SQLAlchemy Session
            conversation_id: Conversation ID

        Returns:
            dict with conversation data and messages, or None if not found
        """
        conversation = VintedConversationRepository.get_by_id(db, conversation_id)
        if not conversation:
            return None

        messages = VintedMessageRepository.get_all_by_conversation(db, conversation_id)

        return {
            "conversation": self._conversation_to_dict(conversation),
            "messages": [self._message_to_dict(m) for m in messages],
        }

    def get_messages(
        self,
        db: Session,
        conversation_id: int,
        page: int = 1,
        per_page: int = 50
    ) -> dict[str, Any]:
        """
        Get messages for a conversation with pagination.

        Args:
            db: SQLAlchemy Session
            conversation_id: Conversation ID
            page: Page number
            per_page: Items per page

        Returns:
            dict with messages and pagination info
        """
        messages = VintedMessageRepository.get_by_conversation(
            db, conversation_id, page=page, per_page=per_page
        )
        total = VintedMessageRepository.count_by_conversation(db, conversation_id)

        return {
            "messages": [self._message_to_dict(m) for m in messages],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_entries": total,
                "total_pages": (total + per_page - 1) // per_page if per_page > 0 else 0,
            },
        }

    def search_messages(
        self,
        db: Session,
        query: str,
        limit: int = 50
    ) -> List[dict]:
        """
        Search messages by content.

        Args:
            db: SQLAlchemy Session
            query: Search term
            limit: Max results

        Returns:
            List of matching message dicts
        """
        messages = VintedMessageRepository.search(db, query, limit=limit)
        return [self._message_to_dict(m) for m in messages]

    # =========================================================================
    # SERIALIZATION HELPERS
    # =========================================================================

    def _conversation_to_dict(self, conv: VintedConversation) -> dict:
        """Convert VintedConversation to dict for API response."""
        return {
            "id": conv.conversation_id,
            "opposite_user": {
                "id": conv.opposite_user_id,
                "login": conv.opposite_user_login,
                "photo_url": conv.opposite_user_photo_url,
            },
            "last_message_preview": conv.last_message_preview,
            "is_unread": conv.is_unread,
            "unread_count": conv.unread_count,
            "item_count": conv.item_count,
            "item": {
                "id": conv.item_id,
                "title": conv.item_title,
                "photo_url": conv.item_photo_url,
            } if conv.item_id else None,
            "transaction_id": conv.transaction_id,
            "updated_at": conv.updated_at_vinted.isoformat() if conv.updated_at_vinted else None,
            "last_synced_at": conv.last_synced_at.isoformat() if conv.last_synced_at else None,
        }

    def _message_to_dict(self, msg: VintedMessage) -> dict:
        """Convert VintedMessage to dict for API response."""
        return {
            "id": msg.id,
            "vinted_message_id": msg.vinted_message_id,
            "entity_type": msg.entity_type,
            "sender": {
                "id": msg.sender_id,
                "login": msg.sender_login,
            } if msg.sender_id else None,
            "body": msg.body,
            "title": msg.title,
            "subtitle": msg.subtitle,
            "offer": {
                "price": msg.offer_price,
                "status": msg.offer_status,
            } if msg.offer_price else None,
            "is_from_current_user": msg.is_from_current_user,
            "created_at": msg.created_at_vinted.isoformat() if msg.created_at_vinted else None,
        }
