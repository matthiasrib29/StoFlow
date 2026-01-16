# Test Database SQL Initialization

This directory contains SQL dumps used to initialize the test database instead of running Alembic migrations.

## Why SQL Dump Instead of Migrations?

**Problem**: Alembic migrations have FK dependency issues when run on a fresh database. Migrations were created incrementally on databases with existing data, so they assume certain records already exist.

**Solution**: Dump the dev database schema + reference data and use that to initialize test databases. This is:
- ✅ **Faster** (~2s vs ~30s)
- ✅ **More reliable** (no FK constraint errors)
- ✅ **Simpler** (one SQL file vs 100+ migration files)

**Trade-off**: SQL dump must be regenerated when schema changes significantly.

## Files

| File | Description | Size |
|------|-------------|------|
| `init_test_db.sql` | Combined schema + data dump | ~10.7k lines |

## Contents

The SQL dump includes:

**Schemas**:
- `public` - Shared tables (users, subscription_quotas, etc.)
- `product_attributes` - Reference data (colors, brands, categories, sizes, etc.)
- `template_tenant` - Template for user-specific schemas

**Data**:
- All `product_attributes` tables (colors, brands, categories, etc.)
- Translations for all attributes (EN, FR, DE, IT, ES, NL, PL)
- ~2000 lines of seed data

## When to Regenerate

Regenerate the SQL dump when:
- ✅ New tables added to `public`, `product_attributes`, or `template_tenant`
- ✅ New columns added to existing tables
- ✅ New reference data added (colors, brands, etc.)
- ⚠️  **NOT needed** for user-specific schema changes (those use `template_tenant`)

## How to Regenerate

### Prerequisites

1. Dev database must be up to date with all migrations:
   ```bash
   cd backend
   docker-compose up -d
   alembic upgrade head
   ```

2. Verify dev database is healthy:
   ```bash
   docker exec stoflow_postgres psql -U stoflow_user -d stoflow_db -c "\dt public.*" | head -20
   docker exec stoflow_postgres psql -U stoflow_user -d stoflow_db -c "\dt product_attributes.*" | head -20
   docker exec stoflow_postgres psql -U stoflow_user -d stoflow_db -c "\dt template_tenant.*" | head -20
   ```

### Regeneration Steps

```bash
cd backend

# 1. Dump schema only (structure)
docker exec stoflow_postgres pg_dump -U stoflow_user -d stoflow_db \
    --schema=public \
    --schema=product_attributes \
    --schema=template_tenant \
    --schema-only \
    --no-owner \
    --no-acl \
    > tests/sql/init_test_db_schema.sql

# 2. Dump reference data (product_attributes only)
docker exec stoflow_postgres pg_dump -U stoflow_user -d stoflow_db \
    --data-only \
    --no-owner \
    --no-acl \
    --schema=product_attributes \
    > tests/sql/init_test_db_data.sql

# 3. Combine into single file with header
cat > tests/sql/init_test_db.sql << 'EOF'
-- StoFlow Test Database Initialization
-- Generated from dev database (stoflow_db)
-- Contains minimal schema and reference data for integration tests
--
-- This script is used instead of running all Alembic migrations to avoid
-- migration ordering issues and speed up test database setup.
--
-- Contents:
-- 1. Schema structure (public, product_attributes, template_tenant)
-- 2. Reference data (colors, brands, categories, sizes, etc.)
--
-- Note: User-specific schemas (user_X) are created dynamically by tests

EOF

cat tests/sql/init_test_db_schema.sql >> tests/sql/init_test_db.sql
cat tests/sql/init_test_db_data.sql >> tests/sql/init_test_db.sql

# 4. Verify
wc -l tests/sql/init_test_db.sql
echo "✅ SQL dump regenerated"

# 5. Cleanup temporary files
rm tests/sql/init_test_db_schema.sql tests/sql/init_test_db_data.sql
```

### Verification

Test that the new dump works:

```bash
# 1. Recreate test database
docker-compose -f docker-compose.test.yml down -v
docker-compose -f docker-compose.test.yml up -d
sleep 5  # Wait for DB to be ready

# 2. Run a simple integration test
pytest tests/integration/services/marketplace/test_marketplace_job_workflow.py::test_create_vinted_job_creates_with_correct_status -xvs
```

If the test passes, the dump is good! Commit it:

```bash
git add tests/sql/init_test_db.sql
git commit -m "test: regenerate SQL dump with latest schema"
```

## Troubleshooting

### Error: "column X does not exist"

**Cause**: Dev database schema doesn't match SQLAlchemy models.

**Solution**: Run migrations on dev database first:
```bash
cd backend
alembic upgrade head
```

Then regenerate the dump.

### Error: "relation already exists"

**Cause**: Test database wasn't fully cleaned before regeneration.

**Solution**: Drop and recreate test database:
```bash
docker-compose -f docker-compose.test.yml down -v
docker-compose -f docker-compose.test.yml up -d
```

### Dump is too large (>20k lines)

**Cause**: Too much data in `product_attributes` tables.

**Solution**: Only dump essential reference data. The current dump should be ~10-12k lines. If larger, check for extra data in dev database.

---

*Last Updated*: 2026-01-16
