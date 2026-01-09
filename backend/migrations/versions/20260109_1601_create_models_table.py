"""create models table

Revision ID: 20260109_1601_create_models_table
Revises: 20260109_1600_create_brand_groups_table
Create Date: 2026-01-09 16:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '20260109_1601_create_models_table'
down_revision: Union[str, None] = '20260109_1600_create_brand_groups_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create models table in public schema."""

    conn = op.get_bind()

    # Create models table
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS public.models (
            id SERIAL PRIMARY KEY,
            brand VARCHAR(100) NOT NULL,
            group_name VARCHAR(50) NOT NULL,
            model VARCHAR(100) NOT NULL,
            coefficient DECIMAL(4,2) NOT NULL DEFAULT 1.0 CHECK (coefficient >= 0.5 AND coefficient <= 3.0),
            expected_features JSONB DEFAULT '[]'::jsonb NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,

            CONSTRAINT uq_models_brand_group_model UNIQUE (brand, group_name, model)
        );
    """))

    # Create indexes
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_models_brand ON public.models(brand);
    """))

    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_models_group ON public.models(group_name);
    """))

    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_models_brand_group ON public.models(brand, group_name);
    """))

    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_models_created_at ON public.models(created_at DESC);
    """))

    print("✓ Created models table in public schema")


def downgrade() -> None:
    """Drop models table."""

    conn = op.get_bind()

    # Drop table (indexes will be dropped automatically)
    conn.execute(text("""
        DROP TABLE IF EXISTS public.models CASCADE;
    """))

    print("✓ Dropped models table from public schema")
