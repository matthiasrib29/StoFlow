"""
Vinted Conversation Repository

Repository for managing Vinted conversations and messages (CRUD operations).
Responsibility: Data access for vinted_conversations and vinted_messages (schema user_{id}).

Architecture:
- Repository pattern for DB isolation
- Standard CRUD operations
- Optimized queries with indexes
- Filters by unread status, date, etc.

Created: 2025-12-19
Author: Claude
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import and_, delete, desc, func, select
from sqlalchemy.orm import Session

from models.user.vinted_conversation import VintedConversation, VintedMessage
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class VintedConversationRepository:
    """
    Repository for VintedConversation operations.

    Provides all CRUD operations and specialized queries.
    """

    # =========================================================================
    # CONVERSATION CRUD
    # =========================================================================

    @staticmethod
    def create(db: Session, conversation: VintedConversation) -> VintedConversation:
        """
        Create a new VintedConversation.

        Args:
            db: SQLAlchemy Session
            conversation: VintedConversation instance to create

        Returns:
            VintedConversation: Created instance
        """
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        logger.info(
            f"[VintedConversationRepo] Conversation created: id={conversation.conversation_id}, "
            f"user={conversation.opposite_user_login}"
        )

        return conversation

    @staticmethod
    def get_by_id(db: Session, conversation_id: int) -> Optional[VintedConversation]:
        """
        Get a VintedConversation by its ID.

        Args:
            db: SQLAlchemy Session
            conversation_id: Vinted conversation ID

        Returns:
            VintedConversation if found, None otherwise
        """
        stmt = select(VintedConversation).where(
            VintedConversation.conversation_id == conversation_id
        )
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_all(
        db: Session,
        page: int = 1,
        per_page: int = 20,
        unread_only: bool = False
    ) -> List[VintedConversation]:
        """
        Get all conversations with pagination.

        Args:
            db: SQLAlchemy Session
            page: Page number (1-indexed)
            per_page: Items per page
            unread_only: Filter to only unread conversations

        Returns:
            List of VintedConversation ordered by updated_at_vinted DESC
        """
        stmt = select(VintedConversation)

        if unread_only:
            stmt = stmt.where(VintedConversation.is_unread == True)

        stmt = stmt.order_by(desc(VintedConversation.updated_at_vinted))

        offset = (page - 1) * per_page
        stmt = stmt.offset(offset).limit(per_page)
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def count(db: Session, unread_only: bool = False) -> int:
        """
        Count total conversations.

        Args:
            db: SQLAlchemy Session
            unread_only: Count only unread conversations

        Returns:
            Total count
        """
        stmt = select(func.count(VintedConversation.conversation_id))

        if unread_only:
            stmt = stmt.where(VintedConversation.is_unread == True)

        return db.execute(stmt).scalar_one() or 0

    @staticmethod
    def update(db: Session, conversation: VintedConversation) -> VintedConversation:
        """
        Update an existing VintedConversation.

        Args:
            db: SQLAlchemy Session
            conversation: VintedConversation instance with updates

        Returns:
            Updated VintedConversation
        """
        db.commit()
        db.refresh(conversation)
        return conversation

    @staticmethod
    def upsert(db: Session, conversation_data: dict) -> VintedConversation:
        """
        Insert or update a conversation based on conversation_id.

        Args:
            db: SQLAlchemy Session
            conversation_data: Dict with conversation fields

        Returns:
            VintedConversation: Created or updated instance
        """
        conversation_id = conversation_data.get("conversation_id")
        existing = VintedConversationRepository.get_by_id(db, conversation_id)

        if existing:
            # Update existing
            for key, value in conversation_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing)
            logger.debug(f"[VintedConversationRepo] Updated conversation {conversation_id}")
            return existing
        else:
            # Create new
            conversation = VintedConversation(**conversation_data)
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            logger.info(f"[VintedConversationRepo] Created conversation {conversation_id}")
            return conversation

    @staticmethod
    def mark_as_read(db: Session, conversation_id: int) -> Optional[VintedConversation]:
        """
        Mark a conversation as read.

        Args:
            db: SQLAlchemy Session
            conversation_id: Conversation ID to mark as read

        Returns:
            Updated VintedConversation or None if not found
        """
        conversation = VintedConversationRepository.get_by_id(db, conversation_id)
        if conversation:
            conversation.is_unread = False
            conversation.unread_count = 0
            db.commit()
            db.refresh(conversation)
            logger.info(f"[VintedConversationRepo] Marked conversation {conversation_id} as read")
        return conversation

    @staticmethod
    def get_unread_count(db: Session) -> int:
        """
        Get total count of unread conversations.

        Args:
            db: SQLAlchemy Session

        Returns:
            Number of unread conversations
        """
        return VintedConversationRepository.count(db, unread_only=True)

    @staticmethod
    def delete(db: Session, conversation_id: int) -> bool:
        """
        Delete a conversation and its messages (cascade).

        Args:
            db: SQLAlchemy Session
            conversation_id: Conversation ID to delete

        Returns:
            True if deleted, False if not found
        """
        conversation = VintedConversationRepository.get_by_id(db, conversation_id)
        if conversation:
            db.delete(conversation)
            db.commit()
            logger.info(f"[VintedConversationRepo] Deleted conversation {conversation_id}")
            return True
        return False


class VintedMessageRepository:
    """
    Repository for VintedMessage operations.

    Provides all CRUD operations and specialized queries.
    """

    # =========================================================================
    # MESSAGE CRUD
    # =========================================================================

    @staticmethod
    def create(db: Session, message: VintedMessage) -> VintedMessage:
        """
        Create a new VintedMessage.

        Args:
            db: SQLAlchemy Session
            message: VintedMessage instance to create

        Returns:
            VintedMessage: Created instance
        """
        db.add(message)
        db.commit()
        db.refresh(message)

        logger.debug(
            f"[VintedMessageRepo] Message created: id={message.id}, "
            f"conv={message.conversation_id}, type={message.entity_type}"
        )

        return message

    @staticmethod
    def create_bulk(db: Session, messages: List[VintedMessage]) -> List[VintedMessage]:
        """
        Create multiple messages at once.

        Args:
            db: SQLAlchemy Session
            messages: List of VintedMessage instances

        Returns:
            List of created VintedMessage instances
        """
        db.add_all(messages)
        db.commit()
        for msg in messages:
            db.refresh(msg)

        logger.info(f"[VintedMessageRepo] Bulk created {len(messages)} messages")
        return messages

    @staticmethod
    def get_by_conversation(
        db: Session,
        conversation_id: int,
        page: int = 1,
        per_page: int = 50
    ) -> List[VintedMessage]:
        """
        Get all messages for a conversation with pagination.

        Args:
            db: SQLAlchemy Session
            conversation_id: Conversation ID
            page: Page number (1-indexed)
            per_page: Items per page

        Returns:
            List of VintedMessage ordered by created_at_vinted ASC
        """
        offset = (page - 1) * per_page

        stmt = (
            select(VintedMessage)
            .where(VintedMessage.conversation_id == conversation_id)
            .order_by(VintedMessage.created_at_vinted)
            .offset(offset)
            .limit(per_page)
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def get_all_by_conversation(db: Session, conversation_id: int) -> List[VintedMessage]:
        """
        Get all messages for a conversation (no pagination).

        Args:
            db: SQLAlchemy Session
            conversation_id: Conversation ID

        Returns:
            List of all VintedMessage ordered by created_at_vinted ASC
        """
        stmt = (
            select(VintedMessage)
            .where(VintedMessage.conversation_id == conversation_id)
            .order_by(VintedMessage.created_at_vinted)
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def count_by_conversation(db: Session, conversation_id: int) -> int:
        """
        Count messages in a conversation.

        Args:
            db: SQLAlchemy Session
            conversation_id: Conversation ID

        Returns:
            Message count
        """
        stmt = (
            select(func.count(VintedMessage.id))
            .where(VintedMessage.conversation_id == conversation_id)
        )
        return db.execute(stmt).scalar_one() or 0

    @staticmethod
    def get_latest_by_conversation(
        db: Session,
        conversation_id: int
    ) -> Optional[VintedMessage]:
        """
        Get the most recent message in a conversation.

        Args:
            db: SQLAlchemy Session
            conversation_id: Conversation ID

        Returns:
            Latest VintedMessage or None
        """
        stmt = (
            select(VintedMessage)
            .where(VintedMessage.conversation_id == conversation_id)
            .order_by(desc(VintedMessage.created_at_vinted))
        )
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def exists_vinted_message_id(
        db: Session,
        conversation_id: int,
        vinted_message_id: int
    ) -> bool:
        """
        Check if a message with given Vinted ID exists in a conversation.

        Args:
            db: SQLAlchemy Session
            conversation_id: Conversation ID
            vinted_message_id: Vinted message ID

        Returns:
            True if exists, False otherwise
        """
        stmt = select(VintedMessage).where(
            and_(
                VintedMessage.conversation_id == conversation_id,
                VintedMessage.vinted_message_id == vinted_message_id
            )
        )
        return db.execute(stmt).scalar_one_or_none() is not None

    @staticmethod
    def delete_by_conversation(db: Session, conversation_id: int) -> int:
        """
        Delete all messages for a conversation.

        Args:
            db: SQLAlchemy Session
            conversation_id: Conversation ID

        Returns:
            Number of deleted messages
        """
        stmt = delete(VintedMessage).where(
            VintedMessage.conversation_id == conversation_id
        )
        result = db.execute(stmt)
        count = result.rowcount
        db.commit()

        logger.info(f"[VintedMessageRepo] Deleted {count} messages for conversation {conversation_id}")
        return count

    @staticmethod
    def search(
        db: Session,
        query: str,
        limit: int = 50
    ) -> List[VintedMessage]:
        """
        Search messages by body content.

        Args:
            db: SQLAlchemy Session
            query: Search term
            limit: Max results

        Returns:
            List of matching VintedMessage
        """
        search_term = f"%{query}%"
        stmt = (
            select(VintedMessage)
            .where(
                and_(
                    VintedMessage.entity_type == "message",
                    VintedMessage.body.ilike(search_term)
                )
            )
            .order_by(desc(VintedMessage.created_at_vinted))
            .limit(limit)
        )
        return list(db.execute(stmt).scalars().all())
