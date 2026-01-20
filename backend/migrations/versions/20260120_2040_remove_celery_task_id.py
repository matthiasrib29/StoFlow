"""Remove celery_task_id from marketplace_jobs

Revision ID: 4b9c0d1e2f3a
Revises: 3a8b9c0d1e2f
Create Date: 2026-01-20 20:40:00

Celery has been removed in favor of a custom worker system.
The celery_task_id column is no longer needed.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '4b9c0d1e2f3a'
down_revision = '3a8b9c0d1e2f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Remove celery_task_id column from marketplace_jobs in all user schemas."""
    # Get all user schemas
    connection = op.get_bind()
    result = connection.execute(
        sa.text("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name LIKE 'user_%'
        """)
    )
    schemas = [row[0] for row in result]

    for schema in schemas:
        # Check if column exists
        column_exists = connection.execute(
            sa.text(f"""
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = '{schema}'
                AND table_name = 'marketplace_jobs'
                AND column_name = 'celery_task_id'
            """)
        ).fetchone()

        if column_exists:
            # Drop index first if exists
            try:
                op.drop_index(
                    f'ix_{schema}_marketplace_jobs_celery_task_id',
                    table_name='marketplace_jobs',
                    schema=schema
                )
            except Exception:
                pass  # Index may not exist

            # Drop column
            op.drop_column('marketplace_jobs', 'celery_task_id', schema=schema)


def downgrade() -> None:
    """Re-add celery_task_id column to marketplace_jobs in all user schemas."""
    # Get all user schemas
    connection = op.get_bind()
    result = connection.execute(
        sa.text("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name LIKE 'user_%'
        """)
    )
    schemas = [row[0] for row in result]

    for schema in schemas:
        # Check if table exists
        table_exists = connection.execute(
            sa.text(f"""
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = '{schema}'
                AND table_name = 'marketplace_jobs'
            """)
        ).fetchone()

        if table_exists:
            # Add column back
            op.add_column(
                'marketplace_jobs',
                sa.Column('celery_task_id', sa.String(255), nullable=True),
                schema=schema
            )

            # Add index
            op.create_index(
                f'ix_{schema}_marketplace_jobs_celery_task_id',
                'marketplace_jobs',
                ['celery_task_id'],
                schema=schema
            )
