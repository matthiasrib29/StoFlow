"""add attributes and move distressed

Revision ID: 0d178c306708
Revises: 243e932d0557
Create Date: 2026-01-07 22:53:59.999808+01:00

"""
from typing import Sequence, Union


from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

from logging import getLogger

logger = getLogger(__name__)


# revision identifiers, used by Alembic.
revision: str = '0d178c306708'
down_revision: Union[str, None] = '243e932d0557'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add 22 new product attributes and move "Distressed" from condition_sups to unique_features.

    Steps:
    0. Create parent colors (Blue, Yellow) if absent
    1. Add 12 TRENDS
    2. Add 2 COLORS (with hex + parent)
    3. Add 3 MATERIALS
    4. Add 1 FIT
    5. Add 1 NECKLINE
    6. Add 3 UNIQUE_FEATURES
    7. Migrate "Distressed" from condition_sups to unique_features
    """
    conn = op.get_bind()

    # ========== STEP 0: Create parent colors if absent ==========
    logger.info("STEP 0: Creating parent colors (Blue, Yellow) if absent...")
    conn.execute(text("""
        INSERT INTO product_attributes.colors (name_en, hex_code)
        VALUES ('Blue', '#0000FF'), ('Yellow', '#FFFF00')
        ON CONFLICT (name_en) DO NOTHING;
    """))
    logger.info("✓ Parent colors ensured")

    # ========== STEP 1: Add 12 TRENDS ==========
    logger.info("STEP 1: Adding 12 TRENDS...")
    trends = [
        "Boho revival", "Downtown girl", "Eclectic grandpa", "Glamoratti",
        "Indie sleaze", "Khaki coded", "Mob wife", "Neo deco",
        "Office siren", "Poetcore", "Vamp romance", "Wilderkind"
    ]

    for trend in trends:
        conn.execute(text("""
            INSERT INTO product_attributes.trends (name_en)
            VALUES (:name_en)
            ON CONFLICT (name_en) DO NOTHING;
        """), {"name_en": trend})

    logger.info(f"✓ Added {len(trends)} trends")

    # ========== STEP 2: Add 2 COLORS (with hex + parent) ==========
    logger.info("STEP 2: Adding 2 COLORS with hierarchy...")
    colors = [
        ("Klein blue", "#002FA7", "Blue"),
        ("Vanilla yellow", "#F3E5AB", "Yellow")
    ]

    for name_en, hex_code, parent_color in colors:
        conn.execute(text("""
            INSERT INTO product_attributes.colors (name_en, hex_code, parent_color)
            VALUES (:name_en, :hex_code, :parent_color)
            ON CONFLICT (name_en) DO NOTHING;
        """), {"name_en": name_en, "hex_code": hex_code, "parent_color": parent_color})

    logger.info(f"✓ Added {len(colors)} colors")

    # ========== STEP 3: Add 3 MATERIALS ==========
    logger.info("STEP 3: Adding 3 MATERIALS...")
    materials = ["Crochet", "Lace", "Technical fabric"]

    for material in materials:
        conn.execute(text("""
            INSERT INTO product_attributes.materials (name_en)
            VALUES (:name_en)
            ON CONFLICT (name_en) DO NOTHING;
        """), {"name_en": material})

    logger.info(f"✓ Added {len(materials)} materials")

    # ========== STEP 4: Add 1 FIT ==========
    logger.info("STEP 4: Adding 1 FIT...")
    conn.execute(text("""
        INSERT INTO product_attributes.fits (name_en)
        VALUES ('Balloon')
        ON CONFLICT (name_en) DO NOTHING;
    """))
    logger.info("✓ Added 1 fit")

    # ========== STEP 5: Add 1 NECKLINE ==========
    logger.info("STEP 5: Adding 1 NECKLINE...")
    conn.execute(text("""
        INSERT INTO product_attributes.necklines (name_en)
        VALUES ('Funnel neck')
        ON CONFLICT (name_en) DO NOTHING;
    """))
    logger.info("✓ Added 1 neckline")

    # ========== STEP 6: Add 3 UNIQUE_FEATURES ==========
    logger.info("STEP 6: Adding 3 UNIQUE_FEATURES...")
    features = ["Cutouts", "Fringe", "Tiered"]

    for feature in features:
        conn.execute(text("""
            INSERT INTO product_attributes.unique_features (name_en)
            VALUES (:name_en)
            ON CONFLICT (name_en) DO NOTHING;
        """), {"name_en": feature})

    logger.info(f"✓ Added {len(features)} unique features")

    # ========== STEP 7: Migrate "Distressed" ==========
    logger.info("STEP 7: Migrating 'Distressed' from condition_sups to unique_features...")

    # 7.1 - Add "Distressed" to unique_features
    conn.execute(text("""
        INSERT INTO product_attributes.unique_features (name_en)
        VALUES ('Distressed')
        ON CONFLICT (name_en) DO NOTHING;
    """))
    logger.info("  ✓ Added 'Distressed' to unique_features")

    # 7.2 - Get all user schemas
    schemas = conn.execute(text("""
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%' OR schema_name = 'template_tenant';
    """)).fetchall()

    logger.info(f"  ✓ Found {len(schemas)} schemas to migrate")

    migrated_products = 0
    for (schema,) in schemas:
        # Check if both tables exist
        condition_sups_exists = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = :schema
                AND table_name = 'product_condition_sups'
            );
        """), {"schema": schema}).scalar()

        unique_features_exists = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = :schema
                AND table_name = 'product_unique_features'
            );
        """), {"schema": schema}).scalar()

        # Skip if either table doesn't exist
        if not condition_sups_exists or not unique_features_exists:
            continue

        # 7.3 - Copy existing data to product_unique_features
        result = conn.execute(text(f"""
            INSERT INTO {schema}.product_unique_features (product_id, unique_feature)
            SELECT product_id, 'Distressed'
            FROM {schema}.product_condition_sups
            WHERE condition_sup = 'Distressed'
            ON CONFLICT (product_id, unique_feature) DO NOTHING;
        """))

        affected = result.rowcount if hasattr(result, 'rowcount') else 0
        if affected > 0:
            logger.info(f"    - {schema}: migrated {affected} products")
            migrated_products += affected

        # 7.4 - Delete from product_condition_sups
        conn.execute(text(f"""
            DELETE FROM {schema}.product_condition_sups
            WHERE condition_sup = 'Distressed';
        """))

    # 7.5 - Remove "Distressed" from condition_sups shared table
    conn.execute(text("""
        DELETE FROM product_attributes.condition_sups
        WHERE name_en = 'Distressed';
    """))

    logger.info(f"  ✓ Migrated {migrated_products} total products")
    logger.info("  ✓ Removed 'Distressed' from condition_sups")

    logger.info("\n=== MIGRATION COMPLETED ===")
    logger.info(f"Total additions:")
    logger.info(f"  - 12 trends")
    logger.info(f"  - 2 colors (with hierarchy)")
    logger.info(f"  - 3 materials")
    logger.info(f"  - 1 fit")
    logger.info(f"  - 1 neckline")
    logger.info(f"  - 4 unique features (including migrated 'Distressed')")
    logger.info(f"  - {migrated_products} products migrated")


def downgrade() -> None:
    """
    Reverse all changes made in upgrade().

    Inverse order:
    7. Restore "Distressed" to condition_sups
    6. Remove 3 unique_features
    5. Remove 1 neckline
    4. Remove 1 fit
    3. Remove 3 materials
    2. Remove 2 colors
    1. Remove 12 trends
    0. Do not remove Blue/Yellow (may be used elsewhere)
    """
    conn = op.get_bind()

    logger.info("\n=== STARTING DOWNGRADE ===")

    # ========== STEP 7 inverse: Restore "Distressed" to condition_sups ==========
    logger.info("STEP 7: Restoring 'Distressed' to condition_sups...")

    # 7.1 - Add "Distressed" back to condition_sups
    conn.execute(text("""
        INSERT INTO product_attributes.condition_sups (name_en)
        VALUES ('Distressed')
        ON CONFLICT (name_en) DO NOTHING;
    """))
    logger.info("  ✓ Added 'Distressed' back to condition_sups")

    # 7.2 - Get all user schemas
    schemas = conn.execute(text("""
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%' OR schema_name = 'template_tenant';
    """)).fetchall()

    restored_products = 0
    for (schema,) in schemas:
        # Check if both tables exist
        unique_features_exists = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = :schema
                AND table_name = 'product_unique_features'
            );
        """), {"schema": schema}).scalar()

        condition_sups_exists = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = :schema
                AND table_name = 'product_condition_sups'
            );
        """), {"schema": schema}).scalar()

        # Skip if either table doesn't exist
        if not unique_features_exists or not condition_sups_exists:
            continue

        # 7.3 - Copy back from product_unique_features to product_condition_sups
        result = conn.execute(text(f"""
            INSERT INTO {schema}.product_condition_sups (product_id, condition_sup)
            SELECT product_id, 'Distressed'
            FROM {schema}.product_unique_features
            WHERE unique_feature = 'Distressed'
            ON CONFLICT (product_id, condition_sup) DO NOTHING;
        """))

        affected = result.rowcount if hasattr(result, 'rowcount') else 0
        if affected > 0:
            logger.info(f"    - {schema}: restored {affected} products")
            restored_products += affected

        # 7.4 - Delete from product_unique_features
        conn.execute(text(f"""
            DELETE FROM {schema}.product_unique_features
            WHERE unique_feature = 'Distressed';
        """))

    # 7.5 - Remove "Distressed" from unique_features
    conn.execute(text("""
        DELETE FROM product_attributes.unique_features
        WHERE name_en = 'Distressed';
    """))

    logger.info(f"  ✓ Restored {restored_products} total products")
    logger.info("  ✓ Removed 'Distressed' from unique_features")

    # ========== STEP 6 inverse: Remove 3 unique_features ==========
    logger.info("STEP 6: Removing 3 unique_features...")
    conn.execute(text("""
        DELETE FROM product_attributes.unique_features
        WHERE name_en IN ('Cutouts', 'Fringe', 'Tiered');
    """))
    logger.info("✓ Removed 3 unique features")

    # ========== STEP 5 inverse: Remove 1 neckline ==========
    logger.info("STEP 5: Removing 1 neckline...")
    conn.execute(text("""
        DELETE FROM product_attributes.necklines
        WHERE name_en = 'Funnel neck';
    """))
    logger.info("✓ Removed 1 neckline")

    # ========== STEP 4 inverse: Remove 1 fit ==========
    logger.info("STEP 4: Removing 1 fit...")
    conn.execute(text("""
        DELETE FROM product_attributes.fits
        WHERE name_en = 'Balloon';
    """))
    logger.info("✓ Removed 1 fit")

    # ========== STEP 3 inverse: Remove 3 materials ==========
    logger.info("STEP 3: Removing 3 materials...")
    conn.execute(text("""
        DELETE FROM product_attributes.materials
        WHERE name_en IN ('Crochet', 'Lace', 'Technical fabric');
    """))
    logger.info("✓ Removed 3 materials")

    # ========== STEP 2 inverse: Remove 2 colors ==========
    logger.info("STEP 2: Removing 2 colors...")
    conn.execute(text("""
        DELETE FROM product_attributes.colors
        WHERE name_en IN ('Klein blue', 'Vanilla yellow');
    """))
    logger.info("✓ Removed 2 colors")

    # ========== STEP 1 inverse: Remove 12 trends ==========
    logger.info("STEP 1: Removing 12 trends...")
    conn.execute(text("""
        DELETE FROM product_attributes.trends
        WHERE name_en IN (
            'Boho revival', 'Downtown girl', 'Eclectic grandpa', 'Glamoratti',
            'Indie sleaze', 'Khaki coded', 'Mob wife', 'Neo deco',
            'Office siren', 'Poetcore', 'Vamp romance', 'Wilderkind'
        );
    """))
    logger.info("✓ Removed 12 trends")

    # STEP 0: Do not remove Blue/Yellow (they may be used elsewhere)

    logger.info("\n=== DOWNGRADE COMPLETED ===")
    logger.info("All changes have been rolled back")
