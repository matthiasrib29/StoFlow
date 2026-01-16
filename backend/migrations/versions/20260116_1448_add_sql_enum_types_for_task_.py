"""add sql enum types for task orchestration

Revision ID: 8c514d17ef8d
Revises: ff06af3092db
Create Date: 2026-01-16 14:48:53.846678+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8c514d17ef8d'
down_revision: Union[str, None] = 'ff06af3092db'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create SQL ENUM types for task orchestration.

    These types are required for MarketplaceTask and MarketplaceJob models.
    They are created in all schemas (public, template_tenant, and existing user schemas).
    """
    # Create TaskStatus ENUM type
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE taskstatus AS ENUM (
                'pending',
                'processing',
                'success',
                'failed',
                'timeout',
                'cancelled'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create MarketplaceTaskType ENUM type
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE marketplacetasktype AS ENUM (
                'plugin_http',
                'direct_http',
                'db_operation',
                'file_operation'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create JobStatus ENUM type (used by MarketplaceJob)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE jobstatus AS ENUM (
                'pending',
                'processing',
                'completed',
                'failed',
                'cancelled'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)


def downgrade() -> None:
    """
    Drop SQL ENUM types for task orchestration.

    Warning: This will fail if any tables are using these types.
    You must drop or alter those tables first.
    """
    op.execute("DROP TYPE IF EXISTS jobstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS marketplacetasktype CASCADE")
    op.execute("DROP TYPE IF EXISTS taskstatus CASCADE")
