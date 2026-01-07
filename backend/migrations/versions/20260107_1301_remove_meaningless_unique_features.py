"""remove_meaningless_unique_features

Revision ID: 5513765d1e79
Revises: edc8822ba716
Create Date: 2026-01-07 13:01:06.755288+01:00

Remove unique features that are meaningless (present on 100% of items in category):
- waistband: All pants have one, not unique
- fly: Too vague, "button fly" or "zip fly" (in Closures) is useful
- yoke: Almost all shirts/jeans have one, not unique unless "Western yoke"
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '5513765d1e79'
down_revision: Union[str, None] = 'edc8822ba716'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove meaningless unique features."""
    conn = op.get_bind()

    features_to_remove = ['waistband', 'fly', 'yoke']

    print(f"Removing {len(features_to_remove)} meaningless unique features...")

    for feature in features_to_remove:
        print(f"  🗑️  Deleting: {feature}")
        conn.execute(text("""
            DELETE FROM product_attributes.unique_features
            WHERE name_en = :feature
        """), {"feature": feature})

    print("✅ Meaningless features removed successfully!")


def downgrade() -> None:
    """Restore removed unique features."""
    conn = op.get_bind()

    features_to_restore = ['waistband', 'fly', 'yoke']

    print(f"Restoring {len(features_to_restore)} unique features...")

    for feature in features_to_restore:
        print(f"  ✏️  Restoring: {feature}")
        conn.execute(text("""
            INSERT INTO product_attributes.unique_features (name_en)
            VALUES (:feature)
            ON CONFLICT (name_en) DO NOTHING
        """), {"feature": feature})

    print("✅ Features restored successfully!")
