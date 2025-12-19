"""
Add result_data column to vinted_jobs

Adds JSONB column for job parameters and result data.

Revision ID: 20251219_1500
Revises: 20251219_1400
Create Date: 2025-12-19 15:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "20251219_1500"
down_revision = "20251219_1400"
branch_labels = None
depends_on = None


def get_user_schemas(connection) -> list[str]:
    """Get all user schemas."""
    result = connection.execute(
        sa.text(
            "SELECT schema_name FROM information_schema.schemata "
            "WHERE schema_name LIKE 'user_%' OR schema_name = 'template_tenant'"
        )
    )
    return [row[0] for row in result]


def upgrade() -> None:
    connection = op.get_bind()
    user_schemas = get_user_schemas(connection)

    for schema_name in user_schemas:
        # Add result_data column to vinted_jobs
        op.execute(f"""
            ALTER TABLE {schema_name}.vinted_jobs
            ADD COLUMN IF NOT EXISTS result_data JSONB
        """)


def downgrade() -> None:
    connection = op.get_bind()
    user_schemas = get_user_schemas(connection)

    for schema_name in user_schemas:
        op.execute(f"""
            ALTER TABLE {schema_name}.vinted_jobs
            DROP COLUMN IF EXISTS result_data
        """)
