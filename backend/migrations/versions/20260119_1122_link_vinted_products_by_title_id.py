"""link_vinted_products_by_title_id

Revision ID: 9d045c61f0bd
Revises: 61fb12af8867
Create Date: 2026-01-19 11:22:15.845012+01:00

Business Rules:
- Vinted product titles contain the StoFlow product ID in brackets at the end
- Example: "Jean Slim Universal Thread | W36/L28 [88808]" → product_id = 88808
- This migration extracts these IDs and populates the product_id FK column
- Only links if the product actually exists in the products table
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9d045c61f0bd'
down_revision: Union[str, None] = '61fb12af8867'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Extract product IDs from Vinted product titles and link them.

    Title format: "... [PRODUCT_ID]"
    Uses PostgreSQL regex to extract the number in brackets at the end.
    """
    conn = op.get_bind()

    # Get all user schemas
    schemas_result = conn.execute(sa.text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
    """))
    user_schemas = [row[0] for row in schemas_result.fetchall()]

    total_linked = 0

    for schema in user_schemas:
        # Check if vinted_products table exists in this schema
        table_exists = conn.execute(sa.text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = '{schema}'
                AND table_name = 'vinted_products'
            )
        """)).scalar()

        if not table_exists:
            continue

        # Update vinted_products with extracted product_id
        # Regex: \[(\d+)\]$ matches [NUMBER] at the end of the string
        # Use DISTINCT ON to handle duplicates (keep most recent by created_at)
        result = conn.execute(sa.text(f"""
            UPDATE {schema}.vinted_products vp
            SET product_id = extracted.pid::integer
            FROM (
                SELECT DISTINCT ON (pid)
                    vinted_id,
                    (regexp_match(title, '\\[(\\d+)\\]$'))[1] as pid,
                    created_at
                FROM {schema}.vinted_products
                WHERE title ~ '\\[\\d+\\]$'
                AND product_id IS NULL
                ORDER BY pid, created_at DESC
            ) extracted
            WHERE vp.vinted_id = extracted.vinted_id
            AND extracted.pid IS NOT NULL
            AND EXISTS (
                SELECT 1 FROM {schema}.products p
                WHERE p.id = extracted.pid::integer
            )
            AND NOT EXISTS (
                SELECT 1 FROM {schema}.vinted_products vp2
                WHERE vp2.product_id = extracted.pid::integer
            )
        """))

        linked = result.rowcount
        total_linked += linked

        if linked > 0:
            print(f"  {schema}: linked {linked} Vinted products")

    print(f"  Total: {total_linked} Vinted products linked to StoFlow products")


def downgrade() -> None:
    """
    Remove the product_id links (set back to NULL).
    """
    conn = op.get_bind()

    # Get all user schemas
    schemas_result = conn.execute(sa.text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
    """))
    user_schemas = [row[0] for row in schemas_result.fetchall()]

    for schema in user_schemas:
        # Check if vinted_products table exists
        table_exists = conn.execute(sa.text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = '{schema}'
                AND table_name = 'vinted_products'
            )
        """)).scalar()

        if not table_exists:
            continue

        # Set product_id back to NULL for products that were linked by title
        conn.execute(sa.text(f"""
            UPDATE {schema}.vinted_products
            SET product_id = NULL
            WHERE title ~ '\\[\\d+\\]$'
            AND product_id IS NOT NULL
        """))

    print("  Removed product_id links from Vinted products")
