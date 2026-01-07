"""add link_product action type

Revision ID: 7d1dc0b3f83e
Revises: ef2af2d8a1c3
Create Date: 2026-01-06 18:38:15.402897+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7d1dc0b3f83e'
down_revision: Union[str, None] = 'ef2af2d8a1c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add link_product action type to vinted.action_types."""
    # Insert link_product action type with explicit id=7
    # (squashed migration used ids 1-6, sequence wasn't updated)
    op.execute("""
        INSERT INTO vinted.action_types (id, code, name, description, priority, is_batch, rate_limit_ms, max_retries, timeout_seconds)
        VALUES (
            7,
            'link_product',
            'Link Product',
            'Link VintedProduct to Product and download images',
            3,
            false,
            500,
            3,
            120
        )
        ON CONFLICT (code) DO NOTHING;
    """)


def downgrade() -> None:
    """Remove link_product action type."""
    op.execute("""
        DELETE FROM vinted.action_types WHERE code = 'link_product';
    """)
