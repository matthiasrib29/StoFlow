"""normalize_all_attributes_to_title_case

Revision ID: 1111dba9b7f2
Revises: 5513765d1e79
Create Date: 2026-01-07 13:05:04.074375+01:00

Normalize all attribute values to Title Case for consistency:
- Materials: corduroy → Corduroy, elastane → Elastane, etc.
- Fits: athletic → Athletic, baggy → Baggy, bootcut → Bootcut, etc.
"""
from typing import Sequence, Union


from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

from logging import getLogger

logger = getLogger(__name__)


# revision identifiers, used by Alembic.
revision: str = '1111dba9b7f2'
down_revision: Union[str, None] = '5513765d1e79'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_user_schemas(conn):
    """Get list of user schemas."""
    result = conn.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
        ORDER BY schema_name
    """))
    return [row[0] for row in result]


def table_exists(conn, schema, table):
    """Check if a table exists in a schema."""
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = :schema AND table_name = :table
        )
    """), {"schema": schema, "table": table})
    return result.scalar()


def upgrade() -> None:
    """Normalize all attributes to Title Case."""
    conn = op.get_bind()

    # Materials to normalize (lowercase → Title Case)
    materials_map = {
        'corduroy': 'Corduroy',
        'elastane': 'Elastane',
        'flannel': 'Flannel',
        'hemp': 'Hemp',
        'lyocell': 'Lyocell',
        'modal': 'Modal',
        'rayon': 'Rayon',
        'satin': 'Satin',
        'tweed': 'Tweed',
    }

    # Fits to normalize (lowercase → Title Case)
    fits_map = {
        'athletic': 'Athletic',
        'baggy': 'Baggy',
        'bootcut': 'Bootcut',
        'flare': 'Flare',
        'skinny': 'Skinny',
        'straight': 'Straight',
    }

    # ===== 1. NORMALIZE ATTRIBUTE TABLES FIRST (FK constraint) =====

    # 1.1 Materials - Rename lowercase to Title Case
    logger.info("Normalizing materials table...")
    for old_val, new_val in materials_map.items():
        conn.execute(text("""
            UPDATE product_attributes.materials
            SET name_en = :new_val
            WHERE name_en = :old_val
        """), {"old_val": old_val, "new_val": new_val})

    # 1.2 Fits - Rename lowercase to Title Case
    logger.info("Normalizing fits table...")
    for old_val, new_val in fits_map.items():
        conn.execute(text("""
            UPDATE product_attributes.fits
            SET name_en = :new_val
            WHERE name_en = :old_val
        """), {"old_val": old_val, "new_val": new_val})

    # ===== 2. UPDATE PRODUCTS IN USER SCHEMAS =====

    # Get all user schemas
    user_schemas = get_user_schemas(conn)
    logger.info(f"Found {len(user_schemas)} user schemas")

    for schema in user_schemas:
        if not table_exists(conn, schema, 'products'):
            continue

        logger.info(f"Normalizing products in {schema}...")

        # Update materials
        for old_val, new_val in materials_map.items():
            conn.execute(text(f"""
                UPDATE {schema}.products
                SET material = :new_val
                WHERE material = :old_val
            """), {"old_val": old_val, "new_val": new_val})

        # Update fits
        for old_val, new_val in fits_map.items():
            conn.execute(text(f"""
                UPDATE {schema}.products
                SET fit = :new_val
                WHERE fit = :old_val
            """), {"old_val": old_val, "new_val": new_val})

    logger.info("✅ All attributes normalized to Title Case!")


def downgrade() -> None:
    """Revert Title Case normalization."""
    conn = op.get_bind()

    # Get all user schemas
    user_schemas = get_user_schemas(conn)
    logger.info(f"Reverting normalization in {len(user_schemas)} user schemas")

    # ===== 1. REVERT ATTRIBUTE TABLES =====

    # 1.1 Materials - Revert to lowercase
    logger.info("Reverting materials table...")
    materials_map = {
        'Corduroy': 'corduroy',
        'Elastane': 'elastane',
        'Flannel': 'flannel',
        'Hemp': 'hemp',
        'Lyocell': 'lyocell',
        'Modal': 'modal',
        'Rayon': 'rayon',
        'Satin': 'satin',
        'Tweed': 'tweed',
    }

    for new_val, old_val in materials_map.items():
        conn.execute(text("""
            UPDATE product_attributes.materials
            SET name_en = :old_val
            WHERE name_en = :new_val
        """), {"old_val": old_val, "new_val": new_val})

    # 1.2 Fits - Revert to lowercase
    logger.info("Reverting fits table...")
    fits_map = {
        'Athletic': 'athletic',
        'Baggy': 'baggy',
        'Bootcut': 'bootcut',
        'Flare': 'flare',
        'Skinny': 'skinny',
        'Straight': 'straight',
    }

    for new_val, old_val in fits_map.items():
        conn.execute(text("""
            UPDATE product_attributes.fits
            SET name_en = :old_val
            WHERE name_en = :new_val
        """), {"old_val": old_val, "new_val": new_val})

    # ===== 2. REVERT PRODUCTS IN USER SCHEMAS =====

    for schema in user_schemas:
        if not table_exists(conn, schema, 'products'):
            continue

        logger.info(f"Reverting products in {schema}...")

        # Revert materials
        for new_val, old_val in materials_map.items():
            conn.execute(text(f"""
                UPDATE {schema}.products
                SET material = :old_val
                WHERE material = :new_val
            """), {"old_val": old_val, "new_val": new_val})

        # Revert fits
        for new_val, old_val in fits_map.items():
            conn.execute(text(f"""
                UPDATE {schema}.products
                SET fit = :old_val
                WHERE fit = :new_val
            """), {"old_val": old_val, "new_val": new_val})

    logger.info("✅ Normalization reverted successfully!")
