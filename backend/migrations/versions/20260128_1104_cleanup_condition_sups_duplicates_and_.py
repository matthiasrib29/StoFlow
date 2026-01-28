"""cleanup condition_sups duplicates and general conditions

Fixes 3 issues in product_attributes.condition_sups:
1. Lowercase duplicates (faded/Faded, hemmed/shortened/Hemmed/shortened, etc.)
2. General conditions overlapping with conditions table (excellent condition, etc.)
3. Remaining lowercase entries not following sentence case convention

Revision ID: 19c2a4d0c9b8
Revises: 0e1eae92f46a
Create Date: 2026-01-28 11:04:18.701069+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '19c2a4d0c9b8'
down_revision: Union[str, None] = '0e1eae92f46a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# --- Data definitions ---

# Lowercase duplicates that have a Title Case equivalent already in the table
DUPLICATES_TO_MERGE = {
    'faded': 'Faded',
    'hemmed/shortened': 'Hemmed/shortened',
    'resewn': 'Resewn',
    'stretched': 'Stretched',
    'worn': 'Worn',
}

# General conditions that overlap with the conditions table - to be removed
GENERAL_CONDITIONS_TO_REMOVE = [
    'acceptable condition',
    'excellent condition',
    'good condition',
    'like new',
    'very good condition',
]

# Remaining lowercase entries to capitalize to sentence case
LOWERCASE_TO_SENTENCE_CASE = {
    'damaged patch': 'Damaged patch',
    'hem undone': 'Hem undone',
    'missing button': 'Missing button',
    'missing patch': 'Missing patch',
    'pilling': 'Pilling',
    'snag': 'Snag',
    'tapered': 'Tapered',
    'torn': 'Torn',
    'waist altered': 'Waist altered',
    'zipper to replace': 'Zipper to replace',
}

# Translations for deleted rows (for downgrade restoration)
DELETED_DUPLICATES_DATA = {
    'faded': {'fr': 'Délavé'},
    'hemmed/shortened': {'fr': 'Ourlé/Raccourci'},
    'resewn': {'fr': 'Recousu'},
    'stretched': {'fr': 'Étiré'},
    'worn': {'fr': 'Usé'},
}

DELETED_GENERAL_CONDITIONS_DATA = {
    'acceptable condition': {'fr': 'État acceptable'},
    'excellent condition': {'fr': 'Excellent état'},
    'good condition': {'fr': 'Bon état'},
    'like new': {'fr': 'Comme neuf'},
    'very good condition': {'fr': 'Très bon état'},
}


def _get_user_schemas(conn):
    """Get all user schemas."""
    result = conn.execute(sa.text(
        "SELECT schema_name FROM information_schema.schemata "
        "WHERE schema_name LIKE 'user_%' ORDER BY schema_name"
    ))
    return [r[0] for r in result.fetchall()]


def _table_exists(conn, schema, table):
    """Check if a table exists in a schema."""
    result = conn.execute(sa.text(
        "SELECT EXISTS ("
        "  SELECT 1 FROM information_schema.tables "
        "  WHERE table_schema = :schema AND table_name = :table"
        ")"
    ), {"schema": schema, "table": table})
    return result.scalar()


def upgrade() -> None:
    conn = op.get_bind()
    user_schemas = _get_user_schemas(conn)

    # --- Phase 1: Fix junction table references in all user schemas ---

    for schema in user_schemas:
        if not _table_exists(conn, schema, 'product_condition_sups'):
            continue

        # 1a. Merge lowercase duplicates into their Title Case version
        for old_val, new_val in DUPLICATES_TO_MERGE.items():
            # Delete rows where product already has the Title Case version
            # (would violate composite PK if we just UPDATE)
            conn.execute(sa.text(f"""
                DELETE FROM {schema}.product_condition_sups
                WHERE condition_sup = :old_val
                AND product_id IN (
                    SELECT product_id FROM {schema}.product_condition_sups
                    WHERE condition_sup = :new_val
                )
            """), {"old_val": old_val, "new_val": new_val})

            # Update remaining lowercase references to Title Case
            conn.execute(sa.text(f"""
                UPDATE {schema}.product_condition_sups
                SET condition_sup = :new_val
                WHERE condition_sup = :old_val
            """), {"old_val": old_val, "new_val": new_val})

        # 1b. Remove general condition references
        conn.execute(sa.text(f"""
            DELETE FROM {schema}.product_condition_sups
            WHERE condition_sup = ANY(:vals)
        """), {"vals": GENERAL_CONDITIONS_TO_REMOVE})

        # 1c. Rename remaining lowercase to sentence case
        for old_val, new_val in LOWERCASE_TO_SENTENCE_CASE.items():
            conn.execute(sa.text(f"""
                UPDATE {schema}.product_condition_sups
                SET condition_sup = :new_val
                WHERE condition_sup = :old_val
            """), {"old_val": old_val, "new_val": new_val})

    # --- Phase 2: Fix condition_sups table ---

    # 2a. Delete lowercase duplicates (references already cleaned up)
    conn.execute(sa.text("""
        DELETE FROM product_attributes.condition_sups
        WHERE name_en = ANY(:vals)
    """), {"vals": list(DUPLICATES_TO_MERGE.keys())})

    # 2b. Delete general conditions (references already cleaned up)
    conn.execute(sa.text("""
        DELETE FROM product_attributes.condition_sups
        WHERE name_en = ANY(:vals)
    """), {"vals": GENERAL_CONDITIONS_TO_REMOVE})

    # 2c. Update remaining lowercase to sentence case
    for old_val, new_val in LOWERCASE_TO_SENTENCE_CASE.items():
        conn.execute(sa.text("""
            UPDATE product_attributes.condition_sups
            SET name_en = :new_val
            WHERE name_en = :old_val
        """), {"old_val": old_val, "new_val": new_val})


def downgrade() -> None:
    conn = op.get_bind()
    user_schemas = _get_user_schemas(conn)

    # --- Reverse Phase 2: Restore condition_sups table ---

    # 2c. Revert sentence case back to lowercase
    for old_val, new_val in LOWERCASE_TO_SENTENCE_CASE.items():
        conn.execute(sa.text("""
            UPDATE product_attributes.condition_sups
            SET name_en = :old_val
            WHERE name_en = :new_val
        """), {"old_val": old_val, "new_val": new_val})

    # 2b. Re-insert general conditions
    for name_en, translations in DELETED_GENERAL_CONDITIONS_DATA.items():
        conn.execute(sa.text("""
            INSERT INTO product_attributes.condition_sups (name_en, name_fr)
            VALUES (:name_en, :name_fr)
            ON CONFLICT (name_en) DO NOTHING
        """), {"name_en": name_en, "name_fr": translations['fr']})

    # 2a. Re-insert lowercase duplicates
    for name_en, translations in DELETED_DUPLICATES_DATA.items():
        conn.execute(sa.text("""
            INSERT INTO product_attributes.condition_sups (name_en, name_fr)
            VALUES (:name_en, :name_fr)
            ON CONFLICT (name_en) DO NOTHING
        """), {"name_en": name_en, "name_fr": translations['fr']})

    # --- Reverse Phase 1: Revert junction table references ---

    for schema in user_schemas:
        if not _table_exists(conn, schema, 'product_condition_sups'):
            continue

        # 1c. Revert sentence case back to lowercase in junction
        for old_val, new_val in LOWERCASE_TO_SENTENCE_CASE.items():
            conn.execute(sa.text(f"""
                UPDATE {schema}.product_condition_sups
                SET condition_sup = :old_val
                WHERE condition_sup = :new_val
            """), {"old_val": old_val, "new_val": new_val})

        # 1a. Revert Title Case back to lowercase for previously duplicated values
        # (we can't know which products had the lowercase version, so skip this)
        # The downgrade is best-effort for junction references
