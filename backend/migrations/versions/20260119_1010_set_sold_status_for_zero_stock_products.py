"""set_sold_status_for_zero_stock_products

Revision ID: 4727d3780ac6
Revises: 8c514d17ef8d
Create Date: 2026-01-19 10:10:53.593154+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4727d3780ac6'
down_revision: Union[str, None] = '8c514d17ef8d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Set status to 'sold' for all products with stock_quantity <= 0."""
    connection = op.get_bind()

    # Get all user schemas (user_X)
    result = connection.execute(
        sa.text("SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'user_%'")
    )
    schemas = [row[0] for row in result]

    for schema in schemas:
        # Update products with stock <= 0 to status 'SOLD'
        connection.execute(
            sa.text(f"""
                UPDATE {schema}.products
                SET status = 'SOLD', updated_at = NOW()
                WHERE stock_quantity <= 0
                AND status != 'SOLD'
            """)
        )


def downgrade() -> None:
    """Revert status back to 'draft' for products that were changed."""
    # Note: This is a data migration, downgrade sets back to 'draft'
    # but we can't know the original status, so this is a best-effort rollback
    connection = op.get_bind()

    result = connection.execute(
        sa.text("SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'user_%'")
    )
    schemas = [row[0] for row in result]

    for schema in schemas:
        connection.execute(
            sa.text(f"""
                UPDATE {schema}.products
                SET status = 'DRAFT', updated_at = NOW()
                WHERE stock_quantity <= 0
                AND status = 'SOLD'
            """)
        )
