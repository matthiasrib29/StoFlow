"""move models table to product_attributes schema

Revision ID: 9b5d3f2e4c6a
Revises: 8a4c2e1f3d5b
Create Date: 2026-01-22

Move the models table from public schema to product_attributes schema.
The FK to public.brand_groups is preserved (cross-schema FK).
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9b5d3f2e4c6a'
down_revision = '8a4c2e1f3d5b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Move models table from public to product_attributes schema."""
    # PostgreSQL allows moving tables between schemas with ALTER TABLE SET SCHEMA
    op.execute("ALTER TABLE public.models SET SCHEMA product_attributes")


def downgrade() -> None:
    """Move models table back to public schema."""
    op.execute("ALTER TABLE product_attributes.models SET SCHEMA public")
