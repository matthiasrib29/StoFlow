"""remove pending_instructions and add check_connection action type

Removes the obsolete pending_instructions table (replaced by MarketplaceJob + WebSocket)
and adds the check_connection action type for Vinted.

Flow migration:
- OLD: Frontend polling → PendingInstruction → callback → update connection
- NEW: MarketplaceJob → WebSocket → Plugin → job result → update connection

Revision ID: f7a8b9c0d1e2
Revises: d56316he69f2
Create Date: 2026-01-21

"""
from alembic import op
from sqlalchemy import text

from logging import getLogger

logger = getLogger(__name__)


# revision identifiers, used by Alembic.
revision = "f7a8b9c0d1e2"
down_revision = "d56316he69f2"
branch_labels = None
depends_on = None


def upgrade():
    """
    1. Drop pending_instructions table from all user schemas
    2. Add check_connection action type for Vinted
    """
    connection = op.get_bind()

    # ===== PART 1: Drop pending_instructions table =====

    # Get all user_X schemas and template_tenant
    result = connection.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%' OR schema_name = 'template_tenant'
        ORDER BY schema_name
    """))
    schemas = [row[0] for row in result]

    logger.info(f"Dropping pending_instructions table from {len(schemas)} schemas...")

    for schema in schemas:
        # Check if table exists before dropping
        table_exists = connection.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = :schema AND table_name = 'pending_instructions'
            )
        """), {"schema": schema}).scalar()

        if table_exists:
            logger.info(f"  - Dropping from {schema}")
            connection.execute(text(f'DROP TABLE IF EXISTS "{schema}".pending_instructions CASCADE'))
        else:
            logger.info(f"  - Skipping {schema} (table does not exist)")

    logger.info("Dropped pending_instructions table from all schemas")

    # ===== PART 2: Add check_connection action type =====

    connection.execute(text("""
        INSERT INTO public.marketplace_action_types
        (marketplace, code, name, description, priority, is_batch, rate_limit_ms, max_retries, timeout_seconds)
        VALUES
        (
            'vinted',
            'check_connection',
            'Check Connection',
            'Verify Vinted connection status by calling GET /api/v2/users/current via plugin',
            2,
            FALSE,
            1000,
            2,
            30
        )
        ON CONFLICT (marketplace, code) DO NOTHING
    """))

    logger.info("Added check_connection action type for Vinted")


def downgrade():
    """
    1. Recreate pending_instructions table in all user schemas
    2. Remove check_connection action type
    """
    connection = op.get_bind()

    # ===== PART 1: Remove check_connection action type =====

    connection.execute(text("""
        DELETE FROM public.marketplace_action_types
        WHERE marketplace = 'vinted' AND code = 'check_connection'
    """))

    logger.info("Removed check_connection action type for Vinted")

    # ===== PART 2: Recreate pending_instructions table =====

    # Get all user_X schemas and template_tenant
    result = connection.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%' OR schema_name = 'template_tenant'
        ORDER BY schema_name
    """))
    schemas = [row[0] for row in result]

    logger.info(f"Recreating pending_instructions table in {len(schemas)} schemas...")

    for schema in schemas:
        logger.info(f"  - Creating in {schema}")
        connection.execute(text(f"""
            CREATE TABLE IF NOT EXISTS "{schema}".pending_instructions (
                id VARCHAR(36) PRIMARY KEY,
                user_id INTEGER NOT NULL,
                action VARCHAR(100) NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                result JSONB,
                error TEXT,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                completed_at TIMESTAMP WITH TIME ZONE,
                expires_at TIMESTAMP WITH TIME ZONE
            )
        """))

        connection.execute(text(f"""
            CREATE INDEX IF NOT EXISTS idx_pending_instructions_user_status
            ON "{schema}".pending_instructions (user_id, status)
        """))

    logger.info("Recreated pending_instructions table in all schemas")
