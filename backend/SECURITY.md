# 🛡️ StoFlow Security & Data Protection

This document outlines all data protection mechanisms in place to prevent accidental data loss.

**Last updated**: 2026-01-12

---

## 📊 Database Architecture

### Development Database
- **Port**: `5433`
- **Container**: `stoflow_postgres`
- **Database**: `stoflow_db`
- **Purpose**: Development and manual testing
- **Protected**: ✅ YES (automatic backups before destructive ops)

### Test Database
- **Port**: `5434`
- **Container**: `stoflow_test_db`
- **Database**: `stoflow_test`
- **Purpose**: Automated tests (pytest)
- **Protected**: ⚠️  Partial (pytest controls lifecycle)

---

## 🛡️ Protection Mechanisms

### 1. Database Isolation

| Environment | Port | Database | Use Case |
|-------------|------|----------|----------|
| **Development** | 5433 | `stoflow_db` | Manual testing, development |
| **Test** | 5434 | `stoflow_test` | Automated tests (pytest) |
| **Production** | Railway | `production` | Live application |

**Guarantee**: Tests NEVER touch development database.

**Verification**:
```python
# In tests/conftest.py
SQLALCHEMY_TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://stoflow_test:test_password_123@localhost:5434/stoflow_test"
)
```

**Check**:
```bash
cd backend
./scripts/db-protect.sh verify-test-db
```

---

### 2. Automatic Backup System

#### Script: `scripts/db-backup.sh`

Creates automatic backups of the development database.

**Features**:
- ✅ Interactive (confirmation prompt) or silent (--force)
- ✅ Automatic cleanup (keeps last 10 backups)
- ✅ Database size display before backup
- ✅ Connection check before operation

**Usage**:
```bash
cd backend

# Interactive backup
./scripts/db-backup.sh

# Silent backup (for automation)
./scripts/db-backup.sh --force

# Custom output location
./scripts/db-backup.sh --output ~/my-backup.sql

# Backup test database
./scripts/db-backup.sh --database stoflow_test --port 5434
```

**Storage**: `backend/backups/backup_stoflow_db_YYYYMMDD_HHMMSS.sql`

**Retention**: Last 10 backups (older ones auto-deleted)

---

### 3. Protection Before Destructive Operations

#### Script: `scripts/db-protect.sh`

Prevents accidental data loss by enforcing rules.

**Protected Operations**:
- ⚠️  `alembic downgrade` (rollback migrations)
- ⚠️  `DROP TABLE/SCHEMA/DATABASE`
- ⚠️  `TRUNCATE`
- ⚠️  `DELETE FROM` (bulk delete)
- ⚠️  Manual SQL modifications

**Usage**:

```bash
cd backend

# Before downgrade (creates automatic backup)
./scripts/db-protect.sh pre-downgrade && alembic downgrade -1

# Before DROP operation (requires typing "DROP")
./scripts/db-protect.sh pre-drop
# Then run your DROP command

# Check migration safety
./scripts/db-protect.sh check-migration

# Verify test database is used
./scripts/db-protect.sh verify-test-db
```

---

### 4. Migration Safety Rules

#### ✅ Safe Operations (no backup needed)

```bash
alembic upgrade head       # Apply new migrations (forward only)
alembic history            # View migration history
alembic current            # Check current version
alembic show <revision>    # View migration details
```

#### ⚠️  Dangerous Operations (backup required)

```bash
# ALWAYS create backup before these:
alembic downgrade -1       # Rollback one migration
alembic downgrade <rev>    # Rollback to specific version
alembic revision --autogenerate  # Only after review
```

**Recommended workflow**:
```bash
# 1. Create safety backup
./scripts/db-backup.sh --force

# 2. Run downgrade
alembic downgrade -1

# 3. If something goes wrong, restore:
psql -U stoflow_user -d stoflow_db < backups/backup_stoflow_db_20260112_143000.sql
```

---

### 5. Test Isolation (Pytest)

#### Configuration: `tests/conftest.py`

**Guarantees**:
- ✅ Tests use dedicated database (port 5434)
- ✅ Database structure created via Alembic migrations
- ✅ User schemas cloned from `template_tenant`
- ✅ Automatic cleanup after each test
- ✅ Session-scoped fixtures for performance

**Verification**:
```python
# Pytest automatically sets TEST_DATABASE_URL
SQLALCHEMY_TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://stoflow_test:test_password_123@localhost:5434/stoflow_test"
)
```

**Manual check**:
```bash
cd backend
pytest tests/unit/test_example.py -v

# Output should show:
# 🚀 Setting up test database...
# ✅ Database connection successful
```

---

### 6. Git Worktree Safety

See `CLAUDE.md` for worktree-specific rules (prevents accidental `git reset --hard` on develop).

---

## 🚨 Critical Rules

### Rule 1: Never Touch Development Database Without Backup

```bash
# ❌ WRONG
alembic downgrade -1

# ✅ CORRECT
./scripts/db-backup.sh --force && alembic downgrade -1
```

### Rule 2: Always Use Test Database for Tests

```bash
# ❌ WRONG - Tests using dev database
DATABASE_URL=postgresql://...@localhost:5433/stoflow_db pytest

# ✅ CORRECT - Tests using test database
TEST_DATABASE_URL=postgresql://...@localhost:5434/stoflow_test pytest
# OR (automatic)
pytest
```

### Rule 3: Manual SQL Requires Confirmation + Backup

```bash
# For DROP/TRUNCATE/DELETE operations:
./scripts/db-protect.sh pre-drop
# Type "DROP" to confirm
# Then run your SQL command
```

### Rule 4: Review Autogenerated Migrations

```bash
# ❌ WRONG - Blindly apply
alembic revision --autogenerate -m "changes"
alembic upgrade head

# ✅ CORRECT - Review first
alembic revision --autogenerate -m "changes"
cat migrations/versions/<new_file>.py  # REVIEW CONTENT
alembic upgrade head
```

---

## 📋 Daily Workflow Best Practices

### Starting Development

```bash
cd backend

# 1. Check database status
docker ps | grep postgres

# 2. Start if needed
docker-compose up -d

# 3. Check migration status
alembic current

# 4. Apply pending migrations (safe)
alembic upgrade head
```

### Before Risky Operations

```bash
# 1. Create safety backup
./scripts/db-backup.sh --force

# 2. Verify backup exists
ls -lh backups/backup_*.sql | tail -1

# 3. Proceed with operation
alembic downgrade -1
```

### Running Tests

```bash
# Tests automatically use test database (port 5434)
pytest

# Verify test database is used
./scripts/db-protect.sh verify-test-db
```

---

## 🔍 Troubleshooting

### "Cannot connect to database"

```bash
# Check if Docker containers are running
docker ps | grep postgres

# Start containers if needed
cd backend
docker-compose up -d

# Wait for healthy status
docker ps | grep stoflow_postgres
```

### "Tests are slow / failing"

```bash
# Ensure test database is running
docker ps | grep stoflow_test_db

# Rebuild test database
docker-compose -f docker-compose.test.yml down -v
docker-compose -f docker-compose.test.yml up -d
pytest
```

### "Backup failed"

```bash
# Check disk space
df -h

# Check PostgreSQL is accessible
pg_isready -h localhost -p 5433 -U stoflow_user

# Manual backup
pg_dump -h localhost -p 5433 -U stoflow_user -d stoflow_db > manual_backup.sql
```

---

## 📚 Related Documentation

- [CLAUDE.md](../CLAUDE.md) - Project-specific guidelines
- [CLAUDE.md (backend)](CLAUDE.md) - Backend development rules
- [Docker Compose](docker-compose.yml) - Database container configuration
- [Alembic Migrations](migrations/versions/) - Database schema history

---

## ✅ Security Checklist

Before any database operation, ask yourself:

- [ ] Am I targeting the correct database? (dev vs test vs prod)
- [ ] Is this operation destructive? (DROP, TRUNCATE, DELETE, downgrade)
- [ ] Do I have a recent backup? (< 1 day old)
- [ ] Have I reviewed the migration content? (for autogenerated migrations)
- [ ] Can I restore from backup if something goes wrong?

**If you answered "no" to any of these, STOP and create a backup first.**

---

## 🆘 Emergency Recovery

### If you accidentally deleted data:

```bash
cd backend

# 1. Find latest backup
ls -lht backups/backup_*.sql | head -1

# 2. Restore backup
PGPASSWORD="stoflow_dev_password_2024" psql \
  -h localhost -p 5433 \
  -U stoflow_user \
  -d stoflow_db \
  < backups/backup_stoflow_db_YYYYMMDD_HHMMSS.sql

# 3. Verify data is restored
alembic current
```

### If backup doesn't exist:

Check for:
1. Manual backups in `backend/backup_*.sql`
2. Git-tracked database dumps
3. Docker volume snapshots (if configured)

---

**Remember**: Prevention is better than recovery. Always backup before destructive operations! 🛡️
