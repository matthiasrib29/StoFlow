"""create_ai_credit_packs_table

Create ai_credit_packs table to store purchasable AI credit packs.
Seed with Notion pricing strategy packs (25, 75, 200 credits).

Revision ID: 78c0a01b2a38
Revises: 85be05b7612e
Create Date: 2026-01-14 11:16:29.195907+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '78c0a01b2a38'
down_revision: Union[str, None] = '85be05b7612e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Packs from Notion pricing strategy
CREDIT_PACKS = [
    {
        "credits": 25,
        "price": 1.99,
        "is_popular": False,
        "display_order": 1,
    },
    {
        "credits": 75,
        "price": 4.99,
        "is_popular": True,
        "display_order": 2,
    },
    {
        "credits": 200,
        "price": 9.99,
        "is_popular": False,
        "display_order": 3,
    },
]


def table_exists(conn, schema: str, table: str) -> bool:
    """Check if a table exists."""
    result = conn.execute(
        text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = :schema AND table_name = :table
            )
        """),
        {"schema": schema, "table": table}
    )
    return result.scalar()


def index_exists(conn, schema: str, index_name: str) -> bool:
    """Check if an index exists."""
    result = conn.execute(
        text("""
            SELECT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = :schema AND indexname = :index_name
            )
        """),
        {"schema": schema, "index_name": index_name}
    )
    return result.scalar()


def upgrade() -> None:
    """Create ai_credit_packs table and seed with initial data."""
    conn = op.get_bind()

    # Create table if not exists
    if not table_exists(conn, 'public', 'ai_credit_packs'):
        op.create_table(
            'ai_credit_packs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('credits', sa.Integer(), nullable=False, comment='Number of AI credits in this pack'),
            sa.Column('price', sa.DECIMAL(precision=10, scale=2), nullable=False, comment='Price in euros'),
            sa.Column('is_popular', sa.Boolean(), nullable=False, server_default='false', comment='Show as popular/recommended'),
            sa.Column('display_order', sa.Integer(), nullable=False, default=0, comment='Order of display (lower = first)'),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='Pack is available for purchase'),
            sa.PrimaryKeyConstraint('id'),
            schema='public'
        )

    # Create index on display_order for sorting if not exists
    if not index_exists(conn, 'public', 'ix_ai_credit_packs_display_order'):
        op.create_index('ix_ai_credit_packs_display_order', 'ai_credit_packs', ['display_order'], schema='public')

    # Seed initial packs (idempotent with ON CONFLICT)
    for pack in CREDIT_PACKS:
        conn.execute(
            text("""
                INSERT INTO public.ai_credit_packs (credits, price, is_popular, display_order)
                VALUES (:credits, :price, :is_popular, :display_order)
                ON CONFLICT DO NOTHING
            """),
            pack
        )


def downgrade() -> None:
    """Drop ai_credit_packs table."""
    op.drop_index('ix_ai_credit_packs_display_order', table_name='ai_credit_packs', schema='public')
    op.drop_table('ai_credit_packs', schema='public')
