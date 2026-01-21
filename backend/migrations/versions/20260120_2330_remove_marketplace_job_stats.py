"""Remove marketplace_job_stats table

Revision ID: c45205gd58e1
Revises: b34194fc47d0
Create Date: 2026-01-20 23:30:00

Removes the marketplace_job_stats table as it's not being used.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'c45205gd58e1'
down_revision = 'b34194fc47d0'
branch_labels = None
depends_on = None


def get_tenant_schemas(connection) -> list:
    """Get all tenant schemas (user_X and template_tenant)."""
    result = connection.execute(
        text("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name LIKE 'user_%'
               OR schema_name = 'template_tenant'
        """)
    )
    return [row[0] for row in result]


def table_exists(connection, schema: str, table: str) -> bool:
    """Check if a table exists in a schema."""
    result = connection.execute(
        text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = :schema AND table_name = :table
            )
        """),
        {"schema": schema, "table": table}
    )
    return result.scalar()


def upgrade() -> None:
    """Drop marketplace_job_stats table from all schemas."""
    connection = op.get_bind()
    schemas = get_tenant_schemas(connection)

    for schema in schemas:
        if table_exists(connection, schema, "marketplace_job_stats"):
            # Use CASCADE to drop dependent sequences
            connection.execute(text(f"DROP TABLE IF EXISTS {schema}.marketplace_job_stats CASCADE"))


def downgrade() -> None:
    """Recreate marketplace_job_stats table in all schemas."""
    connection = op.get_bind()
    schemas = get_tenant_schemas(connection)

    for schema in schemas:
        if not table_exists(connection, schema, "marketplace_job_stats"):
            op.create_table(
                "marketplace_job_stats",
                sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
                sa.Column("marketplace", sa.String(20), nullable=False),
                sa.Column("action_type_id", sa.Integer(), nullable=False),
                sa.Column("date", sa.Date(), nullable=False),
                sa.Column("total_jobs", sa.Integer(), nullable=False, server_default="0"),
                sa.Column("success_count", sa.Integer(), nullable=False, server_default="0"),
                sa.Column("failure_count", sa.Integer(), nullable=False, server_default="0"),
                sa.Column("avg_duration_ms", sa.Integer(), nullable=True),
                sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
                sa.UniqueConstraint(
                    "action_type_id", "marketplace", "date",
                    name=f"uq_{schema}_marketplace_job_stats_action_marketplace_date"
                ),
                sa.CheckConstraint(
                    "marketplace IN ('vinted', 'ebay', 'etsy')",
                    name=f"ck_{schema}_marketplace_job_stats_marketplace"
                ),
                schema=schema
            )
            op.create_index(
                f"idx_{schema}_marketplace_job_stats_marketplace",
                "marketplace_job_stats",
                ["marketplace"],
                schema=schema
            )
            op.create_index(
                f"idx_{schema}_marketplace_job_stats_action_type_id",
                "marketplace_job_stats",
                ["action_type_id"],
                schema=schema
            )
            op.create_index(
                f"idx_{schema}_marketplace_job_stats_date",
                "marketplace_job_stats",
                ["date"],
                schema=schema
            )
