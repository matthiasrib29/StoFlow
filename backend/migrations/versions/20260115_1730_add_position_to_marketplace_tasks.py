"""add position to marketplace_tasks for retry intelligence

Revision ID: 20260115_1730
Revises: 077dc55ef8d0
Create Date: 2026-01-15 17:30:00

Description:
Add position column to marketplace_tasks table for ordered task execution.
Enables intelligent retry: skip completed tasks, retry only failed tasks.

Changes:
- Add position INTEGER column (nullable for backward compat)
- Create composite index (job_id, position) for ordered retrieval
- Create composite index (job_id, status) for retry queries
- Apply to public schema (template) + all user_X schemas (multi-tenant)

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260115_1730'
down_revision = '077dc55ef8d0'
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
    Add position column and indexes to marketplace_tasks in all schemas.
    """
    bind = op.get_bind()

    # 1. Update public schema (template)
    if table_exists(bind, 'marketplace_tasks', 'public'):
        if not column_exists(bind, 'marketplace_tasks', 'position', 'public'):
            op.add_column(
                'marketplace_tasks',
                sa.Column(
                    'position',
                    sa.Integer(),
                    nullable=True,
                    comment='Execution order within job (1, 2, 3...). Enables intelligent retry.'
                ),
                schema='public'
            )

        # Create indexes if not exist (idempotent)
        try:
            op.create_index(
                'ix_marketplace_tasks_job_position',
                'marketplace_tasks',
                ['job_id', 'position'],
                schema='public',
                unique=False
            )
        except Exception:
            # Index already exists, skip
            pass

        try:
            op.create_index(
                'ix_marketplace_tasks_job_status',
                'marketplace_tasks',
                ['job_id', 'status'],
                schema='public',
                unique=False
            )
        except Exception:
            # Index already exists, skip
            pass

    # 2. Fan-out to all user_X schemas
    user_schemas = get_user_schemas(bind)

    for schema in user_schemas:
        if table_exists(bind, 'marketplace_tasks', schema):
            # Add position column if not exists
            if not column_exists(bind, 'marketplace_tasks', 'position', schema):
                op.add_column(
                    'marketplace_tasks',
                    sa.Column(
                        'position',
                        sa.Integer(),
                        nullable=True,
                        comment='Execution order within job (1, 2, 3...). Enables intelligent retry.'
                    ),
                    schema=schema
                )

            # Create indexes if not exist
            try:
                op.create_index(
                    'ix_marketplace_tasks_job_position',
                    'marketplace_tasks',
                    ['job_id', 'position'],
                    schema=schema,
                    unique=False
                )
            except Exception:
                # Index already exists, skip
                pass

            try:
                op.create_index(
                    'ix_marketplace_tasks_job_status',
                    'marketplace_tasks',
                    ['job_id', 'status'],
                    schema=schema,
                    unique=False
                )
            except Exception:
                # Index already exists, skip
                pass


def downgrade() -> None:
    """
    Remove position column and indexes from marketplace_tasks in all schemas.
    """
    bind = op.get_bind()

    # 1. Drop from all user_X schemas first
    user_schemas = get_user_schemas(bind)

    for schema in user_schemas:
        if table_exists(bind, 'marketplace_tasks', schema):
            # Drop indexes
            try:
                op.drop_index(
                    'ix_marketplace_tasks_job_status',
                    'marketplace_tasks',
                    schema=schema
                )
            except Exception:
                # Index doesn't exist, skip
                pass

            try:
                op.drop_index(
                    'ix_marketplace_tasks_job_position',
                    'marketplace_tasks',
                    schema=schema
                )
            except Exception:
                # Index doesn't exist, skip
                pass

            # Drop position column if exists
            if column_exists(bind, 'marketplace_tasks', 'position', schema):
                op.drop_column('marketplace_tasks', 'position', schema=schema)

    # 2. Drop from public schema (template)
    if table_exists(bind, 'marketplace_tasks', 'public'):
        # Drop indexes
        try:
            op.drop_index(
                'ix_marketplace_tasks_job_status',
                'marketplace_tasks',
                schema='public'
            )
        except Exception:
            # Index doesn't exist, skip
            pass

        try:
            op.drop_index(
                'ix_marketplace_tasks_job_position',
                'marketplace_tasks',
                schema='public'
            )
        except Exception:
            # Index doesn't exist, skip
            pass

        # Drop position column if exists
        if column_exists(bind, 'marketplace_tasks', 'position', 'public'):
            op.drop_column('marketplace_tasks', 'position', schema='public')
