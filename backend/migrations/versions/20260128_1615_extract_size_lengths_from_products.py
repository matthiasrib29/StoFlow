"""extract size_length from existing products

Phase 1B of size system refactoring:
- Parse size_normalized and size_original for bottoms products
- Extract L values from W/L patterns (e.g., "W32/L34" → size_length = "34")
- Only processes products in bottoms categories

Patterns matched:
- W32/L34, W32xL34, W32 L34 → extracts "34"
- 32/34, 32x34 → extracts "34"
- L34 → extracts "34"

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-01-28
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = 'f2a3b4c5d6e7'
down_revision: Union[str, None] = 'e1f2a3b4c5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Categories considered "bottoms" (have leg length)
BOTTOMS_CATEGORIES = [
    'jeans', 'pants', 'chinos', 'cargo-pants', 'joggers',
    'shorts', 'bermuda', 'dress-pants', 'culottes', 'leggings'
]


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
    schemas = _get_tenant_schemas(conn)

    # Regex patterns to extract leg length:
    # Pattern 1: W32/L34, W32xL34, W32 L34, W32-L34 → captures 34
    # Pattern 2: 32/34, 32x34, 32-34 (no W prefix) → captures 34
    # Pattern 3: L34 alone → captures 34

    # Build category filter
    categories_list = "'" + "','".join(BOTTOMS_CATEGORIES) + "'"

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

        # Check if size_length column exists
        col_exists = conn.execute(text(
            "SELECT EXISTS ("
            "  SELECT 1 FROM information_schema.columns "
            "  WHERE table_schema = :schema "
            "    AND table_name = 'products' "
            "    AND column_name = 'size_length'"
            ")"
        ), {"schema": schema}).scalar()

        if not col_exists:
            continue

        # Update products with W/L pattern in size_normalized
        # Pattern: W32/L34, W32xL34, W32-L34, W32 L34 → extract "34"
        conn.execute(text(f"""
            UPDATE "{schema}".products
            SET size_length = (
                regexp_replace(
                    COALESCE(size_normalized, size_original),
                    '.*[Ww]?\\d{{2}}[/xX\\-\\s][Ll]?(\\d{{2}}).*',
                    '\\1'
                )
            )
            WHERE category IN ({categories_list})
              AND size_length IS NULL
              AND (
                  size_normalized ~ '[Ww]?\\d{{2}}[/xX\\-\\s][Ll]?\\d{{2}}'
                  OR size_original ~ '[Ww]?\\d{{2}}[/xX\\-\\s][Ll]?\\d{{2}}'
              )
              AND regexp_replace(
                    COALESCE(size_normalized, size_original),
                    '.*[Ww]?\\d{{2}}[/xX\\-\\s][Ll]?(\\d{{2}}).*',
                    '\\1'
                  ) IN (SELECT name_en FROM product_attributes.size_lengths)
        """))

        # Update products with standalone L pattern (L34)
        # Pattern: L34 alone → extract "34"
        conn.execute(text(f"""
            UPDATE "{schema}".products
            SET size_length = (
                regexp_replace(
                    COALESCE(size_normalized, size_original),
                    '.*[Ll](\\d{{2}}).*',
                    '\\1'
                )
            )
            WHERE category IN ({categories_list})
              AND size_length IS NULL
              AND (
                  size_normalized ~ '[Ll]\\d{{2}}'
                  OR size_original ~ '[Ll]\\d{{2}}'
              )
              AND regexp_replace(
                    COALESCE(size_normalized, size_original),
                    '.*[Ll](\\d{{2}}).*',
                    '\\1'
                  ) IN (SELECT name_en FROM product_attributes.size_lengths)
        """))


def downgrade() -> None:
    conn = op.get_bind()
    schemas = _get_tenant_schemas(conn)

    for schema in schemas:
        # Check if column exists
        col_exists = conn.execute(text(
            "SELECT EXISTS ("
            "  SELECT 1 FROM information_schema.columns "
            "  WHERE table_schema = :schema "
            "    AND table_name = 'products' "
            "    AND column_name = 'size_length'"
            ")"
        ), {"schema": schema}).scalar()

        if col_exists:
            # Reset size_length to NULL (data migration rollback)
            conn.execute(text(f"""
                UPDATE "{schema}".products
                SET size_length = NULL
                WHERE size_length IS NOT NULL
            """))
