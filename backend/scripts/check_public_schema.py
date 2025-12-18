"""
Script pour vérifier le schéma public et search_path
"""
import sys
sys.path.append('.')

from sqlalchemy import create_engine, text
from shared.config import settings

def check_public_schema():
    engine = create_engine(settings.database_url)

    with engine.connect() as conn:
        # Check current search_path
        result = conn.execute(text("SHOW search_path"))
        search_path = result.fetchone()[0]
        print(f"Current search_path: {search_path}\n")

        # Check if plugin_tasks exists in public schema
        result = conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'plugin_tasks'
        """))

        if result.fetchone():
            print("✓ Table plugin_tasks exists in PUBLIC schema")

            # Get columns from public.plugin_tasks
            result = conn.execute(text("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = 'plugin_tasks'
                ORDER BY ordinal_position
            """))

            columns = result.fetchall()
            print("\nColumns in public.plugin_tasks:")
            for col_name, data_type in columns:
                print(f"  - {col_name:<20} {data_type}")
        else:
            print("✗ Table plugin_tasks does NOT exist in PUBLIC schema")

if __name__ == '__main__':
    check_public_schema()
