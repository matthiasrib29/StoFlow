"""create brand_groups table

Revision ID: 2f3a9708b420
Revises: 20260109_0400
Create Date: 2026-01-09 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '2f3a9708b420'
down_revision: Union[str, None] = '20260109_0400'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create brand_groups table in public schema."""

    conn = op.get_bind()

    # Create brand_groups table
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS public.brand_groups (
            id SERIAL PRIMARY KEY,
            brand VARCHAR(100) NOT NULL,
            group_name VARCHAR(50) NOT NULL,
            base_price DECIMAL(10,2) NOT NULL CHECK (base_price >= 5.00 AND base_price <= 500.00),
            expected_origins JSONB DEFAULT '[]'::jsonb NOT NULL,
            expected_decades JSONB DEFAULT '[]'::jsonb NOT NULL,
            expected_trends JSONB DEFAULT '[]'::jsonb NOT NULL,
            condition_sensitivity DECIMAL(3,2) NOT NULL DEFAULT 1.0 CHECK (condition_sensitivity >= 0.5 AND condition_sensitivity <= 1.5),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,

            CONSTRAINT uq_brand_groups_brand_group UNIQUE (brand, group_name)
        );
    """))

    # Create indexes
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_brand_groups_brand ON public.brand_groups(brand);
    """))

    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_brand_groups_group ON public.brand_groups(group_name);
    """))

    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_brand_groups_created_at ON public.brand_groups(created_at DESC);
    """))

    print("✓ Created brand_groups table in public schema")


def downgrade() -> None:
    """Drop brand_groups table."""

    conn = op.get_bind()

    # Drop table (indexes will be dropped automatically)
    conn.execute(text("""
        DROP TABLE IF EXISTS public.brand_groups CASCADE;
    """))

    print("✓ Dropped brand_groups table from public schema")
