"""add ebay import action type

Adds the 'import' action type for eBay marketplace.
This action type was missing, causing eBay import jobs to fail with:
"Invalid action code 'import' for marketplace 'ebay'"

Revision ID: a1b2c3d4e5f6
Revises: 8f3a2b1c9d0e
Create Date: 2026-01-19

"""
from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = "b08ea57b8754"
down_revision = "8f3a2b1c9d0e"
branch_labels = None
depends_on = None


def upgrade():
    """
    Insert eBay 'import' action type into public.marketplace_action_types.
    """
    connection = op.get_bind()

    connection.execute(text("""
        INSERT INTO public.marketplace_action_types
        (marketplace, code, name, description, priority, is_batch, rate_limit_ms, max_retries, timeout_seconds)
        VALUES
        (
            'ebay',
            'import',
            'Import Products',
            'Import products from eBay inventory',
            2,
            TRUE,
            2000,
            3,
            600
        )
        ON CONFLICT (marketplace, code) DO NOTHING
    """))

    print("✓ Inserted eBay 'import' action type into public.marketplace_action_types")


def downgrade():
    """
    Remove eBay 'import' action type from public.marketplace_action_types.
    """
    connection = op.get_bind()

    connection.execute(text("""
        DELETE FROM public.marketplace_action_types
        WHERE marketplace = 'ebay' AND code = 'import'
    """))

    print("✓ Removed eBay 'import' action type from public.marketplace_action_types")
