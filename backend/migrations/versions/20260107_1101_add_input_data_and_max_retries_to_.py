"""add_input_data_and_max_retries_to_marketplace_jobs

Add input_data (JSONB) and max_retries (INTEGER) to marketplace_jobs table
in template_tenant and all user_X schemas.

Revision ID: 4fcb2f0387ba
Revises: 9ce74bed2321
Create Date: 2026-01-07 11:01:36.748120+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '4fcb2f0387ba'
down_revision: Union[str, None] = '9ce74bed2321'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add input_data and max_retries columns to marketplace_jobs."""
    conn = op.get_bind()

    # Helper to check if table exists in schema
    def table_exists(schema_name: str, table_name: str) -> bool:
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = :schema AND table_name = :table
            )
        """), {"schema": schema_name, "table": table_name})
        return result.scalar()

    # Apply to template_tenant first
    if table_exists('template_tenant', 'marketplace_jobs'):
        op.add_column(
            'marketplace_jobs',
            sa.Column('input_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True,
                      comment='Job input parameters'),
            schema='template_tenant'
        )
        op.add_column(
            'marketplace_jobs',
            sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3',
                      comment='Maximum retry attempts'),
            schema='template_tenant'
        )

    # Apply to all existing user_X schemas
    result = conn.execute(text("""
        SELECT nspname FROM pg_namespace
        WHERE nspname LIKE 'user_%'
        ORDER BY nspname
    """))

    for (schema_name,) in result:
        if table_exists(schema_name, 'marketplace_jobs'):
            op.add_column(
                'marketplace_jobs',
                sa.Column('input_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True,
                          comment='Job input parameters'),
                schema=schema_name
            )
            op.add_column(
                'marketplace_jobs',
                sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3',
                          comment='Maximum retry attempts'),
                schema=schema_name
            )


def downgrade() -> None:
    """Remove input_data and max_retries columns from marketplace_jobs."""
    conn = op.get_bind()

    # Helper to check if table exists in schema
    def table_exists(schema_name: str, table_name: str) -> bool:
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = :schema AND table_name = :table
            )
        """), {"schema": schema_name, "table": table_name})
        return result.scalar()

    # Remove from template_tenant
    if table_exists('template_tenant', 'marketplace_jobs'):
        op.drop_column('marketplace_jobs', 'max_retries', schema='template_tenant')
        op.drop_column('marketplace_jobs', 'input_data', schema='template_tenant')

    # Remove from all user_X schemas
    result = conn.execute(text("""
        SELECT nspname FROM pg_namespace
        WHERE nspname LIKE 'user_%'
        ORDER BY nspname
    """))

    for (schema_name,) in result:
        if table_exists(schema_name, 'marketplace_jobs'):
            op.drop_column('marketplace_jobs', 'max_retries', schema=schema_name)
            op.drop_column('marketplace_jobs', 'input_data', schema=schema_name)
