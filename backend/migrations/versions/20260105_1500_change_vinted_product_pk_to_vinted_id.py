"""Change VintedProduct primary key from id to vinted_id

Revision ID: 20260105_1500
Revises: 20260105_1450
Create Date: 2026-01-05 15:00:00.000000

CRITICAL MIGRATION - Changes primary key structure

Before:
- id (Integer, PK auto-increment)
- vinted_id (BigInteger, UNIQUE NOT NULL)

After:
- vinted_id (BigInteger, PK)
- (id column removed)

Note: This migration cannot be easily rolled back. Make a backup before running.
"""
from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '20260105_1500'
down_revision = '20260105_1450'
branch_labels = None
depends_on = None


def upgrade():
    """Change primary key from id to vinted_id in all user schemas and template_tenant."""
    conn = op.get_bind()

    # Get all user schemas + template_tenant
    result = conn.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
           OR schema_name = 'template_tenant'
        ORDER BY schema_name
    """))
    schemas = [row[0] for row in result]

    if not schemas:
        print("No schemas found, skipping migration")
        return

    print(f"Found {len(schemas)} schemas to migrate")

    for schema in schemas:
        # Check if table exists in this schema
        table_exists = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = :schema AND table_name = 'vinted_products'
            )
        """), {"schema": schema}).scalar()

        if not table_exists:
            print(f"  {schema}: vinted_products table not found, skipping")
            continue

        # Check for NULL vinted_id values (should not exist, but verify)
        null_count = conn.execute(text(f"""
            SELECT COUNT(*) FROM {schema}.vinted_products
            WHERE vinted_id IS NULL
        """)).scalar()

        if null_count > 0:
            print(f"  {schema}: WARNING - Found {null_count} rows with NULL vinted_id, deleting them")
            conn.execute(text(f"""
                DELETE FROM {schema}.vinted_products WHERE vinted_id IS NULL
            """))

        # Check if id column exists (might have been removed already)
        id_exists = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = :schema
                AND table_name = 'vinted_products'
                AND column_name = 'id'
            )
        """), {"schema": schema}).scalar()

        if not id_exists:
            print(f"  {schema}: id column already removed, skipping")
            continue

        print(f"  {schema}: Changing PK from id to vinted_id...")

        # Step 1: Drop existing primary key constraint
        # Get the actual PK constraint name
        pk_name = conn.execute(text("""
            SELECT constraint_name
            FROM information_schema.table_constraints
            WHERE table_schema = :schema
            AND table_name = 'vinted_products'
            AND constraint_type = 'PRIMARY KEY'
        """), {"schema": schema}).scalar()

        if pk_name:
            conn.execute(text(f"""
                ALTER TABLE {schema}.vinted_products
                DROP CONSTRAINT {pk_name}
            """))
            print(f"    Dropped PK constraint: {pk_name}")

        # Step 2: Drop unique constraint on vinted_id (if exists)
        unique_constraints = conn.execute(text("""
            SELECT constraint_name
            FROM information_schema.table_constraints
            WHERE table_schema = :schema
            AND table_name = 'vinted_products'
            AND constraint_type = 'UNIQUE'
        """), {"schema": schema}).fetchall()

        for (constraint_name,) in unique_constraints:
            # Check if this constraint is on vinted_id
            col_check = conn.execute(text("""
                SELECT column_name
                FROM information_schema.constraint_column_usage
                WHERE constraint_schema = :schema
                AND constraint_name = :constraint_name
            """), {"schema": schema, "constraint_name": constraint_name}).scalar()

            if col_check == 'vinted_id':
                conn.execute(text(f"""
                    ALTER TABLE {schema}.vinted_products
                    DROP CONSTRAINT {constraint_name}
                """))
                print(f"    Dropped UNIQUE constraint on vinted_id: {constraint_name}")

        # Step 3: Drop index on vinted_id (will be replaced by PK index)
        vinted_id_indexes = conn.execute(text("""
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = :schema
            AND tablename = 'vinted_products'
            AND indexdef LIKE '%vinted_id%'
            AND indexname NOT LIKE '%pkey%'
        """), {"schema": schema}).fetchall()

        for (index_name,) in vinted_id_indexes:
            conn.execute(text(f"""
                DROP INDEX IF EXISTS {schema}.{index_name}
            """))
            print(f"    Dropped index: {index_name}")

        # Step 4: Create new primary key on vinted_id
        conn.execute(text(f"""
            ALTER TABLE {schema}.vinted_products
            ADD PRIMARY KEY (vinted_id)
        """))
        print(f"    Created new PK on vinted_id")

        # Step 5: Drop the old id column
        conn.execute(text(f"""
            ALTER TABLE {schema}.vinted_products
            DROP COLUMN id
        """))
        print(f"    Dropped id column")

        print(f"  {schema}: Migration completed")

    print("Migration completed successfully")


def downgrade():
    """Re-add the id column and restore it as primary key.

    WARNING: This creates a new id column with auto-generated values.
    The original id values are lost and cannot be restored.
    """
    conn = op.get_bind()

    # Get all user schemas + template_tenant
    result = conn.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
           OR schema_name = 'template_tenant'
        ORDER BY schema_name
    """))
    schemas = [row[0] for row in result]

    if not schemas:
        return

    for schema in schemas:
        table_exists = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = :schema AND table_name = 'vinted_products'
            )
        """), {"schema": schema}).scalar()

        if not table_exists:
            continue

        # Check if id column already exists
        id_exists = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = :schema
                AND table_name = 'vinted_products'
                AND column_name = 'id'
            )
        """), {"schema": schema}).scalar()

        if id_exists:
            print(f"  {schema}: id column already exists, skipping")
            continue

        print(f"  {schema}: Restoring id as PK...")

        # Step 1: Drop current PK on vinted_id
        pk_name = conn.execute(text("""
            SELECT constraint_name
            FROM information_schema.table_constraints
            WHERE table_schema = :schema
            AND table_name = 'vinted_products'
            AND constraint_type = 'PRIMARY KEY'
        """), {"schema": schema}).scalar()

        if pk_name:
            conn.execute(text(f"""
                ALTER TABLE {schema}.vinted_products
                DROP CONSTRAINT {pk_name}
            """))

        # Step 2: Add id column with SERIAL
        conn.execute(text(f"""
            ALTER TABLE {schema}.vinted_products
            ADD COLUMN id SERIAL
        """))

        # Step 3: Create PK on id
        conn.execute(text(f"""
            ALTER TABLE {schema}.vinted_products
            ADD PRIMARY KEY (id)
        """))

        # Step 4: Add unique constraint on vinted_id
        conn.execute(text(f"""
            ALTER TABLE {schema}.vinted_products
            ADD CONSTRAINT vinted_products_vinted_id_key UNIQUE (vinted_id)
        """))

        # Step 5: Create index on vinted_id
        conn.execute(text(f"""
            CREATE INDEX idx_vinted_products_vinted_id
            ON {schema}.vinted_products (vinted_id)
        """))

        print(f"  {schema}: Downgrade completed (new id values generated)")
