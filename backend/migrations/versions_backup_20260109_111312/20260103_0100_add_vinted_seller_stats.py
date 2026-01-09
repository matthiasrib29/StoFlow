"""Add seller stats columns to vinted_connection

Revision ID: 20260103_0100
Revises: 20251224_3000
Create Date: 2026-01-03 17:00:00.000000

Adds columns for tracking Vinted seller statistics from /api/v2/users/current:
- item_count: Number of items currently for sale
- total_items_count: Total items (including sold)
- given_item_count: Items sold
- taken_item_count: Items bought
- followers_count: Number of followers
- feedback_count: Total feedback count
- feedback_reputation: Reputation score (0.0-1.0)
- positive_feedback_count: Positive reviews
- negative_feedback_count: Negative reviews
- is_business: Is a business account
- is_on_holiday: Holiday mode status
- stats_updated_at: Last stats update timestamp
"""
from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '20260103_0100'
down_revision = '20251224_3000'
branch_labels = None
depends_on = None


STATS_COLUMNS = [
    ("item_count", "INTEGER DEFAULT NULL"),
    ("total_items_count", "INTEGER DEFAULT NULL"),
    ("given_item_count", "INTEGER DEFAULT NULL"),
    ("taken_item_count", "INTEGER DEFAULT NULL"),
    ("followers_count", "INTEGER DEFAULT NULL"),
    ("feedback_count", "INTEGER DEFAULT NULL"),
    ("feedback_reputation", "DOUBLE PRECISION DEFAULT NULL"),
    ("positive_feedback_count", "INTEGER DEFAULT NULL"),
    ("negative_feedback_count", "INTEGER DEFAULT NULL"),
    ("is_business", "BOOLEAN DEFAULT NULL"),
    ("is_on_holiday", "BOOLEAN DEFAULT NULL"),
    ("stats_updated_at", "TIMESTAMP WITH TIME ZONE DEFAULT NULL"),
]


def upgrade():
    """Add seller stats columns to vinted_connection in all user schemas."""
    conn = op.get_bind()

    # Get all user schemas
    result = conn.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
        AND schema_name <> 'user_invalid'
        ORDER BY schema_name
    """))
    user_schemas = [row[0] for row in result.fetchall()]

    for schema in user_schemas:
        # Check if vinted_connection table exists in this schema
        table_exists = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = '{schema}'
                AND table_name = 'vinted_connection'
            )
        """)).scalar()

        if not table_exists:
            print(f"vinted_connection table doesn't exist in {schema}, skipping")
            continue

        # Check if item_count column already exists (first column we add)
        column_exists = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = '{schema}'
                AND table_name = 'vinted_connection'
                AND column_name = 'item_count'
            )
        """)).scalar()

        if column_exists:
            print(f"Stats columns already exist in {schema}.vinted_connection, skipping")
            continue

        print(f"Adding seller stats columns to {schema}.vinted_connection")

        # Add all stats columns
        for col_name, col_type in STATS_COLUMNS:
            conn.execute(text(f"""
                ALTER TABLE {schema}.vinted_connection
                ADD COLUMN {col_name} {col_type}
            """))

        print(f"  -> Added {len(STATS_COLUMNS)} stats columns to {schema}.vinted_connection")

    # Also update template_tenant if it exists
    template_exists = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'template_tenant'
            AND table_name = 'vinted_connection'
        )
    """)).scalar()

    if template_exists:
        column_exists = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'template_tenant'
                AND table_name = 'vinted_connection'
                AND column_name = 'item_count'
            )
        """)).scalar()

        if not column_exists:
            print("Adding seller stats columns to template_tenant.vinted_connection")
            for col_name, col_type in STATS_COLUMNS:
                conn.execute(text(f"""
                    ALTER TABLE template_tenant.vinted_connection
                    ADD COLUMN {col_name} {col_type}
                """))
            print(f"  -> Added {len(STATS_COLUMNS)} columns to template_tenant.vinted_connection")


def downgrade():
    """Remove seller stats columns from vinted_connection."""
    conn = op.get_bind()

    # Build DROP COLUMN list
    drop_columns = ", ".join([f"DROP COLUMN IF EXISTS {col[0]}" for col in STATS_COLUMNS])

    # Get all user schemas
    result = conn.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
        AND schema_name <> 'user_invalid'
        ORDER BY schema_name
    """))
    user_schemas = [row[0] for row in result.fetchall()]

    for schema in user_schemas:
        table_exists = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = '{schema}'
                AND table_name = 'vinted_connection'
            )
        """)).scalar()

        if table_exists:
            conn.execute(text(f"""
                ALTER TABLE {schema}.vinted_connection
                {drop_columns}
            """))
            print(f"Removed stats columns from {schema}.vinted_connection")

    # Also update template_tenant
    template_exists = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'template_tenant'
            AND table_name = 'vinted_connection'
        )
    """)).scalar()

    if template_exists:
        conn.execute(text(f"""
            ALTER TABLE template_tenant.vinted_connection
            {drop_columns}
        """))
        print("Removed stats columns from template_tenant.vinted_connection")
