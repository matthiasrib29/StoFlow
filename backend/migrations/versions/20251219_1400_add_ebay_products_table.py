"""add_ebay_products_table

Revision ID: f8a3c5d7e9b1
Revises: 20251219_1000_add_permissions_tables
Create Date: 2025-12-19 14:00:00.000000+01:00

Create ebay_products table for storing eBay inventory items.
Standalone table with optional FK to products (1:1 relationship).
Applies to template_tenant and all user_X schemas.

Author: Claude
Date: 2025-12-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251219_1400'
down_revision: Union[str, None] = '20251219_1300'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create ebay_products table in template_tenant and all user schemas."""

    # Create table in template_tenant
    op.execute("""
        DO $$
        BEGIN
            -- Create ebay_products table
            CREATE TABLE IF NOT EXISTS template_tenant.ebay_products (
                id SERIAL PRIMARY KEY,
                ebay_sku VARCHAR(100) NOT NULL UNIQUE,
                product_id INTEGER UNIQUE REFERENCES template_tenant.products(id) ON DELETE SET NULL ON UPDATE CASCADE,

                -- Product Info
                title TEXT,
                description TEXT,
                price NUMERIC(10, 2),
                currency VARCHAR(3) NOT NULL DEFAULT 'EUR',

                -- Categorization
                brand VARCHAR(100),
                size VARCHAR(50),
                color VARCHAR(50),
                material VARCHAR(100),
                category_id VARCHAR(50),
                category_name VARCHAR(255),

                -- Condition
                condition VARCHAR(50),
                condition_description TEXT,

                -- Availability
                quantity INTEGER NOT NULL DEFAULT 1,
                availability_type VARCHAR(50) DEFAULT 'IN_STOCK',

                -- Marketplace
                marketplace_id VARCHAR(20) NOT NULL DEFAULT 'EBAY_FR',

                -- eBay IDs
                ebay_listing_id BIGINT,
                ebay_offer_id BIGINT,

                -- Images & Aspects
                image_urls TEXT,
                aspects TEXT,

                -- Status
                status VARCHAR(20) NOT NULL DEFAULT 'active',

                -- Listing details
                listing_format VARCHAR(50),
                listing_duration VARCHAR(20),

                -- Package details
                package_weight_value NUMERIC(10, 2),
                package_weight_unit VARCHAR(10),

                -- Location
                location VARCHAR(100),
                country VARCHAR(2),

                -- Timestamps
                published_at TIMESTAMP WITH TIME ZONE,
                last_synced_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
            );

            -- Create indexes
            CREATE INDEX IF NOT EXISTS idx_ebay_products_status ON template_tenant.ebay_products(status);
            CREATE INDEX IF NOT EXISTS idx_ebay_products_ebay_sku ON template_tenant.ebay_products(ebay_sku);
            CREATE INDEX IF NOT EXISTS idx_ebay_products_marketplace_id ON template_tenant.ebay_products(marketplace_id);
            CREATE INDEX IF NOT EXISTS idx_ebay_products_brand ON template_tenant.ebay_products(brand);
            CREATE INDEX IF NOT EXISTS idx_ebay_products_ebay_listing_id ON template_tenant.ebay_products(ebay_listing_id);
            CREATE INDEX IF NOT EXISTS idx_ebay_products_product_id ON template_tenant.ebay_products(product_id);

            -- Comments
            COMMENT ON TABLE template_tenant.ebay_products IS 'Produits eBay importés depuis Inventory API';
            COMMENT ON COLUMN template_tenant.ebay_products.ebay_sku IS 'SKU unique eBay (inventory item)';
            COMMENT ON COLUMN template_tenant.ebay_products.product_id IS 'FK optionnelle vers Product Stoflow (1:1)';
            COMMENT ON COLUMN template_tenant.ebay_products.aspects IS 'JSON des aspects eBay (Brand, Color, Size, etc.)';
            COMMENT ON COLUMN template_tenant.ebay_products.image_urls IS 'JSON des URLs d images';
        END $$;
    """)

    # Apply to all user schemas (only those with products table)
    op.execute("""
        DO $$
        DECLARE
            schema_name TEXT;
        BEGIN
            FOR schema_name IN
                SELECT nspname FROM pg_namespace
                WHERE nspname LIKE 'user_%'
                AND EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = nspname
                    AND table_name = 'products'
                )
            LOOP
                -- Create table if not exists
                EXECUTE format('
                    CREATE TABLE IF NOT EXISTS %I.ebay_products (
                        id SERIAL PRIMARY KEY,
                        ebay_sku VARCHAR(100) NOT NULL UNIQUE,
                        product_id INTEGER UNIQUE REFERENCES %I.products(id) ON DELETE SET NULL ON UPDATE CASCADE,

                        -- Product Info
                        title TEXT,
                        description TEXT,
                        price NUMERIC(10, 2),
                        currency VARCHAR(3) NOT NULL DEFAULT ''EUR'',

                        -- Categorization
                        brand VARCHAR(100),
                        size VARCHAR(50),
                        color VARCHAR(50),
                        material VARCHAR(100),
                        category_id VARCHAR(50),
                        category_name VARCHAR(255),

                        -- Condition
                        condition VARCHAR(50),
                        condition_description TEXT,

                        -- Availability
                        quantity INTEGER NOT NULL DEFAULT 1,
                        availability_type VARCHAR(50) DEFAULT ''IN_STOCK'',

                        -- Marketplace
                        marketplace_id VARCHAR(20) NOT NULL DEFAULT ''EBAY_FR'',

                        -- eBay IDs
                        ebay_listing_id BIGINT,
                        ebay_offer_id BIGINT,

                        -- Images & Aspects
                        image_urls TEXT,
                        aspects TEXT,

                        -- Status
                        status VARCHAR(20) NOT NULL DEFAULT ''active'',

                        -- Listing details
                        listing_format VARCHAR(50),
                        listing_duration VARCHAR(20),

                        -- Package details
                        package_weight_value NUMERIC(10, 2),
                        package_weight_unit VARCHAR(10),

                        -- Location
                        location VARCHAR(100),
                        country VARCHAR(2),

                        -- Timestamps
                        published_at TIMESTAMP WITH TIME ZONE,
                        last_synced_at TIMESTAMP WITH TIME ZONE,
                        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                        updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
                    )', schema_name, schema_name);

                -- Create indexes
                EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%s_ebay_products_status ON %I.ebay_products(status)', schema_name, schema_name);
                EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%s_ebay_products_ebay_sku ON %I.ebay_products(ebay_sku)', schema_name, schema_name);
                EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%s_ebay_products_marketplace_id ON %I.ebay_products(marketplace_id)', schema_name, schema_name);
                EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%s_ebay_products_brand ON %I.ebay_products(brand)', schema_name, schema_name);
                EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%s_ebay_products_ebay_listing_id ON %I.ebay_products(ebay_listing_id)', schema_name, schema_name);
                EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%s_ebay_products_product_id ON %I.ebay_products(product_id)', schema_name, schema_name);
            END LOOP;
        END $$;
    """)


def downgrade() -> None:
    """Drop ebay_products table from all schemas."""

    # Drop from template_tenant
    op.execute("DROP TABLE IF EXISTS template_tenant.ebay_products CASCADE;")

    # Drop from all user schemas
    op.execute("""
        DO $$
        DECLARE
            schema_name TEXT;
        BEGIN
            FOR schema_name IN
                SELECT nspname FROM pg_namespace
                WHERE nspname LIKE 'user_%'
            LOOP
                EXECUTE format('DROP TABLE IF EXISTS %I.ebay_products CASCADE', schema_name);
            END LOOP;
        END $$;
    """)
