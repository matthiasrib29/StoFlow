"""add_response_data_to_ai_generation_logs

Revision ID: aae3bed742fd
Revises: 5308f5fcccc3
Create Date: 2026-01-07 21:18:49.968422+01:00

"""
from typing import Sequence, Union


from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from logging import getLogger

logger = getLogger(__name__)


# revision identifiers, used by Alembic.
revision: str = 'aae3bed742fd'
down_revision: Union[str, None] = '5308f5fcccc3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add response_data column to ai_generation_logs table.
    This stores the raw AI response JSON for debugging, audit, and re-parsing.
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
            # Add response_data column
            conn.execute(text(f"""
                ALTER TABLE {schema}.ai_generation_logs
                ADD COLUMN IF NOT EXISTS response_data JSONB NULL
            """))

            # Add comment
            conn.execute(text(f"""
                COMMENT ON COLUMN {schema}.ai_generation_logs.response_data IS
                'Raw AI response JSON for debugging, audit, and re-parsing'
            """))

            logger.info(f"✓ Added response_data column to {schema}.ai_generation_logs")


def downgrade() -> None:
    """
    Remove response_data column from ai_generation_logs table.
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
            # Drop response_data column
            conn.execute(text(f"""
                ALTER TABLE {schema}.ai_generation_logs
                DROP COLUMN IF EXISTS response_data
            """))
            logger.info(f"✓ Removed response_data column from {schema}.ai_generation_logs")
