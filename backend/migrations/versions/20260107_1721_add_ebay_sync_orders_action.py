"""add_ebay_sync_orders_action

Revision ID: f8a4a4d3ec7e
Revises: 4d2e58dae912
Create Date: 2026-01-07 17:21:18.616786+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f8a4a4d3ec7e'
down_revision: Union[str, None] = '4d2e58dae912'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add sync_orders_ebay action type to vinted.action_types."""
    # Insert sync_orders_ebay action type with explicit id=8
    # (id=7 was used by link_product)
    op.execute("""
        INSERT INTO vinted.action_types (id, code, name, description, priority, is_batch, rate_limit_ms, max_retries, timeout_seconds)
        VALUES (
            8,
            'sync_orders_ebay',
            'Synchroniser les commandes eBay',
            'Synchronise les commandes depuis eBay Fulfillment API vers la base de données locale',
            2,
            false,
            2000,
            3,
            300
        )
        ON CONFLICT (code) DO NOTHING;
    """)


def downgrade() -> None:
    """Remove sync_orders_ebay action type."""
    op.execute("""
        DELETE FROM vinted.action_types WHERE code = 'sync_orders_ebay';
    """)
