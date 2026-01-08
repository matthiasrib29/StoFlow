"""create_sizes_original

Revision ID: 20260106_1410
Revises: 20260106_1400
Create Date: 2026-01-06 14:10:00.000000+01:00

"""
from typing import Sequence, Union


from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

from logging import getLogger

logger = getLogger(__name__)


# revision identifiers, used by Alembic.
revision: str = '20260106_1410'
down_revision: Union[str, None] = '20260106_1400'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_user_schemas(conn) -> list[str]:
    """Get all user_X schemas dynamically."""
    result = conn.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
        ORDER BY schema_name
    """))
    return [row[0] for row in result]


def upgrade() -> None:
    """
    Create sizes_original table in product_attributes schema.
    Migrate existing size_original data from products tables.
    """
    conn = op.get_bind()

    # Step 1: Create sizes_original table
    op.create_table(
        'sizes_original',
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('name', name='sizes_original_pkey'),
        schema='product_attributes'
    )

    # Create index on name for performance
    op.execute(text("""
        CREATE INDEX ix_sizes_original_name
        ON product_attributes.sizes_original (name);
    """))

    logger.info("✅ Created table product_attributes.sizes_original")

    # Step 2: Migrate existing size_original data from all user schemas
    user_schemas = get_user_schemas(conn)
    template_schemas = ['template_tenant']
    all_schemas = template_schemas + user_schemas

    total_migrated = 0

    for schema in all_schemas:
        # Check if products table exists in schema
        table_exists = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = :schema
                AND table_name = 'products'
            )
        """), {"schema": schema}).scalar()

        if not table_exists:
            logger.info(f"⚠️  Skipping {schema} (products table does not exist)")
            continue

        # Insert distinct size_original values
        result = conn.execute(text(f"""
            INSERT INTO product_attributes.sizes_original (name, created_at)
            SELECT DISTINCT size_original, CURRENT_TIMESTAMP
            FROM {schema}.products
            WHERE size_original IS NOT NULL
              AND size_original != ''
              AND size_original NOT IN (
                  SELECT name FROM product_attributes.sizes_original
              )
            ON CONFLICT (name) DO NOTHING
        """))

        migrated_count = result.rowcount
        total_migrated += migrated_count

        if migrated_count > 0:
            logger.info(f"✅ Migrated {migrated_count} sizes from {schema}.products")

    logger.info(f"✅ Total migrated: {total_migrated} distinct size_original values")


def downgrade() -> None:
    """
    Drop sizes_original table.
    """
    conn = op.get_bind()

    # Drop index
    op.execute(text("""
        DROP INDEX IF EXISTS product_attributes.ix_sizes_original_name;
    """))

    # Drop table
    op.drop_table('sizes_original', schema='product_attributes')

    logger.info("✅ Dropped table product_attributes.sizes_original")
