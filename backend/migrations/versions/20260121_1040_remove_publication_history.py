"""remove publication_history table

Removes the obsolete publication_history table.
This functionality is now covered by:
- MarketplaceJob: tracks all publication operations
- VintedProduct/EbayProduct: stores platform IDs and URLs

Revision ID: a2b3c4d5e6f7
Revises: f7a8b9c0d1e2
Create Date: 2026-01-21

"""
from alembic import op
from sqlalchemy import text

from logging import getLogger

logger = getLogger(__name__)


# revision identifiers, used by Alembic.
revision = "a2b3c4d5e6f7"
down_revision = "f7a8b9c0d1e2"
branch_labels = None
depends_on = None


def upgrade():
    """Drop publication_history table from all user schemas."""
    connection = op.get_bind()

    # Get all user_X schemas and template_tenant
    result = connection.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%' OR schema_name = 'template_tenant'
        ORDER BY schema_name
    """))
    schemas = [row[0] for row in result]

    logger.info(f"Dropping publication_history table from {len(schemas)} schemas...")

    for schema in schemas:
        # Check if table exists before dropping
        table_exists = connection.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = :schema AND table_name = 'publication_history'
            )
        """), {"schema": schema}).scalar()

        if table_exists:
            logger.info(f"  - Dropping from {schema}")
            connection.execute(text(f'DROP TABLE IF EXISTS "{schema}".publication_history CASCADE'))
        else:
            logger.info(f"  - Skipping {schema} (table does not exist)")

    # Also drop the enum type if it exists
    connection.execute(text("""
        DROP TYPE IF EXISTS publication_status CASCADE
    """))

    logger.info("Dropped publication_history table from all schemas")


def downgrade():
    """Recreate publication_history table in all user schemas."""
    connection = op.get_bind()

    # Recreate enum type
    connection.execute(text("""
        DO $$ BEGIN
            CREATE TYPE publication_status AS ENUM ('pending', 'success', 'failed');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$
    """))

    # Get all user_X schemas and template_tenant
    result = connection.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%' OR schema_name = 'template_tenant'
        ORDER BY schema_name
    """))
    schemas = [row[0] for row in result]

    logger.info(f"Recreating publication_history table in {len(schemas)} schemas...")

    for schema in schemas:
        logger.info(f"  - Creating in {schema}")
        connection.execute(text(f"""
            CREATE TABLE IF NOT EXISTS "{schema}".publication_history (
                id SERIAL PRIMARY KEY,
                product_id INTEGER NOT NULL REFERENCES "{schema}".products(id) ON DELETE CASCADE,
                platform VARCHAR(50) NOT NULL,
                status publication_status NOT NULL DEFAULT 'pending',
                platform_product_id VARCHAR(100),
                platform_url VARCHAR(500),
                error_message TEXT,
                published_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            )
        """))

        # Create indexes
        connection.execute(text(f"""
            CREATE INDEX IF NOT EXISTS idx_publication_history_product_id
            ON "{schema}".publication_history (product_id)
        """))
        connection.execute(text(f"""
            CREATE INDEX IF NOT EXISTS idx_publication_history_platform
            ON "{schema}".publication_history (platform)
        """))
        connection.execute(text(f"""
            CREATE INDEX IF NOT EXISTS idx_publication_history_status
            ON "{schema}".publication_history (status)
        """))
        connection.execute(text(f"""
            CREATE INDEX IF NOT EXISTS idx_publication_history_published_at
            ON "{schema}".publication_history (published_at)
        """))

    logger.info("Recreated publication_history table in all schemas")
