"""drop unused vinted_credentials table

Revision ID: drop_vinted_credentials
Revises: rename_color_to_color1
Create Date: 2026-01-05

The vinted_credentials table was never used - no SQLAlchemy model exists.
All connection info is stored in vinted_connection instead.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '20260105_1300'
down_revision = '20260105_1200'
branch_labels = None
depends_on = None


def get_user_schemas(connection) -> list[str]:
    """Get all user_X schemas."""
    result = connection.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
        ORDER BY schema_name
    """))
    return [row[0] for row in result.fetchall()]


def table_exists(connection, schema: str, table: str) -> bool:
    """Check if a table exists in a schema."""
    result = connection.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = :schema AND table_name = :table
        )
    """), {"schema": schema, "table": table})
    return result.scalar()


def upgrade() -> None:
    connection = op.get_bind()

    # Drop from template_tenant
    if table_exists(connection, 'template_tenant', 'vinted_credentials'):
        op.drop_table('vinted_credentials', schema='template_tenant')
        print("  - Dropped vinted_credentials from template_tenant")

    # Drop from all user schemas
    user_schemas = get_user_schemas(connection)
    for schema in user_schemas:
        if table_exists(connection, schema, 'vinted_credentials'):
            op.drop_table('vinted_credentials', schema=schema)
            print(f"  - Dropped vinted_credentials from {schema}")


def downgrade() -> None:
    """Recreate the vinted_credentials table (not recommended - table was unused)."""
    connection = op.get_bind()

    # Recreate in template_tenant
    op.create_table(
        'vinted_credentials',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vinted_user_id', sa.BigInteger(), nullable=True),
        sa.Column('login', sa.String(255), nullable=True),
        sa.Column('csrf_token', sa.String(100), nullable=True),
        sa.Column('anon_id', sa.String(100), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('real_name', sa.String(255), nullable=True),
        sa.Column('birthday', sa.String(10), nullable=True),
        sa.Column('gender', sa.String(20), nullable=True),
        sa.Column('city', sa.String(255), nullable=True),
        sa.Column('country_code', sa.String(10), nullable=True),
        sa.Column('currency', sa.String(10), nullable=False, server_default='EUR'),
        sa.Column('locale', sa.String(10), nullable=False, server_default='fr'),
        sa.Column('profile_url', sa.Text(), nullable=True),
        sa.Column('photo_url', sa.Text(), nullable=True),
        sa.Column('feedback_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('feedback_reputation', sa.Numeric(3, 2), nullable=False, server_default='0.00'),
        sa.Column('item_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_items_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('followers_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('following_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_business', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('business_legal_name', sa.String(255), nullable=True),
        sa.Column('business_legal_code', sa.String(50), nullable=True),
        sa.Column('business_vat', sa.String(50), nullable=True),
        sa.Column('is_connected', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('last_sync', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema='template_tenant'
    )
    op.create_index('ix_template_tenant_vinted_credentials_vinted_user_id', 'vinted_credentials', ['vinted_user_id'], unique=True, schema='template_tenant')

    # Recreate in user schemas
    user_schemas = get_user_schemas(connection)
    for schema in user_schemas:
        op.execute(text(f"""
            CREATE TABLE IF NOT EXISTS {schema}.vinted_credentials (
                LIKE template_tenant.vinted_credentials INCLUDING ALL
            )
        """))
