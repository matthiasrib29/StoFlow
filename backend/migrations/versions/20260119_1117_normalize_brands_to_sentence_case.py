"""normalize_brands_to_sentence_case

Revision ID: 61fb12af8867
Revises: 4727d3780ac6
Create Date: 2026-01-19 11:17:21.019950+01:00

Business Rules:
- Normalize all brand names to Sentence Case (first letter capitalized)
- Handle duplicates that may arise from normalization (e.g., "lee", "Lee", "LEE" → "Lee")
- Use PostgreSQL INITCAP for proper sentence case conversion
- FK CASCADE will automatically update products.brand when brands.name changes

Examples:
- "lee" → "Lee"
- "tommy hilfiger" → "Tommy Hilfiger"
- "ralph lauren" → "Ralph Lauren"
- "levi's" → "Levi's"
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '61fb12af8867'
down_revision: Union[str, None] = '4727d3780ac6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Normalize brand names to Sentence Case.

    Strategy:
    1. Find brands that would become duplicates after normalization
    2. For each duplicate group, keep the one that's already in correct case (or first one)
    3. Update products pointing to duplicates to point to the canonical brand
    4. Delete duplicate brands
    5. Update remaining brands to Sentence Case
    """
    conn = op.get_bind()

    # Step 1: Find duplicate groups after normalization
    # Get all brands and their normalized versions
    result = conn.execute(sa.text("""
        SELECT name, INITCAP(name) as normalized
        FROM product_attributes.brands
        ORDER BY normalized, name
    """))
    brands = result.fetchall()

    # Group brands by their normalized form
    normalized_groups: dict[str, list[str]] = {}
    for row in brands:
        name, normalized = row[0], row[1]
        if normalized not in normalized_groups:
            normalized_groups[normalized] = []
        normalized_groups[normalized].append(name)

    # Step 2: Handle duplicates
    for normalized, names in normalized_groups.items():
        if len(names) > 1:
            # Multiple brands will normalize to the same value
            # Keep the one that's already in correct case, or the first one
            canonical = normalized if normalized in names else names[0]
            duplicates = [n for n in names if n != canonical]

            print(f"  Merging duplicates: {duplicates} → {canonical}")

            # Step 3: Update all user schemas' products to point to canonical brand
            # Get all user schemas
            schemas_result = conn.execute(sa.text("""
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name LIKE 'user_%'
            """))
            user_schemas = [row[0] for row in schemas_result.fetchall()]

            for duplicate in duplicates:
                for schema in user_schemas:
                    # Update products in this schema to use canonical brand
                    conn.execute(sa.text(f"""
                        UPDATE {schema}.products
                        SET brand = :canonical
                        WHERE brand = :duplicate
                    """), {"canonical": canonical, "duplicate": duplicate})

                # Also update brand_groups if they reference the duplicate
                conn.execute(sa.text("""
                    UPDATE public.brand_groups
                    SET brand = :canonical
                    WHERE brand = :duplicate
                """), {"canonical": canonical, "duplicate": duplicate})

                # Step 4: Delete the duplicate brand
                conn.execute(sa.text("""
                    DELETE FROM product_attributes.brands
                    WHERE name = :duplicate
                """), {"duplicate": duplicate})

    # Step 5: Update remaining brands to Sentence Case
    # Only update brands that are not already in correct case
    conn.execute(sa.text("""
        UPDATE product_attributes.brands
        SET name = INITCAP(name)
        WHERE name != INITCAP(name)
    """))

    print("  Brand normalization complete!")


def downgrade() -> None:
    """
    Downgrade is not fully reversible because:
    - We don't know the original case of merged duplicates
    - We can convert back to lowercase, but merged brands stay merged

    This converts all brands to lowercase as a best-effort rollback.
    """
    conn = op.get_bind()

    conn.execute(sa.text("""
        UPDATE product_attributes.brands
        SET name = LOWER(name)
        WHERE name != LOWER(name)
    """))

    print("  Brands converted back to lowercase (merged duplicates remain merged)")
