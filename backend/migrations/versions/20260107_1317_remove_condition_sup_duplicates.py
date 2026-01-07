"""remove_condition_sup_duplicates

Revision ID: 312dfe0a7c07
Revises: b5ac89614dfc
Create Date: 2026-01-07 13:17:42.294960+01:00

Remove duplicates between CONDITIONS and CONDITION_SUP:
- "Acceptable condition" (duplicate of "Acceptable")
- "Excellent condition" (duplicate of "Excellent")
- "Good condition" (duplicate of "Good")
- "Like new" (exact duplicate)
- "Very good condition" (duplicate of "Very good")
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '312dfe0a7c07'
down_revision: Union[str, None] = 'b5ac89614dfc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove duplicate condition_sup values."""
    conn = op.get_bind()

    duplicates_to_remove = [
        'Acceptable condition',
        'Excellent condition',
        'Good condition',
        'Like new',
        'Very good condition'
    ]

    print(f"Removing {len(duplicates_to_remove)} duplicate condition_sup values...")

    for duplicate in duplicates_to_remove:
        print(f"  🗑️  Deleting: {duplicate}")
        conn.execute(text("""
            DELETE FROM product_attributes.condition_sup
            WHERE name_en = :duplicate
        """), {"duplicate": duplicate})

    print("✅ Duplicates removed successfully!")


def downgrade() -> None:
    """Restore removed condition_sup duplicates."""
    conn = op.get_bind()

    duplicates_to_restore = [
        'Acceptable condition',
        'Excellent condition',
        'Good condition',
        'Like new',
        'Very good condition'
    ]

    print(f"Restoring {len(duplicates_to_restore)} condition_sup values...")

    for duplicate in duplicates_to_restore:
        print(f"  ✏️  Restoring: {duplicate}")
        conn.execute(text("""
            INSERT INTO product_attributes.condition_sup (name_en)
            VALUES (:duplicate)
            ON CONFLICT (name_en) DO NOTHING
        """), {"duplicate": duplicate})

    print("✅ Duplicates restored successfully!")
