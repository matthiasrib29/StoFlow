#!/usr/bin/env python3
"""
Sync User Schemas with Template Tenant

This script synchronizes all user_X schemas with the template_tenant schema.
It detects structural differences (missing tables, columns, indexes) and applies them.

Usage:
    python scripts/sync_user_schemas.py [--dry-run] [--user USER_ID]

Options:
    --dry-run       Show what would be done without making changes
    --user USER_ID  Sync only specific user schema (e.g., --user 1 for user_1)

Author: Claude
Date: 2025-12-22
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from shared.config import settings


def get_engine():
    """Create database engine."""
    return create_engine(str(settings.database_url))


def get_user_schemas(conn) -> list[str]:
    """Get all user schemas (user_1, user_2, etc.)."""
    result = conn.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
        AND schema_name != 'user_information'
        ORDER BY schema_name
    """))
    return [row[0] for row in result.fetchall()]


def get_schema_tables(conn, schema: str) -> dict:
    """
    Get all tables and their columns for a schema.

    Returns:
        dict: {table_name: {column_name: column_info}}
    """
    # Get tables
    tables_result = conn.execute(text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = :schema
        AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """), {"schema": schema})

    tables = {}
    for (table_name,) in tables_result:
        # Get columns for each table
        cols_result = conn.execute(text("""
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length,
                numeric_precision,
                numeric_scale
            FROM information_schema.columns
            WHERE table_schema = :schema
            AND table_name = :table
            ORDER BY ordinal_position
        """), {"schema": schema, "table": table_name})

        columns = {}
        for row in cols_result:
            columns[row[0]] = {
                "data_type": row[1],
                "is_nullable": row[2],
                "column_default": row[3],
                "max_length": row[4],
                "precision": row[5],
                "scale": row[6],
            }

        tables[table_name] = columns

    return tables


def get_schema_indexes(conn, schema: str) -> dict:
    """
    Get all indexes for a schema.

    Returns:
        dict: {table_name: [index_info]}
    """
    result = conn.execute(text("""
        SELECT
            t.relname AS table_name,
            i.relname AS index_name,
            pg_get_indexdef(i.oid) AS index_def
        FROM pg_index ix
        JOIN pg_class t ON t.oid = ix.indrelid
        JOIN pg_class i ON i.oid = ix.indexrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE n.nspname = :schema
        AND NOT ix.indisprimary
        ORDER BY t.relname, i.relname
    """), {"schema": schema})

    indexes = {}
    for row in result:
        table_name = row[0]
        if table_name not in indexes:
            indexes[table_name] = []
        indexes[table_name].append({
            "name": row[1],
            "definition": row[2],
        })

    return indexes


def get_schema_constraints(conn, schema: str) -> dict:
    """
    Get all constraints (FK, unique, check) for a schema.

    Returns:
        dict: {table_name: [constraint_info]}
    """
    result = conn.execute(text("""
        SELECT
            tc.table_name,
            tc.constraint_name,
            tc.constraint_type,
            pg_get_constraintdef(c.oid) AS constraint_def
        FROM information_schema.table_constraints tc
        JOIN pg_constraint c ON c.conname = tc.constraint_name
        JOIN pg_namespace n ON n.oid = c.connamespace AND n.nspname = tc.table_schema
        WHERE tc.table_schema = :schema
        AND tc.constraint_type != 'PRIMARY KEY'
        ORDER BY tc.table_name, tc.constraint_name
    """), {"schema": schema})

    constraints = {}
    for row in result:
        table_name = row[0]
        if table_name not in constraints:
            constraints[table_name] = []
        constraints[table_name].append({
            "name": row[1],
            "type": row[2],
            "definition": row[3],
        })

    return constraints


def generate_create_table_sql(conn, template_schema: str, table_name: str, target_schema: str) -> str:
    """Generate CREATE TABLE SQL by copying from template."""
    # Get the CREATE TABLE statement from template
    result = conn.execute(text("""
        SELECT
            'CREATE TABLE ' || :target_schema || '.' || :table_name || ' (' ||
            string_agg(
                column_name || ' ' ||
                CASE
                    WHEN data_type = 'character varying' THEN 'VARCHAR(' || character_maximum_length || ')'
                    WHEN data_type = 'numeric' THEN 'NUMERIC(' || numeric_precision || ',' || numeric_scale || ')'
                    WHEN data_type = 'ARRAY' THEN udt_name
                    ELSE UPPER(data_type)
                END ||
                CASE WHEN is_nullable = 'NO' THEN ' NOT NULL' ELSE '' END ||
                CASE WHEN column_default IS NOT NULL THEN ' DEFAULT ' || column_default ELSE '' END,
                ', ' ORDER BY ordinal_position
            ) || ')'
        FROM information_schema.columns
        WHERE table_schema = :template_schema
        AND table_name = :table_name
        GROUP BY table_name
    """), {
        "template_schema": template_schema,
        "table_name": table_name,
        "target_schema": target_schema,
    })

    row = result.fetchone()
    return row[0] if row else None


def generate_add_column_sql(
    target_schema: str,
    table_name: str,
    column_name: str,
    column_info: dict
) -> str:
    """Generate ALTER TABLE ADD COLUMN SQL."""
    data_type = column_info["data_type"].upper()

    if data_type == "CHARACTER VARYING" and column_info["max_length"]:
        data_type = f"VARCHAR({column_info['max_length']})"
    elif data_type == "NUMERIC" and column_info["precision"]:
        scale = column_info["scale"] or 0
        data_type = f"NUMERIC({column_info['precision']},{scale})"

    nullable = "" if column_info["is_nullable"] == "YES" else " NOT NULL"
    default = f" DEFAULT {column_info['column_default']}" if column_info["column_default"] else ""

    return f'ALTER TABLE "{target_schema}"."{table_name}" ADD COLUMN "{column_name}" {data_type}{nullable}{default}'


def sync_schema(engine, template_schema: str, target_schema: str, dry_run: bool = False) -> dict:
    """
    Sync target schema with template schema.

    Uses individual transactions for each operation to avoid cascade failures.

    Returns:
        dict with sync statistics
    """
    stats = {
        "tables_created": 0,
        "columns_added": 0,
        "indexes_created": 0,
        "errors": [],
    }

    # Get structures using a read-only connection
    with engine.connect() as conn:
        template_tables = get_schema_tables(conn, template_schema)
        target_tables = get_schema_tables(conn, target_schema)
        template_indexes = get_schema_indexes(conn, template_schema)

    # Skip alembic_version table
    template_tables.pop("alembic_version", None)
    target_tables.pop("alembic_version", None)

    # 1. Create missing tables
    for table_name, columns in template_tables.items():
        if table_name not in target_tables:
            print(f"  📦 Creating table: {target_schema}.{table_name}")

            if not dry_run:
                try:
                    with engine.connect() as conn:
                        sql = generate_create_table_sql(conn, template_schema, table_name, target_schema)
                        if sql:
                            conn.execute(text(sql))
                            conn.commit()
                            stats["tables_created"] += 1
                except Exception as e:
                    error_msg = str(e).split('\n')[0]  # First line only
                    if "already exists" not in error_msg:
                        stats["errors"].append(f"Create {table_name}: {error_msg}")
                        print(f"    ❌ Error: {error_msg}")
                    else:
                        stats["tables_created"] += 1
            else:
                stats["tables_created"] += 1

    # Refresh target tables after creating new ones
    if not dry_run:
        with engine.connect() as conn:
            target_tables = get_schema_tables(conn, target_schema)

    # 2. Add missing columns to existing tables
    for table_name, template_columns in template_tables.items():
        if table_name in target_tables:
            target_columns = target_tables[table_name]

            for col_name, col_info in template_columns.items():
                if col_name not in target_columns:
                    print(f"  📝 Adding column: {target_schema}.{table_name}.{col_name}")

                    if not dry_run:
                        try:
                            with engine.connect() as conn:
                                sql = generate_add_column_sql(target_schema, table_name, col_name, col_info)
                                conn.execute(text(sql))
                                conn.commit()
                                stats["columns_added"] += 1
                        except Exception as e:
                            error_msg = str(e).split('\n')[0]
                            if "already exists" not in error_msg:
                                stats["errors"].append(f"Add {table_name}.{col_name}: {error_msg}")
                                print(f"    ❌ Error: {error_msg}")
                            else:
                                stats["columns_added"] += 1
                    else:
                        stats["columns_added"] += 1

    # 3. Create missing indexes (get fresh target indexes)
    with engine.connect() as conn:
        target_all_indexes = {}
        for table_name in template_indexes:
            target_all_indexes[table_name] = get_schema_indexes(conn, target_schema).get(table_name, [])

    for table_name, indexes in template_indexes.items():
        target_idx = target_all_indexes.get(table_name, [])
        target_idx_names = {idx["name"] for idx in target_idx}

        for idx in indexes:
            # Replace schema name in index definition
            idx_def = idx["definition"].replace(f'"{template_schema}"', f'"{target_schema}"')
            idx_name = idx["name"]

            # Generate a unique index name for target schema
            target_idx_name = idx_name.replace(template_schema, target_schema)

            if idx_name not in target_idx_names and target_idx_name not in target_idx_names:
                print(f"  🔍 Creating index: {target_idx_name}")

                if not dry_run:
                    try:
                        with engine.connect() as conn:
                            # Modify index name in definition
                            idx_def_target = idx_def.replace(idx_name, target_idx_name)
                            conn.execute(text(idx_def_target))
                            conn.commit()
                            stats["indexes_created"] += 1
                    except Exception as e:
                        error_msg = str(e).split('\n')[0]
                        # Index might already exist with different name
                        if "already exists" not in error_msg:
                            stats["errors"].append(f"Index {target_idx_name}: {error_msg}")
                            print(f"    ❌ Error: {error_msg}")
                        else:
                            stats["indexes_created"] += 1
                else:
                    stats["indexes_created"] += 1

    return stats


def main():
    parser = argparse.ArgumentParser(description="Sync user schemas with template_tenant")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without applying")
    parser.add_argument("--user", type=int, help="Sync only specific user (e.g., --user 1)")
    args = parser.parse_args()

    print("=" * 60)
    print("User Schema Synchronization")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print("=" * 60)

    engine = get_engine()

    # Get schemas to sync
    with engine.connect() as conn:
        if args.user:
            user_schemas = [f"user_{args.user}"]
        else:
            user_schemas = get_user_schemas(conn)

    if not user_schemas:
        print("No user schemas found.")
        return

    print(f"\nFound {len(user_schemas)} user schema(s) to sync")
    print(f"Template: template_tenant\n")

    total_stats = {
        "tables_created": 0,
        "columns_added": 0,
        "indexes_created": 0,
        "errors": [],
    }

    for schema in user_schemas:
        print(f"\n{'─' * 40}")
        print(f"🔄 Syncing: {schema}")
        print("─" * 40)

        try:
            stats = sync_schema(engine, "template_tenant", schema, args.dry_run)

            total_stats["tables_created"] += stats["tables_created"]
            total_stats["columns_added"] += stats["columns_added"]
            total_stats["indexes_created"] += stats["indexes_created"]
            total_stats["errors"].extend(stats["errors"])

            if not stats["tables_created"] and not stats["columns_added"] and not stats["indexes_created"] and not stats["errors"]:
                print("  ✅ Already in sync")

        except Exception as e:
            print(f"  ❌ Error syncing {schema}: {e}")
            total_stats["errors"].append(f"{schema}: {e}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Tables created:  {total_stats['tables_created']}")
    print(f"  Columns added:   {total_stats['columns_added']}")
    print(f"  Indexes created: {total_stats['indexes_created']}")

    if total_stats["errors"]:
        print(f"\n  ⚠️  Errors: {len(total_stats['errors'])}")
        for err in total_stats["errors"]:
            print(f"    - {err}")

    print("\n✅ Done!")


if __name__ == "__main__":
    main()
