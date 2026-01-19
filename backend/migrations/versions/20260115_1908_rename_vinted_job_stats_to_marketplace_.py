"""rename vinted_job_stats to marketplace_job_stats and add marketplace column

Revision ID: 307a8e381a2b
Revises: 381503c3aa77
Create Date: 2026-01-15 19:08:02.703593+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '307a8e381a2b'
down_revision: Union[str, None] = '381503c3aa77'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(conn, table):
    """Check if table exists in template_tenant schema."""
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'template_tenant' AND table_name = :table
        )
    """), {"table": table})
    return result.scalar()


def upgrade() -> None:
    """
    Refactor stats tracking to be marketplace-agnostic:
    - Add marketplace column with check constraint
    - Update unique constraint to include marketplace
    - Add index for marketplace queries
    - Rename table from vinted_job_stats to marketplace_job_stats

    Note: schema='tenant' handled by schema_translate_map in env.py
    """
    conn = op.get_bind()

    # Check if already migrated (marketplace_job_stats exists)
    if table_exists(conn, 'marketplace_job_stats'):
        print("  - marketplace_job_stats already exists, skipping migration")
        return

    # Check if source table exists
    if not table_exists(conn, 'vinted_job_stats'):
        print("  - vinted_job_stats does not exist, skipping migration")
        return

    # Add marketplace column with default 'vinted' for existing rows
    op.add_column(
        'vinted_job_stats',
        sa.Column('marketplace', sa.String(20), nullable=False, server_default='vinted')
    )

    # Add check constraint for valid marketplace values
    op.create_check_constraint(
        'ck_marketplace_job_stats_marketplace',
        'vinted_job_stats',
        "marketplace IN ('vinted', 'ebay', 'etsy')"
    )

    # Drop old unique constraint (actual DB name, not from model)
    op.drop_constraint(
        'vinted_job_stats_action_type_id_date_key',
        'vinted_job_stats',
        type_='unique'
    )

    # Add new unique constraint including marketplace
    op.create_unique_constraint(
        'uq_marketplace_job_stats_action_marketplace_date',
        'vinted_job_stats',
        ['action_type_id', 'marketplace', 'date']
    )

    # Add index for marketplace queries
    op.create_index(
        'ix_marketplace_job_stats_marketplace_created_at',
        'vinted_job_stats',
        ['marketplace', 'created_at']
    )

    # Rename table
    op.rename_table(
        'vinted_job_stats',
        'marketplace_job_stats'
    )
    print("  ✓ Renamed vinted_job_stats to marketplace_job_stats")


def downgrade() -> None:
    """
    Revert stats refactoring:
    - Rename table back to vinted_job_stats
    - Drop marketplace index
    - Restore original unique constraint
    - Drop marketplace column

    Note: schema='tenant' handled by schema_translate_map in env.py
    """
    # Rename table back
    op.rename_table(
        'marketplace_job_stats',
        'vinted_job_stats'
    )

    # Drop marketplace index
    op.drop_index(
        'ix_marketplace_job_stats_marketplace_created_at',
        'vinted_job_stats'
    )

    # Drop new unique constraint
    op.drop_constraint(
        'uq_marketplace_job_stats_action_marketplace_date',
        'vinted_job_stats',
        type_='unique'
    )

    # Restore old unique constraint (let PostgreSQL auto-generate name)
    op.create_unique_constraint(
        'vinted_job_stats_action_type_id_date_key',
        'vinted_job_stats',
        ['action_type_id', 'date']
    )

    # Drop check constraint
    op.drop_constraint(
        'ck_marketplace_job_stats_marketplace',
        'vinted_job_stats',
        type_='check'
    )

    # Drop marketplace column
    op.drop_column('vinted_job_stats', 'marketplace')
