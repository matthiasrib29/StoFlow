"""add new condition_sups

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-01-07 19:03:00.000000+01:00

Purpose:
    Add 3 new condition supplement values to product_attributes.condition_sups:

    1. New With Tags (NWT) - Item is brand new and still has original tags attached
    2. New Without Tags (NWOT) - Item is brand new but tags have been removed
    3. Deadstock (NOS) - New old stock, never worn/used but from previous season

    These values are commonly used in resale marketplaces (Vinted, eBay, Etsy).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add NWT, NWOT, NOS condition supplements."""
    conn = op.get_bind()

    print("\n" + "=" * 70)
    print("📦 ADDING NEW CONDITION SUPPLEMENTS")
    print("=" * 70 + "\n")

    # New values with French translations
    new_values = [
        ("New With Tags (NWT)", "Neuf Avec Étiquettes (NWT)"),
        ("New Without Tags (NWOT)", "Neuf Sans Étiquettes (NWOT)"),
        ("Deadstock (NOS)", "Stock Mort (NOS)")
    ]

    print(f"Adding {len(new_values)} new condition supplements:\n")

    added_count = 0
    for name_en, name_fr in new_values:
        result = conn.execute(text("""
            INSERT INTO product_attributes.condition_sups (name_en, name_fr)
            VALUES (:name_en, :name_fr)
            ON CONFLICT (name_en) DO NOTHING
            RETURNING name_en;
        """), {"name_en": name_en, "name_fr": name_fr})

        if result.rowcount > 0:
            print(f"  ✅ Added: {name_en} / {name_fr}")
            added_count += 1
        else:
            print(f"  ⏭️  Skipped (already exists): {name_en}")

    # Verify insertion
    result = conn.execute(text("""
        SELECT COUNT(*)
        FROM product_attributes.condition_sups
        WHERE name_en IN (
            'New With Tags (NWT)',
            'New Without Tags (NWOT)',
            'Deadstock (NOS)'
        );
    """))

    count = result.scalar()
    print(f"\n✅ {count} new condition supplements now available")

    print("\n" + "=" * 70)
    print("✅ NEW CONDITION SUPPLEMENTS ADDED")
    print("=" * 70)


def downgrade() -> None:
    """Remove NWT, NWOT, NOS condition supplements."""
    conn = op.get_bind()

    print("\n⚠️  Removing new condition supplements...")

    conn.execute(text("""
        DELETE FROM product_attributes.condition_sups
        WHERE name_en IN (
            'New With Tags (NWT)',
            'New Without Tags (NWOT)',
            'Deadstock (NOS)'
        );
    """))

    print("✅ New condition supplements removed")
