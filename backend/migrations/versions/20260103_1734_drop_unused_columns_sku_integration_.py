"""drop_unused_columns_sku_integration_metadata_published_at_scheduled_publish_at

Revision ID: c49a23dbbae1
Revises: 20250103_0300
Create Date: 2026-01-03 17:34:56.724971+01:00

Drops unused columns from products table:
- sku: never used (0 values in user_1)
- integration_metadata: never used (0 values)
- published_at: workflow not implemented (0 values)
- scheduled_publish_at: workflow not implemented (0 values)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c49a23dbbae1'
down_revision: Union[str, None] = '20250103_0300'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Columns to drop
COLUMNS_TO_DROP = ['sku', 'integration_metadata', 'published_at', 'scheduled_publish_at']


def get_user_schemas():
    """Get all user schemas (user_1, user_2, etc.)"""
    connection = op.get_bind()
    result = connection.execute(sa.text(
        "SELECT schema_name FROM information_schema.schemata "
        "WHERE schema_name LIKE 'user_%' ORDER BY schema_name"
    ))
    return [row[0] for row in result]


def upgrade() -> None:
    """Drop unused columns from products table in all user schemas."""
    user_schemas = get_user_schemas()

    for schema in user_schemas:
        for column in COLUMNS_TO_DROP:
            # Check if column exists before dropping
            connection = op.get_bind()
            result = connection.execute(sa.text(
                f"SELECT column_name FROM information_schema.columns "
                f"WHERE table_schema = '{schema}' AND table_name = 'products' "
                f"AND column_name = '{column}'"
            ))
            if result.fetchone():
                op.drop_column('products', column, schema=schema)


def downgrade() -> None:
    """Recreate dropped columns in all user schemas."""
    user_schemas = get_user_schemas()

    for schema in user_schemas:
        # sku - VARCHAR(100)
        op.add_column('products', sa.Column(
            'sku', sa.String(100), nullable=True,
            comment='Code article interne (SKU)'
        ), schema=schema)

        # integration_metadata - JSONB
        op.add_column('products', sa.Column(
            'integration_metadata', postgresql.JSONB, nullable=True,
            comment='Metadonnees pour integrations (vinted_id, source, etc.)'
        ), schema=schema)

        # published_at - TIMESTAMP WITH TIME ZONE
        op.add_column('products', sa.Column(
            'published_at', sa.DateTime(timezone=True), nullable=True,
            comment='Date de publication effective'
        ), schema=schema)

        # scheduled_publish_at - TIMESTAMP WITH TIME ZONE
        op.add_column('products', sa.Column(
            'scheduled_publish_at', sa.DateTime(timezone=True), nullable=True,
            comment='Date de publication programmee (si status=scheduled)'
        ), schema=schema)
