"""Remove ebay_products_marketplace table

Revision ID: 5c0d1e2f3a4b
Revises: 4b9c0d1e2f3a
Create Date: 2026-01-20 21:00:00

Consolidates ebay_products_marketplace into ebay_products:
- Adds sku_derived, error_message, sold_at columns to ebay_products
- Drops ebay_products_marketplace table

The table was redundant since ebay_products already stores
marketplace_id, ebay_offer_id, ebay_listing_id, status, published_at.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '5c0d1e2f3a4b'
down_revision = '4b9c0d1e2f3a'
branch_labels = None
depends_on = None


def get_tenant_schemas(connection) -> list:
    """Get all tenant schemas (user_X and template_tenant)."""
    result = connection.execute(
        sa.text("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name LIKE 'user_%'
               OR schema_name = 'template_tenant'
        """)
    )
    return [row[0] for row in result]


def table_exists(connection, schema: str, table: str) -> bool:
    """Check if a table exists in a schema."""
    result = connection.execute(
        sa.text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = :schema AND table_name = :table
            )
        """),
        {"schema": schema, "table": table}
    )
    return result.scalar()


def column_exists(connection, schema: str, table: str, column: str) -> bool:
    """Check if a column exists in a table."""
    result = connection.execute(
        sa.text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = :schema
                  AND table_name = :table
                  AND column_name = :column
            )
        """),
        {"schema": schema, "table": table, "column": column}
    )
    return result.scalar()


def upgrade() -> None:
    """Add columns to ebay_products and drop ebay_products_marketplace."""
    connection = op.get_bind()
    schemas = get_tenant_schemas(connection)

    for schema in schemas:
        # Skip if ebay_products doesn't exist
        if not table_exists(connection, schema, "ebay_products"):
            continue

        # 1. Add sku_derived column if not exists
        if not column_exists(connection, schema, "ebay_products", "sku_derived"):
            op.add_column(
                "ebay_products",
                sa.Column(
                    "sku_derived",
                    sa.String(50),
                    nullable=True,
                    comment="SKU derive pour publication (e.g., '1234-FR')"
                ),
                schema=schema
            )
            # Create unique index for sku_derived
            op.create_index(
                f"idx_{schema}_ebay_products_sku_derived",
                "ebay_products",
                ["sku_derived"],
                unique=True,
                schema=schema
            )

        # 2. Add error_message column if not exists
        if not column_exists(connection, schema, "ebay_products", "error_message"):
            op.add_column(
                "ebay_products",
                sa.Column(
                    "error_message",
                    sa.Text(),
                    nullable=True,
                    comment="Message d'erreur si publication echouee"
                ),
                schema=schema
            )

        # 3. Add sold_at column if not exists
        if not column_exists(connection, schema, "ebay_products", "sold_at"):
            op.add_column(
                "ebay_products",
                sa.Column(
                    "sold_at",
                    sa.DateTime(timezone=True),
                    nullable=True,
                    comment="Date de vente"
                ),
                schema=schema
            )

        # 4. Drop ebay_products_marketplace table if exists
        if table_exists(connection, schema, "ebay_products_marketplace"):
            op.drop_table("ebay_products_marketplace", schema=schema)


def downgrade() -> None:
    """Remove columns from ebay_products and recreate ebay_products_marketplace."""
    connection = op.get_bind()
    schemas = get_tenant_schemas(connection)

    for schema in schemas:
        # Skip if ebay_products doesn't exist
        if not table_exists(connection, schema, "ebay_products"):
            continue

        # 1. Recreate ebay_products_marketplace table
        op.create_table(
            "ebay_products_marketplace",
            sa.Column("sku_derived", sa.String(50), primary_key=True, nullable=False),
            sa.Column("product_id", sa.Integer(), nullable=False),
            sa.Column("marketplace_id", sa.String(20), nullable=False),
            sa.Column("ebay_offer_id", sa.BigInteger(), nullable=True),
            sa.Column("ebay_listing_id", sa.BigInteger(), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("sold_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(
                ["product_id"],
                [f"{schema}.products.id"],
                ondelete="CASCADE"
            ),
            schema=schema
        )
        op.create_index(
            f"idx_{schema}_ebay_products_marketplace_product_id",
            "ebay_products_marketplace",
            ["product_id"],
            schema=schema
        )
        op.create_index(
            f"idx_{schema}_ebay_products_marketplace_marketplace_id",
            "ebay_products_marketplace",
            ["marketplace_id"],
            schema=schema
        )
        op.create_index(
            f"idx_{schema}_ebay_products_marketplace_ebay_listing_id",
            "ebay_products_marketplace",
            ["ebay_listing_id"],
            schema=schema
        )
        op.create_index(
            f"idx_{schema}_ebay_products_marketplace_status",
            "ebay_products_marketplace",
            ["status"],
            schema=schema
        )

        # 2. Drop columns from ebay_products
        if column_exists(connection, schema, "ebay_products", "sku_derived"):
            # Drop index first
            try:
                op.drop_index(
                    f"idx_{schema}_ebay_products_sku_derived",
                    table_name="ebay_products",
                    schema=schema
                )
            except Exception:
                pass
            op.drop_column("ebay_products", "sku_derived", schema=schema)

        if column_exists(connection, schema, "ebay_products", "error_message"):
            op.drop_column("ebay_products", "error_message", schema=schema)

        if column_exists(connection, schema, "ebay_products", "sold_at"):
            op.drop_column("ebay_products", "sold_at", schema=schema)
