"""create etsy action types

Inserts Etsy action types into public.marketplace_action_types.
This migration must run after 20260109_0300_create_ebay_action_types.

Revision ID: 20260109_0400
Revises: 20260109_0300
Create Date: 2026-01-09

"""
from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = "20260109_0400"
down_revision = "20260109_0300"
branch_labels = None
depends_on = None


def upgrade():
    """
    Insert Etsy action types into public.marketplace_action_types.
    """
    connection = op.get_bind()

    connection.execute(text("""
        INSERT INTO public.marketplace_action_types
        (marketplace, code, name, description, priority, is_batch, rate_limit_ms, max_retries, timeout_seconds)
        VALUES
        (
            'etsy',
            'publish',
            'Publish Product',
            'Create listing on Etsy',
            3,
            FALSE,
            1000,
            3,
            60
        ),
        (
            'etsy',
            'update',
            'Update Product',
            'Update existing Etsy listing',
            3,
            FALSE,
            1000,
            3,
            60
        ),
        (
            'etsy',
            'delete',
            'Delete Product',
            'Delete/deactivate Etsy listing',
            3,
            FALSE,
            1000,
            3,
            60
        ),
        (
            'etsy',
            'sync',
            'Sync Products',
            'Sync all products from Etsy shop',
            2,
            TRUE,
            2000,
            3,
            300
        ),
        (
            'etsy',
            'sync_orders',
            'Sync Orders',
            'Sync orders from Etsy',
            2,
            TRUE,
            2000,
            3,
            300
        )
        ON CONFLICT (marketplace, code) DO NOTHING
    """))

    print("✓ Inserted 5 Etsy action types into public.marketplace_action_types")


def downgrade():
    """
    Remove Etsy action types from public.marketplace_action_types.
    """
    connection = op.get_bind()

    connection.execute(text("""
        DELETE FROM public.marketplace_action_types
        WHERE marketplace = 'etsy'
    """))

    print("✓ Removed Etsy action types from public.marketplace_action_types")
