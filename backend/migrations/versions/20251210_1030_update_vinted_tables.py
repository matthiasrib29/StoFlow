"""update_vinted_tables

Revision ID: e8f9a0b1c2d3
Revises: 65d4e8f9a0b1
Create Date: 2025-12-10 10:30:00.000000+01:00

IMPORTANT: Cette migration met à jour les tables Vinted dans template_tenant.

Modifications:
1. Mise à jour vinted_products pour correspondre au nouveau modèle:
   - Renommer vinted_item_id -> vinted_id
   - Supprimer colonnes mapping (vinted_category_id, vinted_brand_id, vinted_color_ids, vinted_size_id, vinted_status_id)
   - Ajouter colonnes publication (status, date, title, price, url, view_count, favourite_count, conversations, image_ids)

2. Ajout table vinted_error_logs pour tracking des erreurs

Architecture:
- Tables dans schema template_tenant (template pour user_{id})
- Isolation multi-tenant via schema PostgreSQL
- Foreign keys avec CASCADE delete

Author: Claude
Date: 2025-12-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e8f9a0b1c2d3'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Met à jour les tables Vinted dans template_tenant.
    """

    # ===== 1. MISE À JOUR vinted_products =====

    # Supprimer les anciens indexes (si existants)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = 'template_tenant'
                AND tablename = 'vinted_products'
                AND indexname = 'ix_template_tenant_vinted_products_vinted_item_id'
            ) THEN
                DROP INDEX template_tenant.ix_template_tenant_vinted_products_vinted_item_id;
            END IF;
        END $$;
    """)

    # Gérer vinted_id: renommer vinted_item_id si existe, sinon créer
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'template_tenant'
                AND table_name = 'vinted_products'
                AND column_name = 'vinted_item_id'
            ) THEN
                ALTER TABLE template_tenant.vinted_products
                RENAME COLUMN vinted_item_id TO vinted_id;
            ELSIF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'template_tenant'
                AND table_name = 'vinted_products'
                AND column_name = 'vinted_id'
            ) THEN
                ALTER TABLE template_tenant.vinted_products
                ADD COLUMN vinted_id BIGINT;
                COMMENT ON COLUMN template_tenant.vinted_products.vinted_id IS 'ID du produit sur Vinted';
            END IF;
        END $$;
    """)

    # Supprimer colonnes mapping (si existantes)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'template_tenant' AND table_name = 'vinted_products' AND column_name = 'vinted_category_id') THEN
                ALTER TABLE template_tenant.vinted_products DROP COLUMN vinted_category_id;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'template_tenant' AND table_name = 'vinted_products' AND column_name = 'vinted_brand_id') THEN
                ALTER TABLE template_tenant.vinted_products DROP COLUMN vinted_brand_id;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'template_tenant' AND table_name = 'vinted_products' AND column_name = 'vinted_color_ids') THEN
                ALTER TABLE template_tenant.vinted_products DROP COLUMN vinted_color_ids;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'template_tenant' AND table_name = 'vinted_products' AND column_name = 'vinted_size_id') THEN
                ALTER TABLE template_tenant.vinted_products DROP COLUMN vinted_size_id;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'template_tenant' AND table_name = 'vinted_products' AND column_name = 'vinted_status_id') THEN
                ALTER TABLE template_tenant.vinted_products DROP COLUMN vinted_status_id;
            END IF;
        END $$;
    """)

    # Gérer url: renommer vinted_url si existe, sinon créer
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'template_tenant'
                AND table_name = 'vinted_products'
                AND column_name = 'vinted_url'
            ) THEN
                ALTER TABLE template_tenant.vinted_products
                RENAME COLUMN vinted_url TO url;
            ELSIF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'template_tenant'
                AND table_name = 'vinted_products'
                AND column_name = 'url'
            ) THEN
                ALTER TABLE template_tenant.vinted_products
                ADD COLUMN url TEXT;
                COMMENT ON COLUMN template_tenant.vinted_products.url IS 'URL du produit sur Vinted';
            END IF;
        END $$;
    """)

    # Ajouter nouvelles colonnes publication (si non existantes)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'template_tenant' AND table_name = 'vinted_products' AND column_name = 'status') THEN
                ALTER TABLE template_tenant.vinted_products ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'pending';
                COMMENT ON COLUMN template_tenant.vinted_products.status IS 'Statut: pending, published, error, deleted';
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'template_tenant' AND table_name = 'vinted_products' AND column_name = 'date') THEN
                ALTER TABLE template_tenant.vinted_products ADD COLUMN date DATE;
                COMMENT ON COLUMN template_tenant.vinted_products.date IS 'Date de publication sur Vinted';
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'template_tenant' AND table_name = 'vinted_products' AND column_name = 'title') THEN
                ALTER TABLE template_tenant.vinted_products ADD COLUMN title TEXT;
                COMMENT ON COLUMN template_tenant.vinted_products.title IS 'Titre utilisé sur Vinted';
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'template_tenant' AND table_name = 'vinted_products' AND column_name = 'price') THEN
                ALTER TABLE template_tenant.vinted_products ADD COLUMN price NUMERIC(10, 2);
                COMMENT ON COLUMN template_tenant.vinted_products.price IS 'Prix de vente sur Vinted';
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'template_tenant' AND table_name = 'vinted_products' AND column_name = 'view_count') THEN
                ALTER TABLE template_tenant.vinted_products ADD COLUMN view_count INTEGER NOT NULL DEFAULT 0;
                COMMENT ON COLUMN template_tenant.vinted_products.view_count IS 'Nombre de vues sur Vinted';
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'template_tenant' AND table_name = 'vinted_products' AND column_name = 'favourite_count') THEN
                ALTER TABLE template_tenant.vinted_products ADD COLUMN favourite_count INTEGER NOT NULL DEFAULT 0;
                COMMENT ON COLUMN template_tenant.vinted_products.favourite_count IS 'Nombre de favoris sur Vinted';
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'template_tenant' AND table_name = 'vinted_products' AND column_name = 'conversations') THEN
                ALTER TABLE template_tenant.vinted_products ADD COLUMN conversations INTEGER NOT NULL DEFAULT 0;
                COMMENT ON COLUMN template_tenant.vinted_products.conversations IS 'Nombre de conversations sur Vinted';
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'template_tenant' AND table_name = 'vinted_products' AND column_name = 'image_ids') THEN
                ALTER TABLE template_tenant.vinted_products ADD COLUMN image_ids TEXT;
                COMMENT ON COLUMN template_tenant.vinted_products.image_ids IS 'IDs images uploadées (CSV)';
            END IF;
        END $$;
    """)

    # Ajouter created_at si absent
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'template_tenant'
                AND table_name = 'vinted_products'
                AND column_name = 'created_at'
            ) THEN
                ALTER TABLE template_tenant.vinted_products
                ADD COLUMN created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now();
            END IF;
        END $$;
    """)

    # Créer indexes (si non existants)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname = 'template_tenant' AND indexname = 'idx_vinted_products_status') THEN
                CREATE INDEX idx_vinted_products_status ON template_tenant.vinted_products(status);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname = 'template_tenant' AND indexname = 'idx_vinted_products_vinted_id') THEN
                CREATE INDEX idx_vinted_products_vinted_id ON template_tenant.vinted_products(vinted_id);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname = 'template_tenant' AND indexname = 'idx_vinted_products_date') THEN
                CREATE INDEX idx_vinted_products_date ON template_tenant.vinted_products(date);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname = 'template_tenant' AND indexname = 'idx_vinted_products_vinted_id_unique') THEN
                CREATE UNIQUE INDEX idx_vinted_products_vinted_id_unique ON template_tenant.vinted_products(vinted_id) WHERE vinted_id IS NOT NULL;
            END IF;
        END $$;
    """)

    # Ajouter contrainte unique sur product_id (si non existante)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'uq_vinted_products_product_id'
                AND connamespace = 'template_tenant'::regnamespace
            ) THEN
                ALTER TABLE template_tenant.vinted_products
                ADD CONSTRAINT uq_vinted_products_product_id UNIQUE (product_id);
            END IF;
        END $$;
    """)

    # ===== 2. CRÉATION TABLE vinted_error_logs (si non existante) =====
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'template_tenant'
                AND table_name = 'vinted_error_logs'
            ) THEN
                CREATE TABLE template_tenant.vinted_error_logs (
                    id SERIAL PRIMARY KEY,
                    product_id INTEGER NOT NULL,
                    operation VARCHAR(20) NOT NULL,
                    error_type VARCHAR(50) NOT NULL,
                    error_message TEXT NOT NULL,
                    error_details TEXT,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                    FOREIGN KEY (product_id) REFERENCES template_tenant.products(id) ON DELETE CASCADE
                );

                COMMENT ON COLUMN template_tenant.vinted_error_logs.operation IS 'Type d''opération: publish, update, delete';
                COMMENT ON COLUMN template_tenant.vinted_error_logs.error_type IS 'Type d''erreur: mapping_error, api_error, image_error, validation_error';
                COMMENT ON COLUMN template_tenant.vinted_error_logs.error_message IS 'Message d''erreur principal';
                COMMENT ON COLUMN template_tenant.vinted_error_logs.error_details IS 'Détails supplémentaires (JSON, traceback, etc.)';

                -- Indexes
                CREATE INDEX idx_vinted_error_logs_product_id ON template_tenant.vinted_error_logs(product_id);
                CREATE INDEX idx_vinted_error_logs_error_type ON template_tenant.vinted_error_logs(error_type);
                CREATE INDEX idx_vinted_error_logs_created_at ON template_tenant.vinted_error_logs(created_at);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    """
    Revient à l'ancienne structure vinted_products et supprime vinted_error_logs.
    """

    # ===== 1. SUPPRIMER vinted_error_logs =====
    op.drop_index('idx_vinted_error_logs_created_at', table_name='vinted_error_logs', schema='template_tenant')
    op.drop_index('idx_vinted_error_logs_error_type', table_name='vinted_error_logs', schema='template_tenant')
    op.drop_index('idx_vinted_error_logs_product_id', table_name='vinted_error_logs', schema='template_tenant')
    op.drop_table('vinted_error_logs', schema='template_tenant')

    # ===== 2. RESTAURER vinted_products =====

    # Supprimer nouveaux indexes
    op.drop_index('idx_vinted_products_vinted_id_unique', table_name='vinted_products', schema='template_tenant')
    op.drop_constraint('uq_vinted_products_product_id', 'vinted_products', schema='template_tenant')
    op.drop_index('idx_vinted_products_date', table_name='vinted_products', schema='template_tenant')
    op.drop_index('idx_vinted_products_vinted_id', table_name='vinted_products', schema='template_tenant')
    op.drop_index('idx_vinted_products_status', table_name='vinted_products', schema='template_tenant')

    # Supprimer nouvelles colonnes
    op.drop_column('vinted_products', 'image_ids', schema='template_tenant')
    op.drop_column('vinted_products', 'conversations', schema='template_tenant')
    op.drop_column('vinted_products', 'favourite_count', schema='template_tenant')
    op.drop_column('vinted_products', 'view_count', schema='template_tenant')
    op.drop_column('vinted_products', 'price', schema='template_tenant')
    op.drop_column('vinted_products', 'title', schema='template_tenant')
    op.drop_column('vinted_products', 'date', schema='template_tenant')
    op.drop_column('vinted_products', 'status', schema='template_tenant')

    # Renommer url -> vinted_url
    op.alter_column('vinted_products', 'url', new_column_name='vinted_url', schema='template_tenant')

    # Restaurer colonnes mapping
    op.add_column('vinted_products', sa.Column('vinted_status_id', sa.Integer(), nullable=True), schema='template_tenant')
    op.add_column('vinted_products', sa.Column('vinted_size_id', sa.Integer(), nullable=True), schema='template_tenant')
    op.add_column('vinted_products', sa.Column('vinted_color_ids', sa.String(length=100), nullable=True), schema='template_tenant')
    op.add_column('vinted_products', sa.Column('vinted_brand_id', sa.Integer(), nullable=True), schema='template_tenant')
    op.add_column('vinted_products', sa.Column('vinted_category_id', sa.Integer(), nullable=True), schema='template_tenant')

    # Renommer vinted_id -> vinted_item_id
    op.alter_column('vinted_products', 'vinted_id', new_column_name='vinted_item_id', schema='template_tenant')

    # Restaurer ancien index
    op.create_index('ix_template_tenant_vinted_products_vinted_item_id', 'vinted_products', ['vinted_item_id'], unique=False, schema='template_tenant')
