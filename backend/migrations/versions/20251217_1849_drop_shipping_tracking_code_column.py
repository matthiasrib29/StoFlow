"""drop_shipping_tracking_code_column

Remove shipping_tracking_code column from vinted_orders (duplicate of tracking_number).

Revision ID: ca33d9632b06
Revises: 20251217_1850
Create Date: 2025-12-17 18:49:58.892467+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'ca33d9632b06'
down_revision: Union[str, None] = '20251217_1850'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_user_schemas(connection) -> list[str]:
    """Get all user schemas (user_X pattern)."""
    result = connection.execute(text("""
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
        ORDER BY schema_name
    """))
    return [row[0] for row in result]


def upgrade() -> None:
    """Drop shipping_tracking_code column from all schemas."""
    connection = op.get_bind()

    # Drop from template_tenant
    op.execute(text("""
        ALTER TABLE IF EXISTS template_tenant.vinted_orders
        DROP COLUMN IF EXISTS shipping_tracking_code
    """))

    # Drop from all user schemas
    for schema in get_user_schemas(connection):
        op.execute(text(f"""
            ALTER TABLE IF EXISTS {schema}.vinted_orders
            DROP COLUMN IF EXISTS shipping_tracking_code
        """))


def downgrade() -> None:
    """Re-add shipping_tracking_code column to all schemas."""
    connection = op.get_bind()

    # Add to template_tenant
    op.execute(text("""
        ALTER TABLE IF EXISTS template_tenant.vinted_orders
        ADD COLUMN IF NOT EXISTS shipping_tracking_code VARCHAR(100)
    """))

    # Add to all user schemas
    for schema in get_user_schemas(connection):
        op.execute(text(f"""
            ALTER TABLE IF EXISTS {schema}.vinted_orders
            ADD COLUMN IF NOT EXISTS shipping_tracking_code VARCHAR(100)
        """))
