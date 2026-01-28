"""cleanup W/L patterns in sizes_normalized

Phase 2 final step: Transform W32/L34 → W32 in sizes_normalized.
The length (L34) is now stored in product.size_length.

Process:
1. For each W/L entry (e.g., W32/L34):
   - Ensure waist-only entry exists (W32)
   - Copy marketplace mappings if W32 doesn't have them
   - Update products to point to W32 instead of W32/L34
   - Delete the W/L entry

Revision ID: sz_cleanup_wl
Revises: sz_catgrp_003
Create Date: 2026-01-28
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = 'sz_cleanup_wl'
down_revision: Union[str, None] = 'sz_catgrp_003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _get_tenant_schemas(conn) -> list[str]:
    """Get all tenant schemas (user_X) + template_tenant."""
    result = conn.execute(text(
        "SELECT schema_name FROM information_schema.schemata "
        "WHERE schema_name LIKE 'user_%' OR schema_name = 'template_tenant' "
        "ORDER BY schema_name"
    ))
    return [row[0] for row in result]


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Get all W/L entries from sizes_normalized
    result = conn.execute(text("""
        SELECT name_en, vinted_women_id, vinted_men_id, ebay_size, etsy_size, category_group
        FROM product_attributes.sizes_normalized
        WHERE name_en ~ '^W[0-9]+/L[0-9]+$'
        ORDER BY name_en
    """))
    wl_entries = list(result)

    print(f"Found {len(wl_entries)} W/L entries to process")

    # 2. Process each W/L entry
    for entry in wl_entries:
        wl_name = entry[0]  # e.g., "W32/L34"
        vinted_women = entry[1]
        vinted_men = entry[2]
        ebay_size = entry[3]
        etsy_size = entry[4]
        category_group = entry[5]

        # Extract waist part (W32 from W32/L34)
        waist_name = wl_name.split('/')[0]  # "W32"

        # 2a. Check if waist-only entry exists
        waist_exists = conn.execute(text(
            "SELECT 1 FROM product_attributes.sizes_normalized WHERE name_en = :name"
        ), {"name": waist_name}).scalar()

        if not waist_exists:
            # Create waist-only entry with mappings from W/L entry
            conn.execute(text("""
                INSERT INTO product_attributes.sizes_normalized
                (name_en, vinted_women_id, vinted_men_id, ebay_size, etsy_size, category_group)
                VALUES (:name, :vw, :vm, :ebay, :etsy, :cat)
            """), {
                "name": waist_name,
                "vw": vinted_women,
                "vm": vinted_men,
                "ebay": ebay_size,
                "etsy": etsy_size,
                "cat": category_group or 'waist'
            })
        else:
            # Update waist entry with mappings if it doesn't have them
            conn.execute(text("""
                UPDATE product_attributes.sizes_normalized
                SET
                    vinted_women_id = COALESCE(vinted_women_id, :vw),
                    vinted_men_id = COALESCE(vinted_men_id, :vm),
                    ebay_size = COALESCE(ebay_size, :ebay),
                    etsy_size = COALESCE(etsy_size, :etsy),
                    category_group = COALESCE(category_group, :cat)
                WHERE name_en = :name
            """), {
                "name": waist_name,
                "vw": vinted_women,
                "vm": vinted_men,
                "ebay": ebay_size,
                "etsy": etsy_size,
                "cat": category_group or 'waist'
            })

    # 3. Update all products in all tenant schemas
    schemas = _get_tenant_schemas(conn)

    for schema in schemas:
        # Check if products table exists
        products_exists = conn.execute(text(
            "SELECT EXISTS ("
            "  SELECT 1 FROM information_schema.tables "
            "  WHERE table_schema = :schema AND table_name = 'products'"
            ")"
        ), {"schema": schema}).scalar()

        if not products_exists:
            continue

        # Update products: W32/L34 → W32
        conn.execute(text(f"""
            UPDATE "{schema}".products
            SET size_normalized = split_part(size_normalized, '/', 1)
            WHERE size_normalized ~ '^W[0-9]+/L[0-9]+$'
        """))

    # 4. Delete all W/L entries from sizes_normalized
    conn.execute(text("""
        DELETE FROM product_attributes.sizes_normalized
        WHERE name_en ~ '^W[0-9]+/L[0-9]+$'
    """))


def downgrade() -> None:
    # This migration is not easily reversible as it transforms data
    # The W/L entries would need to be recreated from backup
    # For safety, we don't implement automatic downgrade
    raise NotImplementedError(
        "Downgrade not supported for this migration. "
        "Restore from backup if needed: ~/StoFlow/backups/dev_backup_20260128_162500.dump"
    )
