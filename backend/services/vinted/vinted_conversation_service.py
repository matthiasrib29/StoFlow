"""
Vinted Conversation Service - Synchronization of Vinted inbox/messages

Service dedicated to synchronizing conversations and messages from Vinted API.

Methods available:
- sync_inbox(): Sync conversation list from /api/v2/inbox
- sync_conversation(): Sync messages for a specific conversation
- get_conversations(): Get conversations from local DB
- get_messages(): Get messages for a conversation

Author: Claude
Date: 2025-12-19
"""

from datetime import datetime
from typing import Any, List, Optional

from dateutil.parser import parse as parse_datetime
from sqlalchemy import text
from sqlalchemy.orm import Session

from models.user.vinted_conversation import VintedConversation, VintedMessage
from repositories.vinted_conversation_repository import (
    VintedConversationRepository,
    VintedMessageRepository,
)
from services.plugin_task_helper import create_and_wait, _commit_and_restore_path
from shared.vinted_constants import VintedConversationAPI, VintedReferers
from shared.logging_setup import get_logger

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

    def __init__(self):
        """Initialize VintedConversationService."""
        self._current_schema: Optional[str] = None

    def _capture_schema(self, db: Session) -> None:
        """Capture current schema name for later restoration."""
        try:
            result = db.execute(text("SHOW search_path"))
            current_path = result.scalar()
            if current_path:
                for schema in current_path.split(","):
                    schema = schema.strip().strip('"')
                    if schema.startswith("user_"):
                        self._current_schema = schema
                        break
        except Exception:
            pass

    def _restore_search_path(self, db: Session) -> None:
        """Restore PostgreSQL search_path after rollback."""
        try:
            try:
                db.rollback()
            except Exception:
                pass

            if self._current_schema:
                db.execute(text(f"SET LOCAL search_path TO {self._current_schema}, public"))
        except Exception as e:
            logger.warning(f"Could not restore search_path: {e}")

    # =========================================================================
    # SYNC INBOX (list of conversations)
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

        Uses PluginTask to call GET /api/v2/inbox.

        Args:
            db: SQLAlchemy Session
            page: Page to fetch (1-indexed)
            per_page: Items per page (max 20)
            sync_all_pages: If True, fetch all pages until exhausted

        Returns:
            dict with:
            - synced: Number of conversations synced
            - created: Number of new conversations
            - updated: Number of updated conversations
            - total: Total conversations in inbox
            - unread: Number of unread conversations
        """
        self._capture_schema(db)

        result = {
            "synced": 0,
            "created": 0,
            "updated": 0,
            "total": 0,
            "unread": 0,
            "errors": []
        }

        try:
            current_page = page
            has_more = True

            while has_more:
                logger.info(f"[VintedConversationService] Fetching inbox page {current_page}")

                # Call Vinted API via PluginTask
                api_result = await create_and_wait(
                    db=db,
                    http_method="GET",
                    path=VintedConversationAPI.get_inbox(page=current_page, per_page=per_page),
                    referer=VintedReferers.INBOX,
                    description=f"inbox page {current_page}"
                )

                if not api_result:
                    logger.error("[VintedConversationService] No result from inbox API")
                    result["errors"].append(f"Page {current_page}: No API response")
                    break

                # Parse response
                conversations_data = api_result.get("conversations", [])
                pagination = api_result.get("pagination", {})

                result["total"] = pagination.get("total_entries", 0)

                # Process each conversation
                for conv_data in conversations_data:
                    try:
                        conv = self._parse_conversation(conv_data)
                        existing = VintedConversationRepository.get_by_id(
                            db, conv["conversation_id"]
                        )

                        if existing:
                            # Update existing
                            VintedConversationRepository.upsert(db, conv)
                            result["updated"] += 1
                        else:
                            # Create new
                            VintedConversationRepository.upsert(db, conv)
                            result["created"] += 1

                        result["synced"] += 1

                        if conv.get("is_unread"):
                            result["unread"] += 1

                    except Exception as e:
                        conv_id = conv_data.get("id", "unknown")
                        logger.error(f"[VintedConversationService] Error processing conv {conv_id}: {e}")
                        result["errors"].append(f"Conv {conv_id}: {str(e)}")

                # Check if more pages
                total_pages = pagination.get("total_pages", 1)
                if sync_all_pages and current_page < total_pages:
                    current_page += 1
                else:
                    has_more = False

            logger.info(
                f"[VintedConversationService] Inbox sync complete: "
                f"synced={result['synced']}, created={result['created']}, "
                f"updated={result['updated']}, unread={result['unread']}"
            )

            return result

        except Exception as e:
            logger.error(f"[VintedConversationService] sync_inbox error: {e}")
            self._restore_search_path(db)
            raise

    def _parse_conversation(self, data: dict) -> dict:
        """
        Parse conversation data from Vinted API response.

        Args:
            data: Raw conversation data from API

        Returns:
            dict ready for VintedConversation model
        """
        opposite_user = data.get("opposite_user", {})
        opposite_photo = opposite_user.get("photo", {}) or {}
        item_photos = data.get("item_photos", [])
        first_photo = item_photos[0] if item_photos else {}

        # Parse datetime
        updated_at_str = data.get("updated_at")
        updated_at_vinted = None
        if updated_at_str:
            try:
                updated_at_vinted = parse_datetime(updated_at_str)
            except Exception:
                pass

        # Get thumbnail URL (100x100)
        photo_url = None
        thumbnails = opposite_photo.get("thumbnails", [])
        for thumb in thumbnails:
            if thumb.get("type") == "thumb100":
                photo_url = thumb.get("url")
                break
        if not photo_url:
            photo_url = opposite_photo.get("url")

        # Get item photo URL
        item_photo_url = None
        item_thumbnails = first_photo.get("thumbnails", [])
        for thumb in item_thumbnails:
            if thumb.get("type") == "thumb150x210":
                item_photo_url = thumb.get("url")
                break
        if not item_photo_url:
            item_photo_url = first_photo.get("url")

        return {
            "conversation_id": data.get("id"),
            "opposite_user_id": opposite_user.get("id"),
            "opposite_user_login": opposite_user.get("login"),
            "opposite_user_photo_url": photo_url,
            "last_message_preview": data.get("description"),
            "is_unread": data.get("unread", False),
            "unread_count": 1 if data.get("unread") else 0,
            "item_count": data.get("item_count", 1),
            "item_id": first_photo.get("id") if first_photo else None,
            "item_title": data.get("description"),  # Will be updated when syncing conversation
            "item_photo_url": item_photo_url,
            "updated_at_vinted": updated_at_vinted,
            "last_synced_at": datetime.utcnow(),
        }

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
        self._capture_schema(db)

        result = {
            "conversation_id": conversation_id,
            "messages_synced": 0,
            "messages_new": 0,
            "transaction_id": None,
            "errors": []
        }

        try:
            logger.info(f"[VintedConversationService] Syncing conversation {conversation_id}")

            # Call Vinted API via PluginTask
            api_result = await create_and_wait(
                db=db,
                http_method="GET",
                path=VintedConversationAPI.get_conversation(conversation_id),
                referer=VintedReferers.inbox_conversation(conversation_id),
                description=f"conversation {conversation_id}"
            )

            if not api_result:
                logger.error(f"[VintedConversationService] No result for conversation {conversation_id}")
                result["errors"].append("No API response")
                return result

            conv_data = api_result.get("conversation", {})

            # Update conversation metadata
            transaction = conv_data.get("transaction", {})
            if transaction:
                result["transaction_id"] = transaction.get("id")

                # Update conversation with transaction info
                conversation = VintedConversationRepository.get_by_id(db, conversation_id)
                if conversation:
                    conversation.transaction_id = transaction.get("id")
                    conversation.item_id = transaction.get("item_id")
                    conversation.item_title = transaction.get("item_title")

                    # Get item photo from transaction
                    item_photo = transaction.get("item_photo", {})
                    if item_photo:
                        conversation.item_photo_url = item_photo.get("url")

                    conversation.last_synced_at = datetime.utcnow()
                    _commit_and_restore_path(db)

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

                except Exception as e:
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
            self._restore_search_path(db)
            raise

    def _get_current_user_id(self, conv_data: dict) -> Optional[int]:
        """
        Get current user ID from conversation data.

        The current user is the one who is NOT the opposite_user.
        We can infer this from transaction.buyer_id/seller_id and current_user_side.
        """
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
        """
        Parse message data from Vinted API response.

        Args:
            data: Raw message data from API
            conversation_id: Parent conversation ID
            current_user_id: Current user's Vinted ID

        Returns:
            dict ready for VintedMessage model
        """
        entity_type = data.get("entity_type", "message")
        entity = data.get("entity", {})

        # Parse datetime
        created_at_str = data.get("created_at_ts")
        created_at_vinted = None
        if created_at_str:
            try:
                created_at_vinted = parse_datetime(created_at_str)
            except Exception:
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
            dict with:
            - conversations: List of conversation dicts
            - pagination: Pagination info
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
