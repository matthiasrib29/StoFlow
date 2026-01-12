"""Drop unused mapping tables

Revision ID: 20251224_2300
Revises: 20251224_2200
Create Date: 2025-12-24

Drops:
- public.category_platform_mappings
- public.expected_mappings
- public.platform_mappings
"""

from alembic import op

revision = "20251224_2300"
down_revision = "20251224_2200"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop category_platform_mappings
    op.execute("DROP TABLE IF EXISTS public.category_platform_mappings CASCADE")
    print("  ✓ Dropped category_platform_mappings")
    
    # Drop expected_mappings
    op.execute("DROP TABLE IF EXISTS public.expected_mappings CASCADE")
    print("  ✓ Dropped expected_mappings")
    
    # Drop platform_mappings
    op.execute("DROP TABLE IF EXISTS public.platform_mappings CASCADE")
    print("  ✓ Dropped platform_mappings")
    
    # Drop platform_type enum if exists
    op.execute("DROP TYPE IF EXISTS platform_type CASCADE")
    print("  ✓ Dropped platform_type enum")


def downgrade() -> None:
    # Not recreating - these tables were unused
    pass
