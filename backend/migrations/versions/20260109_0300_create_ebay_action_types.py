"""create ebay action types

Inserts eBay action types into public.marketplace_action_types.
This migration must run after 20260109_0200_unify_action_types.

Revision ID: 20260109_0300
Revises: 20260109_0200
Create Date: 2026-01-09

"""
from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = "20260109_0300"
down_revision = "20260109_0200"
branch_labels = None
depends_on = None


def upgrade():
    """
    Insert eBay action types into public.marketplace_action_types.
    """
    connection = op.get_bind()

    connection.execute(text("""
        INSERT INTO public.marketplace_action_types
        (marketplace, code, name, description, priority, is_batch, rate_limit_ms, max_retries, timeout_seconds)
        VALUES
        (
            'ebay',
            'publish',
            'Publish Product',
            'Create inventory item and offer on eBay',
            3,
            FALSE,
            1000,
            3,
            60
        ),
        (
            'ebay',
            'update',
            'Update Product',
            'Update existing eBay listing',
            3,
            FALSE,
            1000,
            3,
            60
        ),
        (
            'ebay',
            'delete',
            'Delete Product',
            'Delete/end eBay listing',
            3,
            FALSE,
            1000,
            3,
            60
        ),
        (
            'ebay',
            'sync',
            'Sync Products',
            'Sync all products from eBay inventory',
            2,
            TRUE,
            2000,
            3,
            300
        ),
        (
            'ebay',
            'sync_orders',
            'Sync Orders',
            'Sync orders from eBay',
            2,
            TRUE,
            2000,
            3,
            300
        )
        ON CONFLICT (marketplace, code) DO NOTHING
    """))

    print("✓ Inserted 5 eBay action types into public.marketplace_action_types")


def downgrade():
    """
    Remove eBay action types from public.marketplace_action_types.
    """
    connection = op.get_bind()

    connection.execute(text("""
        DELETE FROM public.marketplace_action_types
        WHERE marketplace = 'ebay'
    """))

    print("✓ Removed eBay action types from public.marketplace_action_types")
