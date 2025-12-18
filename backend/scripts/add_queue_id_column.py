"""
Script pour ajouter la colonne queue_id à plugin_tasks dans tous les schémas user_N
"""
import sys
sys.path.append('.')

from sqlalchemy import create_engine, text
from shared.config import settings

def add_queue_id_column():
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

        print(f"Found {len(schemas)} user schemas")

        for schema in schemas:
            print(f"\nProcessing schema: {schema}")

            # Check if column already exists
            check_result = conn.execute(text(f"""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = '{schema}'
                AND table_name = 'plugin_tasks'
                AND column_name = 'queue_id'
            """))

            if check_result.fetchone():
                print(f"  ✓ Column queue_id already exists in {schema}")
                continue

            # Add column
            try:
                conn.execute(text(f"""
                    ALTER TABLE {schema}.plugin_tasks
                    ADD COLUMN queue_id INTEGER NULL
                """))

                # Add index
                conn.execute(text(f"""
                    CREATE INDEX ix_{schema}_plugin_tasks_queue_id
                    ON {schema}.plugin_tasks(queue_id)
                """))

                conn.commit()
                print(f"  ✓ Column queue_id added successfully to {schema}")

            except Exception as e:
                conn.rollback()
                print(f"  ✗ Error adding column to {schema}: {e}")

if __name__ == '__main__':
    add_queue_id_column()
    print("\n✅ Done!")
