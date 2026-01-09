"""create ebay schema and tables

Revision ID: 29170a73217f
Revises: f1g2h3i4j5k6
Create Date: 2025-12-10 12:17:30.751099+01:00

Creates:
1. PUBLIC schema tables (shared across all users):
   - marketplace_config: Configuration of 8 eBay marketplaces
   - aspect_mappings: Translated aspect names per marketplace
   - exchange_rate_config: Currency exchange rates (GBP, PLN)

2. Extends PUBLIC.platform_mappings with eBay-specific columns:
   - OAuth credentials (per user)
   - Business policies IDs (per user)
   - Pricing coefficients & fees (per user, per marketplace)
   - Best Offer settings (per user)
   - Promoted Listings settings (per user)

3. TEMPLATE_TENANT schema tables (cloned to each user_{id}):
   - ebay_products_marketplace: Products published per marketplace
   - ebay_promoted_listings: Promoted listings campaigns
   - ebay_orders: eBay orders
   - ebay_orders_products: Order line items

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '29170a73217f'
down_revision: Union[str, None] = 'f1g2h3i4j5k6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ========================================
    # PART 1: PUBLIC SCHEMA TABLES
    # ========================================

    # 1.1 Create marketplace_config table
    op.create_table(
        'marketplace_config',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('marketplace_id', sa.String(length=20), nullable=False),
        sa.Column('country_code', sa.String(length=2), nullable=False),
        sa.Column('site_id', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('marketplace_id', name='uq_marketplace_id'),
        schema='public'
    )
    op.create_index('idx_marketplace_config_marketplace_id', 'marketplace_config', ['marketplace_id'], schema='public')
    op.create_index('idx_marketplace_config_active', 'marketplace_config', ['is_active'], schema='public')

    # 1.2 Create aspect_mappings table
    op.create_table(
        'aspect_mappings',
        sa.Column('aspect_key', sa.String(length=100), nullable=False),
        sa.Column('ebay_gb', sa.String(length=100), nullable=True),
        sa.Column('ebay_fr', sa.String(length=100), nullable=True),
        sa.Column('ebay_de', sa.String(length=100), nullable=True),
        sa.Column('ebay_it', sa.String(length=100), nullable=True),
        sa.Column('ebay_es', sa.String(length=100), nullable=True),
        sa.Column('ebay_nl', sa.String(length=100), nullable=True),
        sa.Column('ebay_be', sa.String(length=100), nullable=True),
        sa.Column('ebay_pl', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('aspect_key'),
        schema='public'
    )
    op.create_index('idx_aspect_mappings_ebay_gb', 'aspect_mappings', ['ebay_gb'], schema='public')

    # 1.3 Create exchange_rate_config table
    op.create_table(
        'exchange_rate_config',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('rate', sa.Numeric(precision=10, scale=6), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False, server_default='ECB'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('currency', name='uq_currency'),
        schema='public'
    )

    # ========================================
    # PART 2: EXTEND PUBLIC.platform_mappings
    # ========================================

    # 2.1 Add eBay OAuth credentials columns
    op.add_column('platform_mappings', sa.Column('ebay_client_id', sa.Text(), nullable=True), schema='public')
    op.add_column('platform_mappings', sa.Column('ebay_client_secret', sa.Text(), nullable=True), schema='public')
    op.add_column('platform_mappings', sa.Column('ebay_refresh_token', sa.Text(), nullable=True), schema='public')
    op.add_column('platform_mappings', sa.Column('ebay_app_id', sa.Text(), nullable=True), schema='public')
    op.add_column('platform_mappings', sa.Column('ebay_dev_id', sa.Text(), nullable=True), schema='public')
    op.add_column('platform_mappings', sa.Column('ebay_cert_id', sa.Text(), nullable=True), schema='public')

    # 2.2 Add eBay Business Policies IDs
    op.add_column('platform_mappings', sa.Column('ebay_payment_policy_id', sa.BigInteger(), nullable=True), schema='public')
    op.add_column('platform_mappings', sa.Column('ebay_fulfillment_policy_id', sa.BigInteger(), nullable=True), schema='public')
    op.add_column('platform_mappings', sa.Column('ebay_return_policy_id', sa.BigInteger(), nullable=True), schema='public')
    op.add_column('platform_mappings', sa.Column('ebay_inventory_location', sa.String(length=100), nullable=True), schema='public')

    # 2.3 Add pricing coefficients per marketplace (8 marketplaces)
    op.add_column('platform_mappings', sa.Column('ebay_price_coefficient_fr', sa.Numeric(precision=5, scale=2), nullable=False, server_default='1.00'), schema='public')
    op.add_column('platform_mappings', sa.Column('ebay_price_coefficient_gb', sa.Numeric(precision=5, scale=2), nullable=False, server_default='1.10'), schema='public')
    op.add_column('platform_mappings', sa.Column('ebay_price_coefficient_de', sa.Numeric(precision=5, scale=2), nullable=False, server_default='1.05'), schema='public')
    op.add_column('platform_mappings', sa.Column('ebay_price_coefficient_it', sa.Numeric(precision=5, scale=2), nullable=False, server_default='1.08'), schema='public')
    op.add_column('platform_mappings', sa.Column('ebay_price_coefficient_es', sa.Numeric(precision=5, scale=2), nullable=False, server_default='1.07'), schema='public')
    op.add_column('platform_mappings', sa.Column('ebay_price_coefficient_nl', sa.Numeric(precision=5, scale=2), nullable=False, server_default='1.06'), schema='public')
    op.add_column('platform_mappings', sa.Column('ebay_price_coefficient_be', sa.Numeric(precision=5, scale=2), nullable=False, server_default='1.06'), schema='public')
    op.add_column('platform_mappings', sa.Column('ebay_price_coefficient_pl', sa.Numeric(precision=5, scale=2), nullable=False, server_default='1.12'), schema='public')

    # 2.4 Add pricing fees per marketplace (8 marketplaces)
    op.add_column('platform_mappings', sa.Column('ebay_price_fee_fr', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00'), schema='public')
    op.add_column('platform_mappings', sa.Column('ebay_price_fee_gb', sa.Numeric(precision=10, scale=2), nullable=False, server_default='5.00'), schema='public')
    op.add_column('platform_mappings', sa.Column('ebay_price_fee_de', sa.Numeric(precision=10, scale=2), nullable=False, server_default='2.00'), schema='public')
    op.add_column('platform_mappings', sa.Column('ebay_price_fee_it', sa.Numeric(precision=10, scale=2), nullable=False, server_default='3.00'), schema='public')
    op.add_column('platform_mappings', sa.Column('ebay_price_fee_es', sa.Numeric(precision=10, scale=2), nullable=False, server_default='2.50'), schema='public')
    op.add_column('platform_mappings', sa.Column('ebay_price_fee_nl', sa.Numeric(precision=10, scale=2), nullable=False, server_default='2.00'), schema='public')
    op.add_column('platform_mappings', sa.Column('ebay_price_fee_be', sa.Numeric(precision=10, scale=2), nullable=False, server_default='2.00'), schema='public')
    op.add_column('platform_mappings', sa.Column('ebay_price_fee_pl', sa.Numeric(precision=10, scale=2), nullable=False, server_default='10.00'), schema='public')

    # 2.5 Add Best Offer settings
    op.add_column('platform_mappings', sa.Column('ebay_best_offer_enabled', sa.Boolean(), nullable=False, server_default='true'), schema='public')
    op.add_column('platform_mappings', sa.Column('ebay_best_offer_auto_accept_pct', sa.Numeric(precision=5, scale=2), nullable=False, server_default='85.00'), schema='public')
    op.add_column('platform_mappings', sa.Column('ebay_best_offer_auto_decline_pct', sa.Numeric(precision=5, scale=2), nullable=False, server_default='70.00'), schema='public')

    # 2.6 Add Promoted Listings settings
    op.add_column('platform_mappings', sa.Column('ebay_promoted_listings_enabled', sa.Boolean(), nullable=False, server_default='false'), schema='public')
    op.add_column('platform_mappings', sa.Column('ebay_promoted_listings_bid_pct', sa.Numeric(precision=5, scale=2), nullable=False, server_default='10.00'), schema='public')

    # ========================================
    # PART 3: TEMPLATE_TENANT SCHEMA TABLES
    # ========================================

    # 3.1 Create ebay_products_marketplace table in template_tenant
    op.create_table(
        'ebay_products_marketplace',
        sa.Column('sku_derived', sa.String(length=50), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('marketplace_id', sa.String(length=20), nullable=False),
        sa.Column('ebay_offer_id', sa.BigInteger(), nullable=True),
        sa.Column('ebay_listing_id', sa.BigInteger(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sold_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('sku_derived'),
        sa.ForeignKeyConstraint(['product_id'], ['template_tenant.products.id'], ondelete='CASCADE'),
        schema='template_tenant'
    )
    op.create_index('idx_ebay_pm_product_id', 'ebay_products_marketplace', ['product_id'], schema='template_tenant')
    op.create_index('idx_ebay_pm_marketplace', 'ebay_products_marketplace', ['marketplace_id'], schema='template_tenant')
    op.create_index('idx_ebay_pm_status', 'ebay_products_marketplace', ['status'], schema='template_tenant')
    op.create_index('idx_ebay_pm_listing_id', 'ebay_products_marketplace', ['ebay_listing_id'], schema='template_tenant')

    # 3.2 Create ebay_promoted_listings table in template_tenant
    op.create_table(
        'ebay_promoted_listings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('campaign_id', sa.String(length=50), nullable=False),
        sa.Column('campaign_name', sa.String(length=255), nullable=True),
        sa.Column('marketplace_id', sa.String(length=20), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('sku_derived', sa.String(length=50), nullable=False),
        sa.Column('ad_id', sa.String(length=50), nullable=False),
        sa.Column('listing_id', sa.String(length=50), nullable=True),
        sa.Column('bid_percentage', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('ad_status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('total_clicks', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_impressions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_sales', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_sales_amount', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0'),
        sa.Column('total_ad_fees', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['product_id'], ['template_tenant.products.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('ad_id', name='uq_ad_id'),
        schema='template_tenant'
    )
    op.create_index('idx_ebay_pl_campaign', 'ebay_promoted_listings', ['campaign_id'], schema='template_tenant')
    op.create_index('idx_ebay_pl_product_id', 'ebay_promoted_listings', ['product_id'], schema='template_tenant')
    op.create_index('idx_ebay_pl_marketplace', 'ebay_promoted_listings', ['marketplace_id'], schema='template_tenant')
    op.create_index('idx_ebay_pl_status', 'ebay_promoted_listings', ['ad_status'], schema='template_tenant')

    # 3.3 Create ebay_orders table in template_tenant
    op.create_table(
        'ebay_orders',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('order_id', sa.Text(), nullable=False),
        sa.Column('marketplace_id', sa.Text(), nullable=True),
        sa.Column('buyer_username', sa.Text(), nullable=True),
        sa.Column('buyer_email', sa.Text(), nullable=True),
        sa.Column('shipping_name', sa.Text(), nullable=True),
        sa.Column('shipping_address', sa.Text(), nullable=True),
        sa.Column('shipping_city', sa.Text(), nullable=True),
        sa.Column('shipping_postal_code', sa.Text(), nullable=True),
        sa.Column('shipping_country', sa.Text(), nullable=True),
        sa.Column('total_price', sa.Float(), nullable=True),
        sa.Column('currency', sa.Text(), nullable=True),
        sa.Column('shipping_cost', sa.Float(), nullable=True),
        sa.Column('order_fulfillment_status', sa.Text(), nullable=True),
        sa.Column('order_payment_status', sa.Text(), nullable=True),
        sa.Column('creation_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('paid_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tracking_number', sa.Text(), nullable=True),
        sa.Column('shipping_carrier', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_id', name='uq_order_id'),
        schema='template_tenant'
    )
    op.create_index('idx_ebay_orders_order_id', 'ebay_orders', ['order_id'], schema='template_tenant')
    op.create_index('idx_ebay_orders_marketplace', 'ebay_orders', ['marketplace_id'], schema='template_tenant')
    op.create_index('idx_ebay_orders_fulfillment_status', 'ebay_orders', ['order_fulfillment_status'], schema='template_tenant')

    # 3.4 Create ebay_orders_products table in template_tenant
    op.create_table(
        'ebay_orders_products',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('order_id', sa.Text(), nullable=False),
        sa.Column('line_item_id', sa.Text(), nullable=True),
        sa.Column('sku', sa.Text(), nullable=True),
        sa.Column('sku_original', sa.Text(), nullable=True),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('unit_price', sa.Float(), nullable=True),
        sa.Column('total_price', sa.Float(), nullable=True),
        sa.Column('currency', sa.Text(), nullable=True),
        sa.Column('legacy_item_id', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['order_id'], ['template_tenant.ebay_orders.order_id'], ondelete='CASCADE'),
        schema='template_tenant'
    )
    op.create_index('idx_ebay_op_order_id', 'ebay_orders_products', ['order_id'], schema='template_tenant')
    op.create_index('idx_ebay_op_sku', 'ebay_orders_products', ['sku'], schema='template_tenant')
    op.create_index('idx_ebay_op_sku_original', 'ebay_orders_products', ['sku_original'], schema='template_tenant')

    # ========================================
    # PART 4: SEED DATA
    # ========================================

    # 4.1 Insert marketplace configurations (8 marketplaces)
    op.execute("""
        INSERT INTO public.marketplace_config (marketplace_id, country_code, site_id, currency, is_active)
        VALUES
            ('EBAY_FR', 'FR', 71, 'EUR', true),
            ('EBAY_GB', 'UK', 3, 'GBP', true),
            ('EBAY_DE', 'DE', 77, 'EUR', true),
            ('EBAY_IT', 'IT', 101, 'EUR', true),
            ('EBAY_ES', 'ES', 186, 'EUR', true),
            ('EBAY_NL', 'NL', 146, 'EUR', true),
            ('EBAY_BE', 'BE', 23, 'EUR', true),
            ('EBAY_PL', 'PL', 212, 'PLN', true)
        ON CONFLICT (marketplace_id) DO NOTHING;
    """)

    # 4.2 Insert aspect mappings (core aspects)
    op.execute("""
        INSERT INTO public.aspect_mappings (aspect_key, ebay_gb, ebay_fr, ebay_de, ebay_it, ebay_es, ebay_nl, ebay_be, ebay_pl)
        VALUES
            ('brand', 'Brand', 'Marque', 'Marke', 'Marca', 'Marca', 'Merk', 'Marque', 'Marka'),
            ('color', 'Colour', 'Couleur', 'Farbe', 'Colore', 'Color', 'Kleur', 'Couleur', 'Kolor'),
            ('size', 'Size', 'Taille', 'Größe', 'Taglia', 'Talla', 'Maat', 'Taille', 'Rozmiar'),
            ('condition', 'Condition', 'État', 'Zustand', 'Condizioni', 'Estado', 'Staat', 'État', 'Stan'),
            ('material', 'Material', 'Matière', 'Material', 'Materiale', 'Material', 'Materiaal', 'Matière', 'Materiał'),
            ('style', 'Style', 'Style', 'Stil', 'Stile', 'Estilo', 'Stijl', 'Style', 'Styl'),
            ('season', 'Season', 'Saison', 'Jahreszeit', 'Stagione', 'Temporada', 'Seizoen', 'Saison', 'Sezon'),
            ('gender', 'Department', 'Rayon', 'Abteilung', 'Reparto', 'Departamento', 'Afdeling', 'Rayon', 'Dział'),
            ('sleeve_length', 'Sleeve Length', 'Longueur des manches', 'Ärmellänge', 'Lunghezza maniche', 'Largo de manga', 'Mouwlengte', 'Longueur des manches', 'Długość rękawa'),
            ('fit', 'Fit', 'Coupe', 'Passform', 'Vestibilità', 'Ajuste', 'Pasvorm', 'Coupe', 'Krój'),
            ('closure', 'Closure Type', 'Type de fermeture', 'Verschlussart', 'Tipo di chiusura', 'Tipo de cierre', 'Sluitingstype', 'Type de fermeture', 'Typ zapięcia'),
            ('rise', 'Rise', 'Taille (hauteur)', 'Leibhöhe', 'Altezza vita', 'Altura de cintura', 'Taillehoogte', 'Taille (hauteur)', 'Wysokość talii'),
            ('vintage', 'Vintage', 'Vintage', 'Vintage', 'Vintage', 'Vintage', 'Vintage', 'Vintage', 'Vintage'),
            ('decade', 'Decade', 'Décennie', 'Jahrzehnt', 'Decennio', 'Década', 'Decennium', 'Décennie', 'Dekada'),
            ('country', 'Country/Region of Manufacture', 'Pays de fabrication', 'Herstellungsland/-region', 'Paese di fabbricazione', 'País/región de fabricación', 'Land/regio van vervaardiging', 'Pays de fabrication', 'Kraj/region produkcji'),
            ('pattern', 'Pattern', 'Motif', 'Muster', 'Fantasia', 'Patrón', 'Patroon', 'Motif', 'Wzór'),
            ('features', 'Features', 'Caractéristiques', 'Besonderheiten', 'Caratteristiche', 'Características', 'Kenmerken', 'Caractéristiques', 'Cechy')
        ON CONFLICT (aspect_key) DO NOTHING;
    """)

    # 4.3 Insert exchange rates (default values)
    op.execute("""
        INSERT INTO public.exchange_rate_config (currency, rate, source)
        VALUES
            ('GBP', 0.856000, 'ECB'),
            ('PLN', 4.320000, 'ECB')
        ON CONFLICT (currency) DO NOTHING;
    """)


def downgrade() -> None:
    # Drop template_tenant tables
    op.drop_table('ebay_orders_products', schema='template_tenant')
    op.drop_table('ebay_orders', schema='template_tenant')
    op.drop_table('ebay_promoted_listings', schema='template_tenant')
    op.drop_table('ebay_products_marketplace', schema='template_tenant')

    # Remove columns from platform_mappings
    op.drop_column('platform_mappings', 'ebay_promoted_listings_bid_pct', schema='public')
    op.drop_column('platform_mappings', 'ebay_promoted_listings_enabled', schema='public')
    op.drop_column('platform_mappings', 'ebay_best_offer_auto_decline_pct', schema='public')
    op.drop_column('platform_mappings', 'ebay_best_offer_auto_accept_pct', schema='public')
    op.drop_column('platform_mappings', 'ebay_best_offer_enabled', schema='public')
    op.drop_column('platform_mappings', 'ebay_price_fee_pl', schema='public')
    op.drop_column('platform_mappings', 'ebay_price_fee_be', schema='public')
    op.drop_column('platform_mappings', 'ebay_price_fee_nl', schema='public')
    op.drop_column('platform_mappings', 'ebay_price_fee_es', schema='public')
    op.drop_column('platform_mappings', 'ebay_price_fee_it', schema='public')
    op.drop_column('platform_mappings', 'ebay_price_fee_de', schema='public')
    op.drop_column('platform_mappings', 'ebay_price_fee_gb', schema='public')
    op.drop_column('platform_mappings', 'ebay_price_fee_fr', schema='public')
    op.drop_column('platform_mappings', 'ebay_price_coefficient_pl', schema='public')
    op.drop_column('platform_mappings', 'ebay_price_coefficient_be', schema='public')
    op.drop_column('platform_mappings', 'ebay_price_coefficient_nl', schema='public')
    op.drop_column('platform_mappings', 'ebay_price_coefficient_es', schema='public')
    op.drop_column('platform_mappings', 'ebay_price_coefficient_it', schema='public')
    op.drop_column('platform_mappings', 'ebay_price_coefficient_de', schema='public')
    op.drop_column('platform_mappings', 'ebay_price_coefficient_gb', schema='public')
    op.drop_column('platform_mappings', 'ebay_price_coefficient_fr', schema='public')
    op.drop_column('platform_mappings', 'ebay_inventory_location', schema='public')
    op.drop_column('platform_mappings', 'ebay_return_policy_id', schema='public')
    op.drop_column('platform_mappings', 'ebay_fulfillment_policy_id', schema='public')
    op.drop_column('platform_mappings', 'ebay_payment_policy_id', schema='public')
    op.drop_column('platform_mappings', 'ebay_cert_id', schema='public')
    op.drop_column('platform_mappings', 'ebay_dev_id', schema='public')
    op.drop_column('platform_mappings', 'ebay_app_id', schema='public')
    op.drop_column('platform_mappings', 'ebay_refresh_token', schema='public')
    op.drop_column('platform_mappings', 'ebay_client_secret', schema='public')
    op.drop_column('platform_mappings', 'ebay_client_id', schema='public')

    # Drop public tables
    op.drop_table('exchange_rate_config', schema='public')
    op.drop_table('aspect_mappings', schema='public')
    op.drop_table('marketplace_config', schema='public')
