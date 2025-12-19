"""add_vinted_conversations_messages

Revision ID: 20251219_1100
Revises: 20251218_2400
Create Date: 2025-12-19 11:00:00.000000+01:00

This migration adds tables for Vinted messaging/inbox feature.

Tables created (in template_tenant and user_X schemas):
- vinted_conversations: Conversation threads from inbox
- vinted_messages: Individual messages within conversations

Business Rules (2025-12-19):
- conversation_id = Vinted conversation ID (PK)
- Messages have entity_types: message, offer_request_message, status_message, action_message
- Only 'message' type contains actual user text
- Conversations can be linked to transactions

Author: Claude
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251219_1100'
down_revision: Union[str, None] = '20251219_1000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create vinted_conversations and vinted_messages tables."""

    # =========================================================================
    # 1. CREATE TABLES IN template_tenant SCHEMA
    # =========================================================================

    # Table: vinted_conversations
    op.create_table(
        'vinted_conversations',
        # Primary Key
        sa.Column('conversation_id', sa.BigInteger(), nullable=False,
                  comment='Vinted conversation ID (PK)'),

        # Opposite user info
        sa.Column('opposite_user_id', sa.BigInteger(), nullable=True,
                  comment='Other participant Vinted ID'),
        sa.Column('opposite_user_login', sa.String(255), nullable=True,
                  comment='Other participant username'),
        sa.Column('opposite_user_photo_url', sa.Text(), nullable=True,
                  comment='Other participant avatar URL'),

        # Last message info
        sa.Column('last_message_preview', sa.Text(), nullable=True,
                  comment='Preview of last message'),

        # Read status
        sa.Column('is_unread', sa.Boolean(), nullable=False, server_default='false',
                  comment='Has unread messages'),
        sa.Column('unread_count', sa.Integer(), nullable=False, server_default='0',
                  comment='Number of unread messages'),

        # Item info
        sa.Column('item_count', sa.Integer(), nullable=False, server_default='1',
                  comment='Number of items in conversation'),
        sa.Column('item_id', sa.BigInteger(), nullable=True,
                  comment='Main item Vinted ID'),
        sa.Column('item_title', sa.String(255), nullable=True,
                  comment='Main item title'),
        sa.Column('item_photo_url', sa.Text(), nullable=True,
                  comment='Main item photo URL'),

        # Transaction link
        sa.Column('transaction_id', sa.BigInteger(), nullable=True,
                  comment='Linked transaction ID'),

        # Timestamps
        sa.Column('updated_at_vinted', sa.DateTime(timezone=True), nullable=True,
                  comment='Last update on Vinted'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP'),
                  comment='Local creation date'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP'),
                  comment='Local update date'),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True,
                  comment='Last sync with Vinted'),

        sa.PrimaryKeyConstraint('conversation_id'),
        schema='template_tenant'
    )

    # Indexes for vinted_conversations in template_tenant
    op.create_index('idx_vinted_conversations_opposite_user',
                    'vinted_conversations', ['opposite_user_id'],
                    schema='template_tenant')
    op.create_index('idx_vinted_conversations_unread',
                    'vinted_conversations', ['is_unread'],
                    schema='template_tenant')
    op.create_index('idx_vinted_conversations_updated',
                    'vinted_conversations', ['updated_at_vinted'],
                    schema='template_tenant')
    op.create_index('idx_vinted_conversations_transaction',
                    'vinted_conversations', ['transaction_id'],
                    schema='template_tenant')

    # Table: vinted_messages
    op.create_table(
        'vinted_messages',
        # Primary Key
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),

        # Foreign Key
        sa.Column('conversation_id', sa.BigInteger(), nullable=False,
                  comment='FK to vinted_conversations'),

        # Vinted message ID
        sa.Column('vinted_message_id', sa.BigInteger(), nullable=True,
                  comment='Vinted message ID'),

        # Message type
        sa.Column('entity_type', sa.String(50), nullable=False, server_default='message',
                  comment='message, offer_request_message, status_message, action_message'),

        # Sender info
        sa.Column('sender_id', sa.BigInteger(), nullable=True,
                  comment='Sender Vinted ID'),
        sa.Column('sender_login', sa.String(255), nullable=True,
                  comment='Sender username'),

        # Message content (for 'message' type)
        sa.Column('body', sa.Text(), nullable=True,
                  comment='Message text content'),

        # Status/Action message content
        sa.Column('title', sa.Text(), nullable=True,
                  comment='Title for status/action messages'),
        sa.Column('subtitle', sa.Text(), nullable=True,
                  comment='Subtitle for status/action messages'),

        # Offer info (for 'offer_request_message' type)
        sa.Column('offer_price', sa.String(20), nullable=True,
                  comment='Offer price (e.g., 8.0)'),
        sa.Column('offer_status', sa.String(100), nullable=True,
                  comment='Offer status title'),

        # Flags
        sa.Column('is_from_current_user', sa.Boolean(), nullable=False, server_default='false',
                  comment='Sent by current user'),

        # Timestamps
        sa.Column('created_at_vinted', sa.DateTime(timezone=True), nullable=True,
                  comment='Creation time on Vinted'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(
            ['conversation_id'],
            ['template_tenant.vinted_conversations.conversation_id'],
            ondelete='CASCADE'
        ),
        schema='template_tenant'
    )

    # Indexes for vinted_messages in template_tenant
    op.create_index('idx_vinted_messages_conversation',
                    'vinted_messages', ['conversation_id'],
                    schema='template_tenant')
    op.create_index('idx_vinted_messages_sender',
                    'vinted_messages', ['sender_id'],
                    schema='template_tenant')
    op.create_index('idx_vinted_messages_type',
                    'vinted_messages', ['entity_type'],
                    schema='template_tenant')
    op.create_index('idx_vinted_messages_created',
                    'vinted_messages', ['created_at_vinted'],
                    schema='template_tenant')

    # =========================================================================
    # 2. CREATE TABLES IN EXISTING user_X SCHEMAS
    # =========================================================================
    connection = op.get_bind()
    result = connection.execute(sa.text(
        "SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'user_%'"
    ))
    user_schemas = [row[0] for row in result]

    for schema_name in user_schemas:
        # Create vinted_conversations using LIKE template_tenant
        op.execute(f"""
            CREATE TABLE IF NOT EXISTS {schema_name}.vinted_conversations
            (LIKE template_tenant.vinted_conversations INCLUDING ALL)
        """)

        # Create vinted_messages using LIKE template_tenant
        # Note: We need to recreate the FK constraint to point to the correct schema
        op.execute(f"""
            CREATE TABLE IF NOT EXISTS {schema_name}.vinted_messages
            (LIKE template_tenant.vinted_messages INCLUDING ALL)
        """)

        # Add FK constraint for vinted_messages -> vinted_conversations
        op.execute(f"""
            ALTER TABLE {schema_name}.vinted_messages
            DROP CONSTRAINT IF EXISTS vinted_messages_conversation_id_fkey;

            ALTER TABLE {schema_name}.vinted_messages
            ADD CONSTRAINT vinted_messages_conversation_id_fkey
            FOREIGN KEY (conversation_id)
            REFERENCES {schema_name}.vinted_conversations(conversation_id)
            ON DELETE CASCADE;
        """)

        print(f"  ✓ Created vinted_conversations and vinted_messages in {schema_name}")


def downgrade() -> None:
    """Drop vinted_messages and vinted_conversations tables."""

    # =========================================================================
    # 1. DROP TABLES FROM user_X SCHEMAS
    # =========================================================================
    connection = op.get_bind()
    result = connection.execute(sa.text(
        "SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'user_%'"
    ))
    user_schemas = [row[0] for row in result]

    for schema_name in user_schemas:
        op.execute(f"DROP TABLE IF EXISTS {schema_name}.vinted_messages CASCADE")
        op.execute(f"DROP TABLE IF EXISTS {schema_name}.vinted_conversations CASCADE")

    # =========================================================================
    # 2. DROP TABLES FROM template_tenant
    # =========================================================================

    # Drop indexes for vinted_messages
    op.drop_index('idx_vinted_messages_created', table_name='vinted_messages',
                  schema='template_tenant')
    op.drop_index('idx_vinted_messages_type', table_name='vinted_messages',
                  schema='template_tenant')
    op.drop_index('idx_vinted_messages_sender', table_name='vinted_messages',
                  schema='template_tenant')
    op.drop_index('idx_vinted_messages_conversation', table_name='vinted_messages',
                  schema='template_tenant')

    # Drop indexes for vinted_conversations
    op.drop_index('idx_vinted_conversations_transaction', table_name='vinted_conversations',
                  schema='template_tenant')
    op.drop_index('idx_vinted_conversations_updated', table_name='vinted_conversations',
                  schema='template_tenant')
    op.drop_index('idx_vinted_conversations_unread', table_name='vinted_conversations',
                  schema='template_tenant')
    op.drop_index('idx_vinted_conversations_opposite_user', table_name='vinted_conversations',
                  schema='template_tenant')

    # Drop tables (order matters due to FK)
    op.drop_table('vinted_messages', schema='template_tenant')
    op.drop_table('vinted_conversations', schema='template_tenant')
