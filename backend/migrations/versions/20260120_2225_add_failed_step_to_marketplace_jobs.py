"""add_failed_step_to_marketplace_jobs

Add failed_step column to marketplace_jobs table to track which step
caused a job failure. This provides better error diagnosis without
the overhead of full MarketplaceTask tracking.

Revision ID: a23083ebf36c
Revises: f5ac88970130
Create Date: 2026-01-20 22:25:30.976291+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'a23083ebf36c'
down_revision: Union[str, None] = 'f5ac88970130'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_tenant_schemas(conn) -> list[str]:
    """Get all tenant schemas (user_X and template_tenant)."""
    result = conn.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
           OR schema_name = 'template_tenant'
        ORDER BY schema_name
    """))
    return [row[0] for row in result.fetchall()]


def column_exists(conn, schema: str, table: str, column: str) -> bool:
    """Check if a column exists in a table."""
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = :schema
              AND table_name = :table
              AND column_name = :column
        )
    """), {"schema": schema, "table": table, "column": column})
    return result.scalar()


def upgrade() -> None:
    conn = op.get_bind()
    schemas = get_tenant_schemas(conn)

    for schema in schemas:
        if not column_exists(conn, schema, "marketplace_jobs", "failed_step"):
            op.add_column(
                "marketplace_jobs",
                sa.Column(
                    "failed_step",
                    sa.String(100),
                    nullable=True,
                    comment="Step where the job failed (e.g., 'upload_images', 'create_listing')"
                ),
                schema=schema
            )
            print(f"  Added failed_step column to {schema}.marketplace_jobs")


def downgrade() -> None:
    conn = op.get_bind()
    schemas = get_tenant_schemas(conn)

    for schema in schemas:
        if column_exists(conn, schema, "marketplace_jobs", "failed_step"):
            op.drop_column("marketplace_jobs", "failed_step", schema=schema)
            print(f"  Dropped failed_step column from {schema}.marketplace_jobs")
