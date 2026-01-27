"""create_vinted_pro_sellers_table

Revision ID: c0215cd307b0
Revises: a3f7e1c2d4b6
Create Date: 2026-01-27 11:36:37.778439+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'c0215cd307b0'
down_revision: Union[str, None] = 'a3f7e1c2d4b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(conn, schema, table):
    """Check if table exists."""
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = :schema AND table_name = :table
        )
    """), {"schema": schema, "table": table})
    return result.scalar()


def upgrade() -> None:
    """Create vinted_pro_sellers table in public schema (idempotent)."""
    conn = op.get_bind()

    if table_exists(conn, 'public', 'vinted_pro_sellers'):
        print("  - vinted_pro_sellers table already exists, skipping")
        return

    op.create_table('vinted_pro_sellers',
        # Primary key
        sa.Column('id', sa.Integer(), nullable=False),
        # Vinted user data
        sa.Column('vinted_user_id', sa.BigInteger(), nullable=False, comment='Vinted user ID'),
        sa.Column('login', sa.String(length=255), nullable=False, comment='Vinted username'),
        sa.Column('country_code', sa.String(length=10), nullable=True, comment='Country code (FR, DE, etc.)'),
        sa.Column('country_id', sa.Integer(), nullable=True, comment='Vinted country ID'),
        sa.Column('country_title', sa.String(length=100), nullable=True, comment='Country title'),
        # Seller stats
        sa.Column('item_count', sa.Integer(), nullable=False, server_default='0', comment='Active items for sale'),
        sa.Column('total_items_count', sa.Integer(), nullable=False, server_default='0', comment='Total items ever listed'),
        sa.Column('given_item_count', sa.Integer(), nullable=False, server_default='0', comment='Items given away'),
        sa.Column('taken_item_count', sa.Integer(), nullable=False, server_default='0', comment='Items taken/purchased'),
        sa.Column('followers_count', sa.Integer(), nullable=False, server_default='0', comment='Number of followers'),
        sa.Column('following_count', sa.Integer(), nullable=False, server_default='0', comment='Number of following'),
        sa.Column('feedback_count', sa.Integer(), nullable=False, server_default='0', comment='Number of feedback reviews'),
        sa.Column('feedback_reputation', sa.Numeric(precision=5, scale=2), nullable=True, comment='Reputation score (0-5)'),
        sa.Column('positive_feedback_count', sa.Integer(), nullable=False, server_default='0', comment='Positive feedback count'),
        sa.Column('neutral_feedback_count', sa.Integer(), nullable=False, server_default='0', comment='Neutral feedback count'),
        sa.Column('negative_feedback_count', sa.Integer(), nullable=False, server_default='0', comment='Negative feedback count'),
        sa.Column('is_on_holiday', sa.Boolean(), nullable=False, server_default='false', comment='Is on holiday mode'),
        # Business account info
        sa.Column('business_account_id', sa.BigInteger(), nullable=True, comment='Business account ID'),
        sa.Column('business_name', sa.String(length=255), nullable=True, comment='Business commercial name'),
        sa.Column('legal_name', sa.String(length=255), nullable=True, comment='Legal name'),
        sa.Column('legal_code', sa.String(length=50), nullable=True, comment='SIRET / legal code'),
        sa.Column('entity_type', sa.String(length=50), nullable=True, comment='Entity type code'),
        sa.Column('entity_type_title', sa.String(length=100), nullable=True, comment='Entity type title'),
        sa.Column('nationality', sa.String(length=10), nullable=True, comment='Nationality code'),
        sa.Column('business_country', sa.String(length=10), nullable=True, comment='Business country code'),
        sa.Column('business_city', sa.String(length=255), nullable=True, comment='Business city'),
        sa.Column('verified_identity', sa.Boolean(), nullable=True, comment='Identity verified'),
        sa.Column('business_is_active', sa.Boolean(), nullable=True, comment='Business account is active'),
        # Profile
        sa.Column('about', sa.Text(), nullable=True, comment='Bio/about text (raw)'),
        sa.Column('profile_url', sa.String(length=500), nullable=True, comment='URL to Vinted profile'),
        sa.Column('last_loged_on_ts', sa.String(length=50), nullable=True, comment='Last login timestamp'),
        # Extracted contacts
        sa.Column('contact_email', sa.String(length=255), nullable=True, comment='Extracted email'),
        sa.Column('contact_instagram', sa.String(length=255), nullable=True, comment='Extracted Instagram handle'),
        sa.Column('contact_tiktok', sa.String(length=255), nullable=True, comment='Extracted TikTok handle'),
        sa.Column('contact_youtube', sa.String(length=500), nullable=True, comment='Extracted YouTube channel'),
        sa.Column('contact_website', sa.String(length=500), nullable=True, comment='Extracted website URL'),
        sa.Column('contact_phone', sa.String(length=50), nullable=True, comment='Extracted phone number'),
        # Metadata
        sa.Column('marketplace', sa.String(length=20), nullable=False, server_default='vinted_fr', comment='Marketplace origin'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='new', comment='Prospection status'),
        sa.Column('notes', sa.Text(), nullable=True, comment='Admin notes'),
        # Timestamps
        sa.Column('discovered_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_scanned_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('contacted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='Admin user ID'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        # Constraints
        sa.PrimaryKeyConstraint('id', name=op.f('pk_vinted_pro_sellers')),
        sa.UniqueConstraint('vinted_user_id', name=op.f('uq_vinted_pro_sellers_vinted_user_id')),
        schema='public',
    )

    # Create indexes
    op.create_index('idx_vinted_pro_sellers_vinted_user_id', 'vinted_pro_sellers', ['vinted_user_id'], unique=True, schema='public')
    op.create_index('idx_vinted_pro_sellers_country_code', 'vinted_pro_sellers', ['country_code'], unique=False, schema='public')
    op.create_index('idx_vinted_pro_sellers_marketplace', 'vinted_pro_sellers', ['marketplace'], unique=False, schema='public')
    op.create_index('idx_vinted_pro_sellers_status', 'vinted_pro_sellers', ['status'], unique=False, schema='public')
    op.create_index('idx_vinted_pro_sellers_item_count', 'vinted_pro_sellers', ['item_count'], unique=False, schema='public')
    op.create_index('idx_vinted_pro_sellers_legal_code', 'vinted_pro_sellers', ['legal_code'], unique=False, schema='public')

    print("  + Created vinted_pro_sellers table with 6 indexes")


def downgrade() -> None:
    """Drop vinted_pro_sellers table."""
    op.drop_index('idx_vinted_pro_sellers_legal_code', table_name='vinted_pro_sellers', schema='public')
    op.drop_index('idx_vinted_pro_sellers_item_count', table_name='vinted_pro_sellers', schema='public')
    op.drop_index('idx_vinted_pro_sellers_status', table_name='vinted_pro_sellers', schema='public')
    op.drop_index('idx_vinted_pro_sellers_marketplace', table_name='vinted_pro_sellers', schema='public')
    op.drop_index('idx_vinted_pro_sellers_country_code', table_name='vinted_pro_sellers', schema='public')
    op.drop_index('idx_vinted_pro_sellers_vinted_user_id', table_name='vinted_pro_sellers', schema='public')
    op.drop_table('vinted_pro_sellers', schema='public')
