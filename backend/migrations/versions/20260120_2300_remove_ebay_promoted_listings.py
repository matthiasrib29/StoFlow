"""Remove ebay_promoted_listings table

Revision ID: b34194fc47d0
Revises: a23083ebf36c
Create Date: 2026-01-20 23:00:00

Consolidates ebay_promoted_listings into ebay_products:
- Adds promoted_* columns to ebay_products (campaign_id, ad_id, metrics, etc.)
- Drops ebay_promoted_listings table

The table was redundant since a product can only have one active promotion at a time.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'b34194fc47d0'
down_revision = 'a23083ebf36c'
branch_labels = None
depends_on = None


def get_tenant_schemas(connection) -> list:
    """Get all tenant schemas (user_X and template_tenant)."""
    result = connection.execute(
        text("""
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
        text("""
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
        text("""
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
    """Add promoted columns to ebay_products and drop ebay_promoted_listings."""
    connection = op.get_bind()
    schemas = get_tenant_schemas(connection)

    for schema in schemas:
        # Skip if ebay_products doesn't exist
        if not table_exists(connection, schema, "ebay_products"):
            continue

        # 1. Add promoted_campaign_id column
        if not column_exists(connection, schema, "ebay_products", "promoted_campaign_id"):
            op.add_column(
                "ebay_products",
                sa.Column(
                    "promoted_campaign_id",
                    sa.String(50),
                    nullable=True,
                    comment="ID campagne eBay"
                ),
                schema=schema
            )
            # Create index for campaign_id
            op.create_index(
                f"idx_{schema}_ebay_products_promoted_campaign_id",
                "ebay_products",
                ["promoted_campaign_id"],
                schema=schema
            )

        # 2. Add promoted_campaign_name column
        if not column_exists(connection, schema, "ebay_products", "promoted_campaign_name"):
            op.add_column(
                "ebay_products",
                sa.Column(
                    "promoted_campaign_name",
                    sa.String(255),
                    nullable=True,
                    comment="Nom de la campagne"
                ),
                schema=schema
            )

        # 3. Add promoted_ad_id column (unique)
        if not column_exists(connection, schema, "ebay_products", "promoted_ad_id"):
            op.add_column(
                "ebay_products",
                sa.Column(
                    "promoted_ad_id",
                    sa.String(50),
                    nullable=True,
                    comment="ID unique de l'annonce"
                ),
                schema=schema
            )
            # Create unique index for ad_id
            op.create_index(
                f"idx_{schema}_ebay_products_promoted_ad_id",
                "ebay_products",
                ["promoted_ad_id"],
                unique=True,
                schema=schema
            )

        # 4. Add promoted_bid_percentage column
        if not column_exists(connection, schema, "ebay_products", "promoted_bid_percentage"):
            op.add_column(
                "ebay_products",
                sa.Column(
                    "promoted_bid_percentage",
                    sa.Numeric(5, 2),
                    nullable=True,
                    comment="% d'enchere (2-100)"
                ),
                schema=schema
            )

        # 5. Add promoted_ad_status column
        if not column_exists(connection, schema, "ebay_products", "promoted_ad_status"):
            op.add_column(
                "ebay_products",
                sa.Column(
                    "promoted_ad_status",
                    sa.String(20),
                    nullable=True,
                    comment="ACTIVE, PAUSED, ENDED"
                ),
                schema=schema
            )

        # 6. Add promoted_clicks column
        if not column_exists(connection, schema, "ebay_products", "promoted_clicks"):
            op.add_column(
                "ebay_products",
                sa.Column(
                    "promoted_clicks",
                    sa.Integer(),
                    nullable=False,
                    server_default="0",
                    comment="Nombre de clics"
                ),
                schema=schema
            )

        # 7. Add promoted_impressions column
        if not column_exists(connection, schema, "ebay_products", "promoted_impressions"):
            op.add_column(
                "ebay_products",
                sa.Column(
                    "promoted_impressions",
                    sa.Integer(),
                    nullable=False,
                    server_default="0",
                    comment="Nombre d'impressions"
                ),
                schema=schema
            )

        # 8. Add promoted_sales column
        if not column_exists(connection, schema, "ebay_products", "promoted_sales"):
            op.add_column(
                "ebay_products",
                sa.Column(
                    "promoted_sales",
                    sa.Integer(),
                    nullable=False,
                    server_default="0",
                    comment="Nombre de ventes"
                ),
                schema=schema
            )

        # 9. Add promoted_sales_amount column
        if not column_exists(connection, schema, "ebay_products", "promoted_sales_amount"):
            op.add_column(
                "ebay_products",
                sa.Column(
                    "promoted_sales_amount",
                    sa.Numeric(10, 2),
                    nullable=False,
                    server_default="0",
                    comment="Montant total ventes"
                ),
                schema=schema
            )

        # 10. Add promoted_ad_fees column
        if not column_exists(connection, schema, "ebay_products", "promoted_ad_fees"):
            op.add_column(
                "ebay_products",
                sa.Column(
                    "promoted_ad_fees",
                    sa.Numeric(10, 2),
                    nullable=False,
                    server_default="0",
                    comment="Frais publicitaires"
                ),
                schema=schema
            )

        # 11. Drop ebay_promoted_listings table if exists
        if table_exists(connection, schema, "ebay_promoted_listings"):
            op.drop_table("ebay_promoted_listings", schema=schema)


def downgrade() -> None:
    """Remove promoted columns from ebay_products and recreate ebay_promoted_listings."""
    connection = op.get_bind()
    schemas = get_tenant_schemas(connection)

    for schema in schemas:
        # Skip if ebay_products doesn't exist
        if not table_exists(connection, schema, "ebay_products"):
            continue

        # 1. Recreate ebay_promoted_listings table
        op.create_table(
            "ebay_promoted_listings",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("campaign_id", sa.String(50), nullable=False),
            sa.Column("campaign_name", sa.String(255), nullable=True),
            sa.Column("marketplace_id", sa.String(20), nullable=False),
            sa.Column("product_id", sa.Integer(), nullable=False),
            sa.Column("sku_derived", sa.String(50), nullable=False),
            sa.Column("ad_id", sa.String(50), nullable=False, unique=True),
            sa.Column("listing_id", sa.String(50), nullable=True),
            sa.Column("bid_percentage", sa.Numeric(5, 2), nullable=False),
            sa.Column("ad_status", sa.String(20), nullable=False, server_default="ACTIVE"),
            sa.Column("total_clicks", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("total_impressions", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("total_sales", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("total_sales_amount", sa.Numeric(10, 2), nullable=False, server_default="0"),
            sa.Column("total_ad_fees", sa.Numeric(10, 2), nullable=False, server_default="0"),
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
            f"idx_{schema}_ebay_promoted_listings_campaign_id",
            "ebay_promoted_listings",
            ["campaign_id"],
            schema=schema
        )
        op.create_index(
            f"idx_{schema}_ebay_promoted_listings_marketplace_id",
            "ebay_promoted_listings",
            ["marketplace_id"],
            schema=schema
        )
        op.create_index(
            f"idx_{schema}_ebay_promoted_listings_product_id",
            "ebay_promoted_listings",
            ["product_id"],
            schema=schema
        )
        op.create_index(
            f"idx_{schema}_ebay_promoted_listings_ad_status",
            "ebay_promoted_listings",
            ["ad_status"],
            schema=schema
        )

        # 2. Drop promoted columns from ebay_products
        promoted_columns = [
            "promoted_campaign_id",
            "promoted_campaign_name",
            "promoted_ad_id",
            "promoted_bid_percentage",
            "promoted_ad_status",
            "promoted_clicks",
            "promoted_impressions",
            "promoted_sales",
            "promoted_sales_amount",
            "promoted_ad_fees",
        ]

        for col in promoted_columns:
            if column_exists(connection, schema, "ebay_products", col):
                # Drop index first if it exists
                if col == "promoted_campaign_id":
                    try:
                        op.drop_index(
                            f"idx_{schema}_ebay_products_promoted_campaign_id",
                            table_name="ebay_products",
                            schema=schema
                        )
                    except Exception:
                        pass
                elif col == "promoted_ad_id":
                    try:
                        op.drop_index(
                            f"idx_{schema}_ebay_products_promoted_ad_id",
                            table_name="ebay_products",
                            schema=schema
                        )
                    except Exception:
                        pass
                op.drop_column("ebay_products", col, schema=schema)
