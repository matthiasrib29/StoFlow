"""
Test PostgreSQL connection and basic operations.
"""
import sys
from pathlib import Path

# Ajouter le répertoire parent au PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text

from shared.database import check_database_connection, get_db_context


def test_database():
    """Test database connection and queries."""
    print("\n" + "="*60)
    print("🔍 TESTING POSTGRESQL CONNECTION")
    print("="*60)

    # Test 1: Basic connection
    print("\n1️⃣  Testing basic connection...")
    if check_database_connection():
        print("   ✅ Database connection OK")
    else:
        print("   ❌ Database connection FAILED")
        return False

    # Test 2: Query version
    print("\n2️⃣  Testing PostgreSQL version...")
    try:
        with get_db_context() as db:
            result = db.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"   ✅ PostgreSQL version: {version.split(',')[0]}")
    except Exception as e:
        print(f"   ❌ Version query failed: {e}")
        return False

    # Test 3: List schemas
    print("\n3️⃣  Testing schemas listing...")
    try:
        with get_db_context() as db:
            result = db.execute(text("""
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
                ORDER BY schema_name
            """))
            schemas = [row[0] for row in result.fetchall()]
            print(f"   ✅ Found {len(schemas)} schemas: {', '.join(schemas)}")
    except Exception as e:
        print(f"   ❌ Schemas listing failed: {e}")
        return False

    # Test 4: Create test table
    print("\n4️⃣  Testing table creation...")
    try:
        with get_db_context() as db:
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS public.test_connection (
                    id SERIAL PRIMARY KEY,
                    message TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """))
            db.commit()
            print("   ✅ Test table created")

            # Insert test row
            db.execute(text("""
                INSERT INTO public.test_connection (message)
                VALUES ('Hello from Stoflow!')
            """))
            db.commit()
            print("   ✅ Test row inserted")

            # Query test row
            result = db.execute(text("SELECT * FROM public.test_connection LIMIT 1"))
            row = result.fetchone()
            print(f"   ✅ Test row retrieved: ID={row[0]}, Message='{row[1]}'")

            # Clean up
            db.execute(text("DROP TABLE public.test_connection"))
            db.commit()
            print("   ✅ Test table cleaned up")

    except Exception as e:
        print(f"   ❌ Table operations failed: {e}")
        return False

    print("\n" + "="*60)
    print("✅ ALL POSTGRESQL TESTS PASSED")
    print("="*60 + "\n")

    return True


if __name__ == "__main__":
    success = test_database()
    exit(0 if success else 1)
