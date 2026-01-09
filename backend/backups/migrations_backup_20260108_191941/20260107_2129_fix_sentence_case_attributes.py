"""fix_sentence_case_attributes

Fix capitalization to Sentence case (capitalize first letter only):
- Update stretches: Title Case → Sentence case
- Migrate product_condition_sups references: Title Case → Sentence case
- Delete condition_sups Title Case duplicates

Revision ID: cdb2019ff925
Revises: d4e5f6a7b8c9
Create Date: 2026-01-07 21:29:54.882038+01:00

"""
from typing import Sequence, Union


from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

from logging import getLogger

logger = getLogger(__name__)


# revision identifiers, used by Alembic.
revision: str = 'cdb2019ff925'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_user_schemas(conn):
    """Get all user schemas including template_tenant."""
    result = conn.execute(text("""
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%' OR schema_name = 'template_tenant'
        ORDER BY schema_name
    """))
    return [row[0] for row in result]


def table_exists(conn, schema, table):
    """Check if table exists in schema."""
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = :schema AND table_name = :table
        )
    """), {"schema": schema, "table": table})
    return result.scalar()


def upgrade() -> None:
    conn = op.get_bind()

    # ========================================================================
    # STEP 1: Update stretches to Sentence case
    # ========================================================================
    logger.info("Step 1: Updating stretches to Sentence case...")

    stretch_updates = [
        ("No Stretch", "No stretch"),
        ("Slight Stretch", "Slight stretch"),
        ("Moderate Stretch", "Moderate stretch"),
        ("Super Stretch", "Super stretch"),
    ]

    for old_value, new_value in stretch_updates:
        # Update in stretches table
        conn.execute(text("""
            UPDATE product_attributes.stretches
            SET name_en = :new_value,
                name_fr = REPLACE(name_fr, 'Stretch', 'stretch'),
                name_de = REPLACE(name_de, 'Stretch', 'stretch'),
                name_it = REPLACE(name_it, 'Stretch', 'stretch'),
                name_es = REPLACE(name_es, 'Elasticidad', 'elasticidad'),
                name_nl = REPLACE(name_nl, 'Stretch', 'stretch'),
                name_pl = REPLACE(name_pl, 'Rozciągliwość', 'rozciągliwość')
            WHERE name_en = :old_value;
        """), {"old_value": old_value, "new_value": new_value})

        # Update FK references in products tables (all user schemas)
        schemas = get_user_schemas(conn)
        for schema in schemas:
            if table_exists(conn, schema, 'products'):
                conn.execute(text(f"""
                    UPDATE {schema}.products
                    SET stretch = :new_value
                    WHERE stretch = :old_value;
                """), {"old_value": old_value, "new_value": new_value})

    logger.info(f"✅ Updated {len(stretch_updates)} stretch values")

    # ========================================================================
    # STEP 2: Migrate product_condition_sups references (Title → Sentence)
    # ========================================================================
    logger.info("Step 2: Migrating product_condition_sups references...")

    condition_sups_mapping = [
        ("Damaged Button", "Damaged button"),
        ("Frayed Hems", "Frayed hems"),
        ("General Wear", "General wear"),
        ("Hemmed/Shortened", "Hemmed/shortened"),
        ("Knee Wear", "Knee wear"),
        ("Light Discoloration", "Light discoloration"),
        ("Marked Discoloration", "Marked discoloration"),
        ("Multiple Holes", "Multiple holes"),
        ("Multiple Stains", "Multiple stains"),
        ("Seam To Fix", "Seam to fix"),
        ("Single Stain", "Single stain"),
        ("Small Hole", "Small hole"),
        ("Vintage Patina", "Vintage patina"),
        ("Vintage Wear", "Vintage wear"),
    ]

    total_updated = 0
    schemas = get_user_schemas(conn)
    for schema in schemas:
        if table_exists(conn, schema, 'product_condition_sups'):
            for title_case, sentence_case in condition_sups_mapping:
                result = conn.execute(text(f"""
                    UPDATE {schema}.product_condition_sups
                    SET condition_sup = :sentence_case
                    WHERE condition_sup = :title_case;
                """), {"title_case": title_case, "sentence_case": sentence_case})
                total_updated += result.rowcount

    logger.info(f"✅ Migrated {total_updated} product_condition_sups references")

    # ========================================================================
    # STEP 3: Delete Title Case duplicates from condition_sups
    # ========================================================================
    logger.info("Step 3: Deleting Title Case duplicates from condition_sups...")

    title_case_to_delete = [
        "Damaged Button",
        "Frayed Hems",
        "General Wear",
        "Hemmed/Shortened",
        "Knee Wear",
        "Light Discoloration",
        "Marked Discoloration",
        "Multiple Holes",
        "Multiple Stains",
        "Seam To Fix",
        "Single Stain",
        "Small Hole",
        "Vintage Patina",
        "Vintage Wear",
    ]

    for value in title_case_to_delete:
        conn.execute(text("""
            DELETE FROM product_attributes.condition_sups
            WHERE name_en = :value;
        """), {"value": value})

    logger.info(f"✅ Deleted {len(title_case_to_delete)} Title Case duplicates")
    logger.info("🎉 Sentence case migration completed!")


def downgrade() -> None:
    """
    Downgrade not supported - data has been consolidated.
    Cannot restore deleted Title Case values without data loss.
    """
    logger.info("⚠️  Downgrade not supported - Sentence case consolidation is irreversible")
