"""make_ai_generation_log_product_id_nullable

Revision ID: 5308f5fcccc3
Revises: 4d2e58dae912
Create Date: 2026-01-07 19:06:39.194552+01:00

"""
from typing import Sequence, Union


from alembic import op
import sqlalchemy as sa
from logging import getLogger

logger = getLogger(__name__)


# revision identifiers, used by Alembic.
revision: str = '5308f5fcccc3'
down_revision: Union[str, None] = '4d2e58dae912'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Make product_id nullable in ai_generation_logs table.
    This allows logging AI generations without an associated product (direct image analysis).
    """
    from sqlalchemy import text

    # Get database connection
    conn = op.get_bind()

    # Get all user schemas
    result = conn.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
        ORDER BY schema_name
    """))

    user_schemas = [row[0] for row in result]

    # Apply changes to each user schema
    for schema in user_schemas:
        # Check if table exists
        table_exists = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = '{schema}'
                AND table_name = 'ai_generation_logs'
            )
        """)).scalar()

        if table_exists:
            # Alter column to allow NULL
            conn.execute(text(f"""
                ALTER TABLE {schema}.ai_generation_logs
                ALTER COLUMN product_id DROP NOT NULL
            """))
            logger.info(f"✓ Modified ai_generation_logs.product_id in {schema}")


def downgrade() -> None:
    """
    Revert product_id to NOT NULL in ai_generation_logs table.
    WARNING: This will fail if there are rows with NULL product_id.
    """
    from sqlalchemy import text

    # Get database connection
    conn = op.get_bind()

    # Get all user schemas
    result = conn.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
        ORDER BY schema_name
    """))

    user_schemas = [row[0] for row in result]

    # Revert changes in each user schema
    for schema in user_schemas:
        # Check if table exists
        table_exists = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = '{schema}'
                AND table_name = 'ai_generation_logs'
            )
        """)).scalar()

        if table_exists:
            # Revert column to NOT NULL (will fail if NULL values exist)
            conn.execute(text(f"""
                ALTER TABLE {schema}.ai_generation_logs
                ALTER COLUMN product_id SET NOT NULL
            """))
            logger.info(f"✓ Reverted ai_generation_logs.product_id in {schema}")
