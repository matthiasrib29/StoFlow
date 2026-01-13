"""Convert brands to sentence case

Revision ID: 20260113_0900
Revises: 20260112_1901
Create Date: 2026-01-13

Business Rules:
- Brand names should be stored in sentence case (first letter uppercase)
- This migration converts existing lowercase brands to sentence case
- The validator (AttributeValidator) now uses case-insensitive matching
"""

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = "20260113_0900"
down_revision = "20260112_1900_pricing"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Convert brand names to sentence case (capitalize first letter)."""
    conn = op.get_bind()

    # Get all brands
    result = conn.execute(text("SELECT name FROM product_attributes.brands ORDER BY name"))
    brands = result.fetchall()

    # Build a set of existing names for quick lookup
    existing_names = {row[0] for row in brands}

    for (brand_name,) in brands:
        if brand_name:
            # Convert to sentence case (capitalize first letter, preserve rest)
            # E.g., "lee" -> "Lee", "NIKE" -> "Nike", "h&m" -> "H&m"
            sentence_case = brand_name.capitalize()

            # Only process if different
            if sentence_case != brand_name:
                if sentence_case in existing_names:
                    # Sentence case version already exists -> delete the lowercase version
                    conn.execute(
                        text("DELETE FROM product_attributes.brands WHERE name = :old_name"),
                        {"old_name": brand_name}
                    )
                else:
                    # Sentence case version doesn't exist -> rename
                    conn.execute(
                        text("""
                            UPDATE product_attributes.brands
                            SET name = :new_name
                            WHERE name = :old_name
                        """),
                        {"new_name": sentence_case, "old_name": brand_name}
                    )
                    # Update our tracking set
                    existing_names.add(sentence_case)
                    existing_names.discard(brand_name)

    conn.commit()


def downgrade() -> None:
    """Convert brand names back to lowercase."""
    conn = op.get_bind()

    # Get all brands
    result = conn.execute(text("SELECT name FROM product_attributes.brands"))
    brands = result.fetchall()

    for (brand_name,) in brands:
        if brand_name:
            lower_name = brand_name.lower()

            # Only update if different
            if lower_name != brand_name:
                conn.execute(
                    text("""
                        UPDATE product_attributes.brands
                        SET name = :new_name
                        WHERE name = :old_name
                    """),
                    {"new_name": lower_name, "old_name": brand_name}
                )

    conn.commit()
