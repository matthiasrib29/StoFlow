"""fix condition_sup lowercase to title case

Revision ID: 9b12d3d8f4c4
Revises: 001b85a9a3be
Create Date: 2026-01-07 18:15:02.043386+01:00

Purpose:
    Fix case inconsistencies in products.condition_sup JSONB arrays.
    Maps lowercase values to Title Case to match product_attributes.condition_sups.

    Example: ["faded", "small hole"] → ["Faded", "Small Hole"]

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '9b12d3d8f4c4'
down_revision: Union[str, None] = '001b85a9a3be'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_user_schemas(conn):
    """Get all user schemas (template_tenant + user_X)."""
    result = conn.execute(text("""
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name = 'template_tenant'
        OR schema_name LIKE 'user_%'
        ORDER BY schema_name
    """))
    return [row[0] for row in result.fetchall()]


def table_exists(conn, schema, table):
    """Check if a table exists in a schema."""
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = :schema AND table_name = :table
        )
    """), {"schema": schema, "table": table})
    return result.scalar()


def upgrade() -> None:
    """Fix lowercase → Title Case in condition_sup JSONB arrays."""
    conn = op.get_bind()

    print("\n" + "=" * 70)
    print("📊 FIXING CONDITION_SUP CASE (lowercase → Title Case)")
    print("=" * 70 + "\n")

    # Mapping: lowercase → Title Case
    case_mapping = {
        "damaged button": "Damaged Button",
        "distressed": "Distressed",
        "faded": "Faded",
        "frayed hems": "Frayed Hems",
        "general wear": "General Wear",
        "hemmed/shortened": "Hemmed/Shortened",
        "knee wear": "Knee Wear",
        "light discoloration": "Light Discoloration",
        "marked discoloration": "Marked Discoloration",
        "multiple holes": "Multiple Holes",
        "multiple stains": "Multiple Stains",
        "resewn": "Resewn",
        "seam to fix": "Seam To Fix",
        "single stain": "Single Stain",
        "small hole": "Small Hole",
        "stretched": "Stretched",
        "vintage patina": "Vintage Patina",
        "vintage wear": "Vintage Wear",
        "worn": "Worn",
    }

    schemas = get_user_schemas(conn)
    total_products_updated = 0

    for schema in schemas:
        if not table_exists(conn, schema, 'products'):
            continue

        print(f"📦 Processing {schema}...")

        # For each mapping, replace values in JSONB array
        products_updated_in_schema = 0
        for old_val, new_val in case_mapping.items():
            result = conn.execute(text(f"""
                UPDATE {schema}.products
                SET condition_sup = (
                    SELECT jsonb_agg(
                        CASE
                            WHEN elem::text = '"{old_val}"' THEN '"{new_val}"'::jsonb
                            ELSE elem
                        END
                    )
                    FROM jsonb_array_elements(condition_sup) AS elem
                )
                WHERE condition_sup IS NOT NULL
                AND jsonb_typeof(condition_sup) = 'array'
                AND condition_sup::text LIKE '%"{old_val}"%'
                AND deleted_at IS NULL;
            """))
            products_updated_in_schema += result.rowcount

        if products_updated_in_schema > 0:
            print(f"  ✅ Updated {products_updated_in_schema} products")
            total_products_updated += products_updated_in_schema

    print("\n" + "=" * 70)
    print("📊 CASE FIX SUMMARY")
    print("=" * 70)
    print(f"  Total products updated: {total_products_updated}")
    print("=" * 70)
    print("✅ CASE FIX COMPLETE")
    print("=" * 70)


def downgrade() -> None:
    """Revert Title Case → lowercase (not recommended)."""
    print("\n⚠️  Downgrade not implemented (would revert valid Title Case to lowercase)")
