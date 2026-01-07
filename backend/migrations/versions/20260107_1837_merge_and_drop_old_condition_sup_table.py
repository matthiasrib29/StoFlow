"""merge and drop old condition_sup table

Revision ID: 9c7c0b878bb4
Revises: 0dea6c4e2c82
Create Date: 2026-01-07 18:37:13.809682+01:00

Purpose:
    Clean up duplicate condition supplement tables in product_attributes schema.

    There are two tables:
    - condition_sup (singular, 28 values) - OLD table
    - condition_sups (plural, 19 values) - NEW table

    This migration:
    1. Merges values from old table to new table
    2. Drops the old condition_sup (singular) table

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '9c7c0b878bb4'
down_revision: Union[str, None] = '0dea6c4e2c82'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge old condition_sup table into condition_sups and drop it."""
    conn = op.get_bind()

    print("\n" + "=" * 70)
    print("📊 MERGING CONDITION_SUP TABLES")
    print("=" * 70 + "\n")

    # Step 1: Copy all values from old table to new table (ignore duplicates)
    print("📋 Copying values from condition_sup → condition_sups...")
    result = conn.execute(text("""
        INSERT INTO product_attributes.condition_sups
            (name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl)
        SELECT name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl
        FROM product_attributes.condition_sup
        ON CONFLICT (name_en) DO NOTHING;
    """))
    copied = result.rowcount
    print(f"  ✅ Copied {copied} new values")

    # Step 2: Check total count in new table
    result = conn.execute(text("""
        SELECT COUNT(*) FROM product_attributes.condition_sups;
    """))
    total = result.scalar()
    print(f"  📊 Total values in condition_sups: {total}")

    # Step 3: Drop old table
    print("\n🗑️  Dropping old condition_sup table...")
    conn.execute(text("""
        DROP TABLE IF EXISTS product_attributes.condition_sup CASCADE;
    """))
    print("  ✅ Dropped")

    print("\n" + "=" * 70)
    print("✅ MERGE COMPLETE")
    print("=" * 70)
    print(f"\nOnly product_attributes.condition_sups (plural) remains with {total} values.")
    print("=" * 70)


def downgrade() -> None:
    """Cannot recreate dropped table."""
    print("\n⚠️  Downgrade not supported (would require recreating condition_sup table)")
