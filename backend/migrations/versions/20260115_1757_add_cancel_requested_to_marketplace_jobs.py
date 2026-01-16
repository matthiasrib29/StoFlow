"""add cancel_requested to marketplace_jobs

Revision ID: 381503c3aa77
Revises: 20260115_1730
Create Date: 2026-01-15 17:57:12.084650+01:00

Description:
Add cancel_requested column to marketplace_jobs for cooperative cancellation pattern.
Solves PostgreSQL deadlock issue when cancelling running jobs.

Changes:
- Add cancel_requested BOOLEAN DEFAULT FALSE NOT NULL
- Create partial index WHERE cancel_requested = TRUE for performance
- Apply to public schema (template) + all user_X schemas (multi-tenant)

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '381503c3aa77'
down_revision: str = '20260115_1730'
branch_labels = None
depends_on = None


def get_user_schemas(bind):
    """
    Get all user schemas (user_X).

    Returns:
        list[str]: List of user schema names
    """
    from sqlalchemy import text

    result = bind.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
        ORDER BY schema_name
    """))

    return [row[0] for row in result]


def table_exists(bind, table_name, schema):
    """
    Check if a table exists in a schema.

    Args:
        bind: SQLAlchemy connection
        table_name: Name of the table
        schema: Schema name

    Returns:
        bool: True if table exists
    """
    from sqlalchemy import text

    result = bind.execute(text("""
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = :schema
            AND table_name = :table
        )
    """), {"schema": schema, "table": table_name})

    return result.scalar()


def column_exists(bind, table_name, column_name, schema):
    """
    Check if a column exists in a table.

    Args:
        bind: SQLAlchemy connection
        table_name: Name of the table
        column_name: Name of the column
        schema: Schema name

    Returns:
        bool: True if column exists
    """
    from sqlalchemy import text

    result = bind.execute(text("""
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = :schema
            AND table_name = :table
            AND column_name = :column
        )
    """), {"schema": schema, "table": table_name, "column": column_name})

    return result.scalar()


def upgrade() -> None:
    """
    Add cancel_requested column and index to marketplace_jobs in all schemas.
    """
    bind = op.get_bind()

    # 1. Update public schema (template)
    if table_exists(bind, 'marketplace_jobs', 'public'):
        if not column_exists(bind, 'marketplace_jobs', 'cancel_requested', 'public'):
            op.add_column(
                'marketplace_jobs',
                sa.Column(
                    'cancel_requested',
                    sa.Boolean(),
                    nullable=False,
                    server_default='false',
                    comment='Cooperative cancellation flag. Set to TRUE to request job cancellation.'
                ),
                schema='public'
            )

        # Create partial index for performance (only index TRUE values)
        try:
            op.execute("""
                CREATE INDEX IF NOT EXISTS idx_marketplace_jobs_cancel_requested
                ON public.marketplace_jobs(cancel_requested)
                WHERE cancel_requested = TRUE
            """)
        except Exception:
            # Index already exists, skip
            pass

    # 2. Fan-out to all user_X schemas
    user_schemas = get_user_schemas(bind)

    for schema in user_schemas:
        if table_exists(bind, 'marketplace_jobs', schema):
            # Add cancel_requested column if not exists
            if not column_exists(bind, 'marketplace_jobs', 'cancel_requested', schema):
                op.add_column(
                    'marketplace_jobs',
                    sa.Column(
                        'cancel_requested',
                        sa.Boolean(),
                        nullable=False,
                        server_default='false',
                        comment='Cooperative cancellation flag. Set to TRUE to request job cancellation.'
                    ),
                    schema=schema
                )

            # Create partial index
            try:
                op.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_marketplace_jobs_cancel_requested
                    ON {schema}.marketplace_jobs(cancel_requested)
                    WHERE cancel_requested = TRUE
                """)
            except Exception:
                # Index already exists, skip
                pass


def downgrade() -> None:
    """
    Remove cancel_requested column and index from marketplace_jobs in all schemas.
    """
    bind = op.get_bind()

    # 1. Drop from all user_X schemas first
    user_schemas = get_user_schemas(bind)

    for schema in user_schemas:
        if table_exists(bind, 'marketplace_jobs', schema):
            # Drop index
            try:
                op.execute(f"""
                    DROP INDEX IF EXISTS {schema}.idx_marketplace_jobs_cancel_requested
                """)
            except Exception:
                # Index doesn't exist, skip
                pass

            # Drop cancel_requested column if exists
            if column_exists(bind, 'marketplace_jobs', 'cancel_requested', schema):
                op.drop_column('marketplace_jobs', 'cancel_requested', schema=schema)

    # 2. Drop from public schema (template)
    if table_exists(bind, 'marketplace_jobs', 'public'):
        # Drop index
        try:
            op.execute("""
                DROP INDEX IF EXISTS public.idx_marketplace_jobs_cancel_requested
            """)
        except Exception:
            # Index doesn't exist, skip
            pass

        # Drop cancel_requested column if exists
        if column_exists(bind, 'marketplace_jobs', 'cancel_requested', 'public'):
            op.drop_column('marketplace_jobs', 'cancel_requested', schema='public')
