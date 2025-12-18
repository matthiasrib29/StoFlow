"""
Script pour vérifier que la table vinted_connection existe bien.
"""
import sys
sys.path.append('/home/maribeiro/Stoflow/Stoflow_BackEnd')

from sqlalchemy import create_engine, text
from shared.config import settings

def verify_table():
    engine = create_engine(settings.database_url)

    with engine.connect() as conn:
        # Vérifier dans user_2
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'user_2'
            AND table_name = 'vinted_connection'
            ORDER BY ordinal_position
        """))

        columns = list(result)

        if columns:
            print("✅ Table vinted_connection existe dans user_2")
            print("\nColonnes:")
            for col in columns:
                nullable = "NULL" if col[2] == 'YES' else "NOT NULL"
                print(f"  - {col[0]}: {col[1]} ({nullable})")
        else:
            print("❌ Table vinted_connection n'existe pas dans user_2")

        # Vérifier les index
        result = conn.execute(text("""
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'user_2'
            AND tablename = 'vinted_connection'
        """))

        indexes = list(result)
        if indexes:
            print("\nIndex:")
            for idx in indexes:
                print(f"  - {idx[0]}")

if __name__ == "__main__":
    verify_table()
