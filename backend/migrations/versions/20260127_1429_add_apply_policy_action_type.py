"""add_apply_policy_action_type

Inserts the 'apply_policy' action type for eBay into public.marketplace_action_types.

Revision ID: 20260127_0100
Revises: 56c6e9d7806a
Create Date: 2026-01-27

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '20260127_0100'
down_revision: Union[str, None] = '56c6e9d7806a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Insert apply_policy action type for eBay."""
    connection = op.get_bind()

    connection.execute(text("""
        INSERT INTO public.marketplace_action_types
        (marketplace, code, name, description, priority, is_batch, rate_limit_ms, max_retries, timeout_seconds)
        VALUES
        (
            'ebay',
            'apply_policy',
            'Apply Policy',
            'Apply a business policy to all existing eBay offers',
            3,
            TRUE,
            1000,
            3,
            300
        )
        ON CONFLICT (marketplace, code) DO NOTHING
    """))

    print("✓ Inserted apply_policy action type for eBay")


def downgrade() -> None:
    """Remove apply_policy action type for eBay."""
    connection = op.get_bind()

    connection.execute(text("""
        DELETE FROM public.marketplace_action_types
        WHERE marketplace = 'ebay' AND code = 'apply_policy'
    """))

    print("✓ Removed apply_policy action type for eBay")
