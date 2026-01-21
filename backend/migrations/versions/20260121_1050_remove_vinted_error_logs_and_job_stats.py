"""remove vinted_error_logs and vinted_job_stats tables

Removes obsolete tables:
- vinted_error_logs: Never used (dead code)
- vinted_job_stats: Replaced by MarketplaceTask + TaskMetricsService

Revision ID: b3c4d5e6f7a8
Revises: a2b3c4d5e6f7
Create Date: 2026-01-21

"""
from alembic import op
from sqlalchemy import text

from logging import getLogger

logger = getLogger(__name__)


# revision identifiers, used by Alembic.
revision = "b3c4d5e6f7a8"
down_revision = "a2b3c4d5e6f7"
branch_labels = None
depends_on = None


def upgrade():
    """Drop vinted_error_logs and vinted_job_stats tables from all user schemas."""
    connection = op.get_bind()

    # Get all user_X schemas and template_tenant
    result = connection.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%' OR schema_name = 'template_tenant'
        ORDER BY schema_name
    """))
    schemas = [row[0] for row in result]

    tables_to_drop = ["vinted_error_logs", "vinted_job_stats"]

    for table_name in tables_to_drop:
        logger.info(f"Dropping {table_name} table from {len(schemas)} schemas...")

        for schema in schemas:
            # Check if table exists before dropping
            table_exists = connection.execute(text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = :schema AND table_name = :table
                )
            """), {"schema": schema, "table": table_name}).scalar()

            if table_exists:
                logger.info(f"  - Dropping {table_name} from {schema}")
                connection.execute(text(f'DROP TABLE IF EXISTS "{schema}".{table_name} CASCADE'))
            else:
                logger.info(f"  - Skipping {schema} ({table_name} does not exist)")

        logger.info(f"Dropped {table_name} from all schemas")


def downgrade():
    """Recreate vinted_error_logs and vinted_job_stats tables."""
    connection = op.get_bind()

    # Get all user_X schemas and template_tenant
    result = connection.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%' OR schema_name = 'template_tenant'
        ORDER BY schema_name
    """))
    schemas = [row[0] for row in result]

    logger.info(f"Recreating tables in {len(schemas)} schemas...")

    for schema in schemas:
        logger.info(f"  - Creating tables in {schema}")

        # Recreate vinted_error_logs
        connection.execute(text(f"""
            CREATE TABLE IF NOT EXISTS "{schema}".vinted_error_logs (
                id SERIAL PRIMARY KEY,
                product_id INTEGER NOT NULL REFERENCES "{schema}".products(id) ON DELETE CASCADE,
                operation VARCHAR(20) NOT NULL,
                error_type VARCHAR(50) NOT NULL,
                error_message TEXT NOT NULL,
                error_details TEXT,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            )
        """))

        connection.execute(text(f"""
            CREATE INDEX IF NOT EXISTS idx_vinted_error_logs_product_id
            ON "{schema}".vinted_error_logs (product_id)
        """))
        connection.execute(text(f"""
            CREATE INDEX IF NOT EXISTS idx_vinted_error_logs_error_type
            ON "{schema}".vinted_error_logs (error_type)
        """))
        connection.execute(text(f"""
            CREATE INDEX IF NOT EXISTS idx_vinted_error_logs_created_at
            ON "{schema}".vinted_error_logs (created_at)
        """))

        # Recreate vinted_job_stats
        connection.execute(text(f"""
            CREATE TABLE IF NOT EXISTS "{schema}".vinted_job_stats (
                id SERIAL PRIMARY KEY,
                marketplace VARCHAR(50) NOT NULL DEFAULT 'vinted',
                action_type_id INTEGER NOT NULL,
                date DATE NOT NULL,
                total_jobs INTEGER NOT NULL DEFAULT 0,
                success_count INTEGER NOT NULL DEFAULT 0,
                failure_count INTEGER NOT NULL DEFAULT 0,
                avg_duration_ms INTEGER,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                UNIQUE (marketplace, action_type_id, date)
            )
        """))

    logger.info("Recreated tables in all schemas")
