"""Create dimension tables in product_attributes schema

Revision ID: 20251218_1100
Revises: 20251218_1000
Create Date: 2025-12-18 11:00:00.000000

Creates 6 dimension tables (dim1-dim6) for product measurements.
Each table contains a list of valid numeric values in cm.

Author: Claude
Date: 2025-12-18
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '20251218_1100'
down_revision = '20251218_1000'
branch_labels = None
depends_on = None


# Dimension definitions with value ranges
DIMENSION_TABLES = {
    'dim1': {
        'description': 'Tour de poitrine / Épaules (cm)',
        'description_en': 'Chest / Shoulders (cm)',
        'min': 30,
        'max': 80,
        'step': 1
    },
    'dim2': {
        'description': 'Longueur totale (cm)',
        'description_en': 'Total length (cm)',
        'min': 40,
        'max': 120,
        'step': 1
    },
    'dim3': {
        'description': 'Longueur manche (cm)',
        'description_en': 'Sleeve length (cm)',
        'min': 20,
        'max': 80,
        'step': 1
    },
    'dim4': {
        'description': 'Tour de taille (cm)',
        'description_en': 'Waist (cm)',
        'min': 25,
        'max': 60,
        'step': 1
    },
    'dim5': {
        'description': 'Tour de hanches (cm)',
        'description_en': 'Hips (cm)',
        'min': 30,
        'max': 80,
        'step': 1
    },
    'dim6': {
        'description': 'Entrejambe (cm)',
        'description_en': 'Inseam (cm)',
        'min': 20,
        'max': 100,
        'step': 1
    }
}


def upgrade():
    """
    Create dimension tables in product_attributes schema.
    """
    conn = op.get_bind()

    for table_name, config in DIMENSION_TABLES.items():
        # Check if table already exists
        table_exists = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'product_attributes'
                AND table_name = '{table_name}'
            )
        """)).scalar()

        if table_exists:
            print(f"  ⏭️  Table {table_name} already exists, skipping")
            continue

        # Create table
        conn.execute(text(f"""
            CREATE TABLE product_attributes.{table_name} (
                value INTEGER PRIMARY KEY,
                CONSTRAINT {table_name}_value_positive CHECK (value > 0)
            )
        """))

        # Add comment
        conn.execute(text(f"""
            COMMENT ON TABLE product_attributes.{table_name}
            IS '{config['description_en']} - {config['description']}'
        """))

        # Generate and insert values
        values = list(range(config['min'], config['max'] + 1, config['step']))
        values_str = ', '.join([f"({v})" for v in values])

        conn.execute(text(f"""
            INSERT INTO product_attributes.{table_name} (value)
            VALUES {values_str}
        """))

        print(f"  ✓ Created table {table_name} with {len(values)} values "
              f"({config['min']}-{config['max']} cm)")

    # Create a view to show all dimension metadata
    conn.execute(text("""
        CREATE OR REPLACE VIEW product_attributes.vw_dimension_info AS
        SELECT 'dim1' as dimension,
               'Chest / Shoulders' as name_en,
               'Tour de poitrine / Épaules' as name_fr,
               'cm' as unit,
               30 as min_value,
               80 as max_value,
               'measurement_width' as vinted_field
        UNION ALL
        SELECT 'dim2', 'Total length', 'Longueur totale', 'cm', 40, 120, 'measurement_length'
        UNION ALL
        SELECT 'dim3', 'Sleeve length', 'Longueur manche', 'cm', 20, 80, NULL
        UNION ALL
        SELECT 'dim4', 'Waist', 'Tour de taille', 'cm', 25, 60, NULL
        UNION ALL
        SELECT 'dim5', 'Hips', 'Tour de hanches', 'cm', 30, 80, NULL
        UNION ALL
        SELECT 'dim6', 'Inseam', 'Entrejambe', 'cm', 20, 100, NULL
    """))
    print("  ✓ Created vw_dimension_info view")


def downgrade():
    """
    Drop dimension tables.
    """
    conn = op.get_bind()

    # Drop view first
    conn.execute(text("DROP VIEW IF EXISTS product_attributes.vw_dimension_info"))
    print("  ✓ Dropped vw_dimension_info view")

    # Drop tables
    for table_name in DIMENSION_TABLES.keys():
        table_exists = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'product_attributes'
                AND table_name = '{table_name}'
            )
        """)).scalar()

        if table_exists:
            conn.execute(text(f"DROP TABLE product_attributes.{table_name}"))
            print(f"  ✓ Dropped table {table_name}")
        else:
            print(f"  ⏭️  Table {table_name} doesn't exist, skipping")
