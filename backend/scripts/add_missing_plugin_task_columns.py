"""
Script pour ajouter toutes les colonnes manquantes à plugin_tasks
"""
import sys
sys.path.append('.')

from sqlalchemy import create_engine, text
from shared.config import settings

def add_missing_columns():
    engine = create_engine(settings.database_url)

    # Colonnes à ajouter
    columns_to_add = [
        ("platform", "VARCHAR(50)", "Plateforme cible (vinted, ebay, etsy)"),
        ("http_method", "VARCHAR(10)", "Méthode HTTP (POST, PUT, DELETE, GET)"),
        ("path", "VARCHAR(500)", "Path API complet (ex: /api/v2/photos)"),
    ]

    with engine.connect() as conn:
        # Get all user schemas
        result = conn.execute(text("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name LIKE 'user_%'
            ORDER BY schema_name
        """))

        schemas = [row[0] for row in result]
        print(f"Found {len(schemas)} user schemas")

        for schema in schemas:
            print(f"\nProcessing schema: {schema}")

            # Check if plugin_tasks table exists
            table_check = conn.execute(text(f"""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = '{schema}'
                AND table_name = 'plugin_tasks'
            """))

            if not table_check.fetchone():
                print(f"  ⚠️  Table plugin_tasks does not exist in {schema}")
                continue

            for column_name, column_type, comment in columns_to_add:
                # Check if column already exists
                check_result = conn.execute(text(f"""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = '{schema}'
                    AND table_name = 'plugin_tasks'
                    AND column_name = '{column_name}'
                """))

                if check_result.fetchone():
                    print(f"  ✓ Column {column_name} already exists in {schema}")
                    continue

                # Add column
                try:
                    conn.execute(text(f"""
                        ALTER TABLE {schema}.plugin_tasks
                        ADD COLUMN {column_name} {column_type} NULL
                    """))

                    # Add comment
                    conn.execute(text(f"""
                        COMMENT ON COLUMN {schema}.plugin_tasks.{column_name} IS '{comment}'
                    """))

                    # Add index for platform
                    if column_name == 'platform':
                        conn.execute(text(f"""
                            CREATE INDEX ix_{schema}_plugin_tasks_platform
                            ON {schema}.plugin_tasks({column_name})
                        """))

                    conn.commit()
                    print(f"  ✓ Column {column_name} added successfully to {schema}")

                except Exception as e:
                    conn.rollback()
                    print(f"  ✗ Error adding column {column_name} to {schema}: {e}")

if __name__ == '__main__':
    add_missing_columns()
    print("\n✅ Done!")
