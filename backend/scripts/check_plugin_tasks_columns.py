"""
Script pour vérifier les colonnes de plugin_tasks dans tous les schémas
"""
import sys
sys.path.append('.')

from sqlalchemy import create_engine, text
from shared.config import settings

def check_columns():
    engine = create_engine(settings.database_url)

    with engine.connect() as conn:
        # Get all user schemas
        result = conn.execute(text("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name LIKE 'user_%'
            ORDER BY schema_name
        """))

        schemas = [row[0] for row in result]
        print(f"Found {len(schemas)} user schemas\n")

        for schema in schemas:
            print(f"=== Schema: {schema} ===")

            # Check if table exists
            table_check = conn.execute(text(f"""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = '{schema}'
                AND table_name = 'plugin_tasks'
            """))

            if not table_check.fetchone():
                print(f"  ⚠️  Table plugin_tasks does not exist\n")
                continue

            # Get all columns
            columns_result = conn.execute(text(f"""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = '{schema}'
                AND table_name = 'plugin_tasks'
                ORDER BY ordinal_position
            """))

            columns = columns_result.fetchall()
            for col_name, data_type, nullable in columns:
                print(f"  ✓ {col_name:<20} {data_type:<15} NULL={nullable}")
            print()

if __name__ == '__main__':
    check_columns()
