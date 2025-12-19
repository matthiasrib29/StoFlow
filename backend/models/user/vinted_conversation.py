"""
VintedConversation & VintedMessage Models - Schema user_{id}

Models for storing Vinted inbox conversations and messages.

Business Rules (2025-12-19):
- conversation_id = Vinted conversation ID (PK)
- Messages have different entity_types: message, offer_request_message, status_message, action_message
- Only 'message' type contains actual user text (body)
- Conversations can be linked to transactions

Author: Claude
Date: 2025-12-19
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base


class VintedConversation(Base):
    """
    Vinted conversation (inbox thread).

    Stores conversation metadata from GET /api/v2/inbox.

    Attributes:
        conversation_id: Vinted conversation ID (PK)
        opposite_user_id: Other participant's Vinted ID
        opposite_user_login: Other participant's username
        opposite_user_photo_url: Avatar URL (thumbnail)
        last_message_preview: Preview of last message (description field)
        unread_count: Number of unread messages (0 if read)
        is_unread: Quick flag for unread status
        item_count: Number of items in conversation
        item_id: Main item ID (if single item)
        item_title: Main item title
        item_photo_url: Main item photo URL
        transaction_id: Linked transaction ID (if any)
        updated_at_vinted: Last update time from Vinted
    """

    __tablename__ = "vinted_conversations"
    __table_args__ = (
        Index("idx_vinted_conversations_opposite_user", "opposite_user_id"),
        Index("idx_vinted_conversations_unread", "is_unread"),
        Index("idx_vinted_conversations_updated", "updated_at_vinted"),
        Index("idx_vinted_conversations_transaction", "transaction_id"),
    )

    # Primary Key = Vinted conversation ID
    conversation_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        comment="Vinted conversation ID (PK)"
    )

    # Opposite user info
    opposite_user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="Other participant Vinted ID"
    )
    opposite_user_login: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Other participant username"
    )
    opposite_user_photo_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Other participant avatar URL"
    )

    # Last message info
    last_message_preview: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Preview of last message"
    )

    # Read status
    is_unread: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Has unread messages"
    )
    unread_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of unread messages"
    )

    # Item info
    item_count: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="Number of items in conversation"
    )
    item_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="Main item Vinted ID"
    )
    item_title: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Main item title"
    )
    item_photo_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Main item photo URL"
    )

    # Transaction link
    transaction_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="Linked transaction ID"
    )

    # Vinted timestamp
    updated_at_vinted: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last update on Vinted"
    )

    # System timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Local creation date"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Local update date"
    )
    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last sync with Vinted"
    )

    # Relationships
    messages: Mapped[list["VintedMessage"]] = relationship(
        "VintedMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="VintedMessage.created_at_vinted"
    )

    def __repr__(self) -> str:
        return (
            f"<VintedConversation(id={self.conversation_id}, "
            f"user={self.opposite_user_login}, unread={self.is_unread})>"
        )


class VintedMessage(Base):
    """
    Vinted message within a conversation.

    Stores individual messages from GET /api/v2/conversations/{id}.

    Entity types:
    - 'message': User text message (has body, photos, user_id)
    - 'offer_request_message': Price offer (has price, status)
    - 'status_message': System message (has title, subtitle)
    - 'action_message': Action required (has actions[])

    Attributes:
        id: Auto-increment PK
        conversation_id: FK to vinted_conversations
        vinted_message_id: Vinted's message ID (unique within conversation)
        entity_type: Type of message (message, offer_request_message, etc.)
        sender_id: Sender's Vinted ID (for 'message' type)
        body: Message text content (for 'message' type)
        title: Title (for status_message, action_message)
        subtitle: Subtitle (for status_message, action_message)
        is_from_current_user: True if sent by current user
        created_at_vinted: Message creation time on Vinted
    """

    __tablename__ = "vinted_messages"
    __table_args__ = (
        Index("idx_vinted_messages_conversation", "conversation_id"),
        Index("idx_vinted_messages_sender", "sender_id"),
        Index("idx_vinted_messages_type", "entity_type"),
        Index("idx_vinted_messages_created", "created_at_vinted"),
    )

    # Primary Key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    # Foreign Key to conversation
    conversation_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("vinted_conversations.conversation_id", ondelete="CASCADE"),
        nullable=False,
        comment="FK to vinted_conversations"
    )

    # Vinted message ID (unique per conversation)
    vinted_message_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="Vinted message ID"
    )

    # Message type
    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="message",
        comment="message, offer_request_message, status_message, action_message"
    )

    # Sender info (for 'message' type)
    sender_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="Sender Vinted ID"
    )
    sender_login: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Sender username"
    )

    # Message content (for 'message' type)
    body: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Message text content"
    )

    # Status/Action message content
    title: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Title for status/action messages"
    )
    subtitle: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Subtitle for status/action messages"
    )

    # Offer info (for 'offer_request_message' type)
    offer_price: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Offer price (e.g., '8.0')"
    )
    offer_status: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Offer status title"
    )

    # Flags
    is_from_current_user: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Sent by current user"
    )

    # Vinted timestamp
    created_at_vinted: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Creation time on Vinted"
    )

    # System timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationship
    conversation: Mapped["VintedConversation"] = relationship(
        "VintedConversation",
        back_populates="messages"
    )

    def __repr__(self) -> str:
        preview = self.body[:30] + "..." if self.body and len(self.body) > 30 else self.body
        return (
            f"<VintedMessage(id={self.id}, type={self.entity_type}, "
            f"body={preview})>"
        )
