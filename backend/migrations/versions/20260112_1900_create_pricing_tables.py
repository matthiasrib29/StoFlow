"""create pricing tables (brand_groups and models)

Revision ID: 20260112_1900_pricing
Revises: 20260112_1750
Create Date: 2026-01-12 19:00:00

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '20260112_1900_pricing'
down_revision: Union[str, None] = '20260112_1750'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create brand_groups and models tables in public schema."""

    conn = op.get_bind()

    # Create brand_groups table
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS public.brand_groups (
            id SERIAL PRIMARY KEY,
            brand VARCHAR(100) NOT NULL,
            "group" VARCHAR(100) NOT NULL,
            base_price DECIMAL(10,2) NOT NULL CHECK (base_price >= 5.00 AND base_price <= 500.00),
            condition_sensitivity DECIMAL(3,2) NOT NULL DEFAULT 1.0 CHECK (condition_sensitivity >= 0.5 AND condition_sensitivity <= 1.5),
            expected_origins JSONB DEFAULT '[]'::jsonb NOT NULL,
            expected_decades JSONB DEFAULT '[]'::jsonb NOT NULL,
            expected_trends JSONB DEFAULT '[]'::jsonb NOT NULL,
            generated_by_ai BOOLEAN NOT NULL DEFAULT FALSE,
            ai_confidence DECIMAL(3,2),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,

            CONSTRAINT uq_brand_groups_brand_group UNIQUE (brand, "group")
        );
    """))

    # Create indexes for brand_groups
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_brand_groups_brand ON public.brand_groups(brand);
    """))

    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_brand_groups_group ON public.brand_groups("group");
    """))

    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_brand_groups_created_at ON public.brand_groups(created_at DESC);
    """))

    print("✓ Created brand_groups table in public schema")

    # Create models table
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS public.models (
            id SERIAL PRIMARY KEY,
            brand VARCHAR(100) NOT NULL,
            "group" VARCHAR(100) NOT NULL,
            name VARCHAR(100) NOT NULL,
            coefficient DECIMAL(4,2) NOT NULL DEFAULT 1.0 CHECK (coefficient >= 0.5 AND coefficient <= 3.0),
            expected_features JSONB DEFAULT '[]'::jsonb NOT NULL,
            generated_by_ai BOOLEAN NOT NULL DEFAULT FALSE,
            ai_confidence DECIMAL(3,2),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,

            CONSTRAINT uq_models_brand_group_name UNIQUE (brand, "group", name),
            CONSTRAINT fk_models_brand_group FOREIGN KEY (brand, "group")
                REFERENCES public.brand_groups(brand, "group") ON DELETE CASCADE
        );
    """))

    # Create indexes for models
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_models_brand_group ON public.models(brand, "group");
    """))

    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_models_name ON public.models(name);
    """))

    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_models_created_at ON public.models(created_at DESC);
    """))

    print("✓ Created models table in public schema")


def downgrade() -> None:
    """Drop models and brand_groups tables."""

    conn = op.get_bind()

    # Drop tables (models first due to FK)
    conn.execute(text("""
        DROP TABLE IF EXISTS public.models CASCADE;
    """))
    print("✓ Dropped models table")

    conn.execute(text("""
        DROP TABLE IF EXISTS public.brand_groups CASCADE;
    """))
    print("✓ Dropped brand_groups table")
