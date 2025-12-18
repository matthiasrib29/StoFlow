"""restructure_vinted_products_standalone

Revision ID: ba45bfe5128a
Revises: c53c8e6b804b
Create Date: 2025-12-12 19:11:03.606783+01:00

Restructure vinted_products to be standalone (no FK to products).
- Remove product_id FK
- Make vinted_id NOT NULL
- Add description, currency, color, category, condition, is_draft, is_closed, photo_url, photos_data

Author: Claude
Date: 2025-12-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ba45bfe5128a'
down_revision: Union[str, None] = 'c53c8e6b804b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Restructure vinted_products to standalone."""

    # Drop and recreate for template_tenant
    op.execute("""
        DO $$
        BEGIN
            -- Drop old table if exists
            DROP TABLE IF EXISTS template_tenant.vinted_products CASCADE;

            -- Create new standalone table
            CREATE TABLE template_tenant.vinted_products (
                id SERIAL PRIMARY KEY,
                vinted_id BIGINT NOT NULL UNIQUE,

                -- Product Info
                title TEXT,
                description TEXT,
                price NUMERIC(10, 2),
                currency VARCHAR(3) NOT NULL DEFAULT 'EUR',

                -- Categorization
                brand VARCHAR(100),
                size VARCHAR(50),
                color VARCHAR(50),
                category VARCHAR(200),

                -- Status
                status VARCHAR(20) NOT NULL DEFAULT 'published',
                condition VARCHAR(50),
                is_draft BOOLEAN NOT NULL DEFAULT FALSE,
                is_closed BOOLEAN NOT NULL DEFAULT FALSE,

                -- Analytics
                view_count INTEGER NOT NULL DEFAULT 0,
                favourite_count INTEGER NOT NULL DEFAULT 0,

                -- URLs & Images
                url TEXT,
                photo_url TEXT,
                photos_data TEXT,

                -- Dates
                date DATE,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
            );

            -- Create indexes
            CREATE INDEX idx_vinted_products_status ON template_tenant.vinted_products(status);
            CREATE INDEX idx_vinted_products_vinted_id ON template_tenant.vinted_products(vinted_id);
            CREATE INDEX idx_vinted_products_date ON template_tenant.vinted_products(date);
            CREATE INDEX idx_vinted_products_brand ON template_tenant.vinted_products(brand);

            -- Comments
            COMMENT ON TABLE template_tenant.vinted_products IS 'Produits Vinted (standalone, pas de FK vers products)';
            COMMENT ON COLUMN template_tenant.vinted_products.vinted_id IS 'ID unique Vinted';
            COMMENT ON COLUMN template_tenant.vinted_products.photos_data IS 'JSON des photos [{id, url, ...}]';
        END $$;
    """)

    # Apply to all user schemas
    op.execute("""
        DO $$
        DECLARE
            schema_name TEXT;
        BEGIN
            FOR schema_name IN
                SELECT nspname FROM pg_namespace
                WHERE nspname LIKE 'user_%'
            LOOP
                -- Drop old table
                EXECUTE format('DROP TABLE IF EXISTS %I.vinted_products CASCADE', schema_name);

                -- Create new table
                EXECUTE format('
                    CREATE TABLE %I.vinted_products (
                        id SERIAL PRIMARY KEY,
                        vinted_id BIGINT NOT NULL UNIQUE,
                        title TEXT,
                        description TEXT,
                        price NUMERIC(10, 2),
                        currency VARCHAR(3) NOT NULL DEFAULT ''EUR'',
                        brand VARCHAR(100),
                        size VARCHAR(50),
                        color VARCHAR(50),
                        category VARCHAR(200),
                        status VARCHAR(20) NOT NULL DEFAULT ''published'',
                        condition VARCHAR(50),
                        is_draft BOOLEAN NOT NULL DEFAULT FALSE,
                        is_closed BOOLEAN NOT NULL DEFAULT FALSE,
                        view_count INTEGER NOT NULL DEFAULT 0,
                        favourite_count INTEGER NOT NULL DEFAULT 0,
                        url TEXT,
                        photo_url TEXT,
                        photos_data TEXT,
                        date DATE,
                        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                        updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
                    )', schema_name);

                -- Create indexes
                EXECUTE format('CREATE INDEX idx_%I_vinted_products_status ON %I.vinted_products(status)', schema_name, schema_name);
                EXECUTE format('CREATE INDEX idx_%I_vinted_products_vinted_id ON %I.vinted_products(vinted_id)', schema_name, schema_name);
                EXECUTE format('CREATE INDEX idx_%I_vinted_products_date ON %I.vinted_products(date)', schema_name, schema_name);
                EXECUTE format('CREATE INDEX idx_%I_vinted_products_brand ON %I.vinted_products(brand)', schema_name, schema_name);
            END LOOP;
        END $$;
    """)


def downgrade() -> None:
    """Revert to old structure with product_id FK."""

    # This is destructive - old data won't be restored
    op.execute("""
        DO $$
        BEGIN
            DROP TABLE IF EXISTS template_tenant.vinted_products CASCADE;

            CREATE TABLE template_tenant.vinted_products (
                id SERIAL PRIMARY KEY,
                product_id INTEGER NOT NULL UNIQUE REFERENCES template_tenant.products(id) ON DELETE CASCADE,
                vinted_id BIGINT UNIQUE,
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                date DATE,
                title TEXT,
                price NUMERIC(10, 2),
                url TEXT,
                brand VARCHAR(100),
                size VARCHAR(50),
                view_count INTEGER NOT NULL DEFAULT 0,
                favourite_count INTEGER NOT NULL DEFAULT 0,
                conversations INTEGER NOT NULL DEFAULT 0,
                image_ids TEXT,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
            );

            CREATE INDEX idx_vinted_products_status ON template_tenant.vinted_products(status);
            CREATE INDEX idx_vinted_products_vinted_id ON template_tenant.vinted_products(vinted_id);
            CREATE INDEX idx_vinted_products_date ON template_tenant.vinted_products(date);
        END $$;
    """)

    op.execute("""
        DO $$
        DECLARE
            schema_name TEXT;
        BEGIN
            FOR schema_name IN
                SELECT nspname FROM pg_namespace
                WHERE nspname LIKE 'user_%'
            LOOP
                EXECUTE format('DROP TABLE IF EXISTS %I.vinted_products CASCADE', schema_name);

                EXECUTE format('
                    CREATE TABLE %I.vinted_products (
                        id SERIAL PRIMARY KEY,
                        product_id INTEGER NOT NULL UNIQUE REFERENCES %I.products(id) ON DELETE CASCADE,
                        vinted_id BIGINT UNIQUE,
                        status VARCHAR(20) NOT NULL DEFAULT ''pending'',
                        date DATE,
                        title TEXT,
                        price NUMERIC(10, 2),
                        url TEXT,
                        brand VARCHAR(100),
                        size VARCHAR(50),
                        view_count INTEGER NOT NULL DEFAULT 0,
                        favourite_count INTEGER NOT NULL DEFAULT 0,
                        conversations INTEGER NOT NULL DEFAULT 0,
                        image_ids TEXT,
                        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                        updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
                    )', schema_name, schema_name);
            END LOOP;
        END $$;
    """)
