"""Initial Schema Complete - Squashed Migration

This is a consolidated migration that represents the complete database schema.
It combines 104 individual migrations into a single, comprehensive migration.

Revision ID: 20260105_0001
Revises: None
Create Date: 2026-01-05

Schemas created:
- public: Users, subscriptions, shared config
- product_attributes: Brands, categories, colors, etc. (20 tables)
- ebay: eBay marketplace configuration
- vinted: Vinted categories, mappings, orders
- template_tenant: Template for user schemas (cloned for each user_X)

Author: Claude (Squashed from 104 migrations)
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

# Revision identifiers
revision: str = '20260105_0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def schema_exists(connection, schema_name: str) -> bool:
    """Check if a schema exists."""
    result = connection.execute(text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = :schema)"
    ), {"schema": schema_name})
    return result.scalar()


def table_exists(connection, schema: str, table: str) -> bool:
    """Check if a table exists in a specific schema."""
    result = connection.execute(text(
        "SELECT EXISTS ("
        "  SELECT 1 FROM information_schema.tables "
        "  WHERE table_schema = :schema AND table_name = :table"
        ")"
    ), {"schema": schema, "table": table})
    return result.scalar()


def enum_exists(connection, enum_name: str) -> bool:
    """Check if an ENUM type exists."""
    result = connection.execute(text(
        "SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = :name)"
    ), {"name": enum_name})
    return result.scalar()


def upgrade() -> None:
    """Create the complete database schema."""
    connection = op.get_bind()

    print("\n" + "=" * 70)
    print("SQUASHED MIGRATION: Creating complete StoFlow schema")
    print("=" * 70)

    # =========================================================================
    # PART 1: CREATE ENUMS
    # =========================================================================
    print("\n[1/9] Creating ENUMs...")

    enums = [
        ("user_role", "('ADMIN', 'USER', 'SUPPORT')"),
        ("subscription_tier", "('FREE', 'STARTER', 'PRO', 'ENTERPRISE')"),
        ("platform_type", "('VINTED', 'EBAY', 'ETSY')"),
        ("product_status", "('DRAFT', 'PENDING_REVIEW', 'APPROVED', 'REJECTED', 'SCHEDULED', 'PUBLISHED', 'SUSPENDED', 'FLAGGED', 'SOLD', 'ARCHIVED')"),
        ("publication_status", "('PENDING', 'SUCCESS', 'FAILED')"),
        ("account_type", "('individual', 'professional')"),
        ("business_type", "('resale', 'dropshipping', 'artisan', 'retail', 'other')"),
        ("estimated_products", "('0-50', '50-200', '200-500', '500+')"),
        ("gender", "('male', 'female', 'unisex')"),
        ("taskstatus", "('pending', 'processing', 'success', 'failed', 'timeout', 'cancelled')"),
        ("jobstatus", "('pending', 'running', 'paused', 'completed', 'failed', 'cancelled', 'expired')"),
        ("datadomestatus", "('UNKNOWN', 'VALID', 'EXPIRED', 'BLOCKED', 'CAPTCHA_REQUIRED')"),
    ]

    for enum_name, enum_values in enums:
        if not enum_exists(connection, enum_name):
            connection.execute(text(f"CREATE TYPE {enum_name} AS ENUM {enum_values}"))
            print(f"  + Created ENUM: {enum_name}")
        else:
            print(f"  - ENUM exists: {enum_name}")

    print("  Done.")

    # =========================================================================
    # PART 2: CREATE SCHEMAS
    # =========================================================================
    print("\n[2/9] Creating schemas...")

    schemas = ['product_attributes', 'ebay', 'vinted', 'template_tenant']
    for schema in schemas:
        connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        print(f"  + Schema: {schema}")

    print("  Done.")

    # =========================================================================
    # PART 3: PUBLIC SCHEMA TABLES
    # =========================================================================
    print("\n[3/9] Creating public schema tables...")

    # 3.1 subscription_quotas
    if not table_exists(connection, 'public', 'subscription_quotas'):
        op.create_table(
            'subscription_quotas',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('tier', postgresql.ENUM('FREE', 'STARTER', 'PRO', 'ENTERPRISE', name='subscription_tier', create_type=False), nullable=False),
            sa.Column('max_products', sa.Integer(), nullable=False),
            sa.Column('max_platforms', sa.Integer(), nullable=False),
            sa.Column('ai_credits_monthly', sa.Integer(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('tier', name='uq_subscription_quotas_tier'),
            schema='public'
        )
        print("  + subscription_quotas")

    # 3.2 users
    if not table_exists(connection, 'public', 'users'):
        op.create_table(
            'users',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('email', sa.String(255), nullable=False),
            sa.Column('hashed_password', sa.String(255), nullable=False),
            sa.Column('full_name', sa.String(255), nullable=False),
            sa.Column('role', postgresql.ENUM('ADMIN', 'USER', 'SUPPORT', name='user_role', create_type=False), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
            sa.Column('subscription_tier', postgresql.ENUM('FREE', 'STARTER', 'PRO', 'ENTERPRISE', name='subscription_tier', create_type=False), nullable=False, server_default='FREE'),
            sa.Column('subscription_status', sa.String(50), nullable=False, server_default='active'),
            sa.Column('subscription_tier_id', sa.Integer(), nullable=True),
            sa.Column('business_name', sa.String(255), nullable=True),
            sa.Column('account_type', postgresql.ENUM('individual', 'professional', name='account_type', create_type=False), nullable=False, server_default='individual'),
            sa.Column('business_type', postgresql.ENUM('resale', 'dropshipping', 'artisan', 'retail', 'other', name='business_type', create_type=False), nullable=True),
            sa.Column('estimated_products', postgresql.ENUM('0-50', '50-200', '200-500', '500+', name='estimated_products', create_type=False), nullable=True),
            sa.Column('siret', sa.String(14), nullable=True),
            sa.Column('vat_number', sa.String(20), nullable=True),
            sa.Column('phone', sa.String(20), nullable=True),
            sa.Column('country', sa.String(2), nullable=False, server_default='FR'),
            sa.Column('language', sa.String(2), nullable=False, server_default='fr'),
            sa.Column('stripe_customer_id', sa.String(255), nullable=True),
            sa.Column('stripe_subscription_id', sa.String(255), nullable=True),
            sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
            sa.Column('password_changed_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('email_verification_token', sa.String(255), nullable=True),
            sa.Column('email_verification_sent_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['subscription_tier_id'], ['subscription_quotas.id'], name='fk_users_subscription_tier_id'),
            sa.PrimaryKeyConstraint('id'),
            schema='public'
        )
        op.create_index('ix_public_users_email', 'users', ['email'], unique=True, schema='public')
        print("  + users")

    # 3.3 ai_credits
    if not table_exists(connection, 'public', 'ai_credits'):
        op.create_table(
            'ai_credits',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('credits_remaining', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('credits_used_this_month', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('last_reset_date', sa.Date(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_id'),
            schema='public'
        )
        print("  + ai_credits")

    # 3.4 clothing_prices
    if not table_exists(connection, 'public', 'clothing_prices'):
        op.create_table(
            'clothing_prices',
            sa.Column('brand', sa.String(100), nullable=False),
            sa.Column('category', sa.String(255), nullable=False),
            sa.Column('base_price', sa.Numeric(10, 2), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('brand', 'category'),
            sa.CheckConstraint('base_price >= 0', name='check_base_price_positive'),
            schema='public'
        )
        print("  + clothing_prices")

    # 3.5 permissions
    if not table_exists(connection, 'public', 'permissions'):
        op.create_table(
            'permissions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(100), nullable=False),
            sa.Column('code', sa.String(100), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('category', sa.String(50), nullable=False, server_default='general'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('code'),
            schema='public'
        )
        print("  + permissions")

    # 3.6 role_permissions
    if not table_exists(connection, 'public', 'role_permissions'):
        op.create_table(
            'role_permissions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('role', postgresql.ENUM('ADMIN', 'USER', 'SUPPORT', name='user_role', create_type=False), nullable=False),
            sa.Column('permission_id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('role', 'permission_id', name='uq_role_permission'),
            schema='public'
        )
        print("  + role_permissions")

    # 3.7 admin_audit_logs
    if not table_exists(connection, 'public', 'admin_audit_logs'):
        op.create_table(
            'admin_audit_logs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('admin_id', sa.Integer(), nullable=False),
            sa.Column('action', sa.String(100), nullable=False),
            sa.Column('resource_type', sa.String(50), nullable=False),
            sa.Column('resource_id', sa.String(100), nullable=True),
            sa.Column('details', postgresql.JSONB(), nullable=True),
            sa.Column('ip_address', sa.String(45), nullable=True),
            sa.Column('user_agent', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['admin_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            schema='public'
        )
        op.create_index('ix_public_admin_audit_logs_action', 'admin_audit_logs', ['action'], schema='public')
        op.create_index('ix_public_admin_audit_logs_admin_id', 'admin_audit_logs', ['admin_id'], schema='public')
        op.create_index('ix_public_admin_audit_logs_resource_type', 'admin_audit_logs', ['resource_type'], schema='public')
        print("  + admin_audit_logs")

    # 3.8 doc_categories
    if not table_exists(connection, 'public', 'doc_categories'):
        op.create_table(
            'doc_categories',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('slug', sa.String(100), nullable=False),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('icon', sa.String(50), nullable=True),
            sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('slug'),
            schema='public'
        )
        print("  + doc_categories")

    # 3.9 doc_articles
    if not table_exists(connection, 'public', 'doc_articles'):
        op.create_table(
            'doc_articles',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('category_id', sa.Integer(), nullable=False),
            sa.Column('slug', sa.String(100), nullable=False),
            sa.Column('title', sa.String(255), nullable=False),
            sa.Column('summary', sa.Text(), nullable=True),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['category_id'], ['doc_categories.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('slug'),
            schema='public'
        )
        print("  + doc_articles")

    print("  Done.")

    # =========================================================================
    # PART 4: PRODUCT_ATTRIBUTES SCHEMA TABLES
    # =========================================================================
    print("\n[4/9] Creating product_attributes tables...")

    # Define all attribute tables with their specific columns
    attribute_tables = [
        ('brands', [
            sa.Column('name', sa.String(100), nullable=False),
            sa.Column('name_fr', sa.String(100), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('vinted_id', sa.Text(), nullable=True),
            sa.Column('monitoring', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('sector_jeans', sa.String(20), nullable=True),
            sa.Column('sector_jacket', sa.String(20), nullable=True),
        ], 'name'),
        ('categories', [
            sa.Column('name_en', sa.String(100), nullable=False),
            sa.Column('parent_category', sa.String(100), nullable=True),
            sa.Column('name_fr', sa.String(255), nullable=True),
            sa.Column('name_de', sa.String(255), nullable=True),
            sa.Column('name_it', sa.String(255), nullable=True),
            sa.Column('name_es', sa.String(255), nullable=True),
            sa.Column('name_nl', sa.String(255), nullable=True),
            sa.Column('name_pl', sa.String(255), nullable=True),
            sa.Column('genders', postgresql.ARRAY(sa.String(20)), nullable=True),
        ], 'name_en'),
        ('colors', [
            sa.Column('name_en', sa.String(100), nullable=False),
            sa.Column('name_fr', sa.String(100), nullable=True),
            sa.Column('name_de', sa.String(100), nullable=True),
            sa.Column('name_it', sa.String(100), nullable=True),
            sa.Column('name_es', sa.String(100), nullable=True),
            sa.Column('name_nl', sa.String(100), nullable=True),
            sa.Column('name_pl', sa.String(100), nullable=True),
            sa.Column('hex_code', sa.String(7), nullable=True),
        ], 'name_en'),
        ('conditions', [
            sa.Column('note', sa.Integer(), nullable=False),
            sa.Column('name_en', sa.String(100), nullable=False),
            sa.Column('name_fr', sa.String(100), nullable=True),
            sa.Column('name_de', sa.String(100), nullable=True),
            sa.Column('name_it', sa.String(100), nullable=True),
            sa.Column('name_es', sa.String(100), nullable=True),
            sa.Column('name_nl', sa.String(100), nullable=True),
            sa.Column('name_pl', sa.String(100), nullable=True),
            sa.Column('vinted_id', sa.Integer(), nullable=True),
            sa.Column('ebay_condition', sa.String(50), nullable=True),
            sa.Column('etsy_condition', sa.String(50), nullable=True),
        ], 'note'),
    ]

    # Simple multilingual attribute tables
    simple_attrs = [
        'closures', 'decades', 'fits', 'lengths', 'materials', 'necklines',
        'origins', 'patterns', 'rises', 'seasons', 'sleeve_lengths', 'sports', 'trends'
    ]

    for table_name in simple_attrs:
        if not table_exists(connection, 'product_attributes', table_name):
            columns = [
                sa.Column('name_en', sa.String(100), nullable=False),
                sa.Column('name_fr', sa.String(100), nullable=True),
                sa.Column('name_de', sa.String(100), nullable=True),
                sa.Column('name_it', sa.String(100), nullable=True),
                sa.Column('name_es', sa.String(100), nullable=True),
                sa.Column('name_nl', sa.String(100), nullable=True),
                sa.Column('name_pl', sa.String(100), nullable=True),
            ]
            op.create_table(
                table_name,
                *columns,
                sa.PrimaryKeyConstraint('name_en'),
                schema='product_attributes'
            )
            op.create_index(f'ix_product_attributes_{table_name}_name_en', table_name, ['name_en'], schema='product_attributes')
            print(f"  + {table_name}")

    # Create special tables
    for table_name, columns, pk_column in attribute_tables:
        if not table_exists(connection, 'product_attributes', table_name):
            op.create_table(
                table_name,
                *columns,
                sa.PrimaryKeyConstraint(pk_column),
                schema='product_attributes'
            )
            print(f"  + {table_name}")

    # Add FK for categories parent
    if table_exists(connection, 'product_attributes', 'categories'):
        try:
            connection.execute(text("""
                ALTER TABLE product_attributes.categories
                ADD CONSTRAINT fk_categories_parent
                FOREIGN KEY (parent_category) REFERENCES product_attributes.categories(name_en)
                ON UPDATE CASCADE ON DELETE SET NULL
            """))
        except Exception:
            pass  # FK might already exist

    # Sizes table with marketplace IDs
    if not table_exists(connection, 'product_attributes', 'sizes'):
        op.create_table(
            'sizes',
            sa.Column('name_en', sa.String(100), nullable=False),
            sa.Column('name_fr', sa.String(100), nullable=True),
            sa.Column('name_de', sa.String(100), nullable=True),
            sa.Column('name_it', sa.String(100), nullable=True),
            sa.Column('name_es', sa.String(100), nullable=True),
            sa.Column('name_nl', sa.String(100), nullable=True),
            sa.Column('name_pl', sa.String(100), nullable=True),
            sa.Column('vinted_id', sa.Integer(), nullable=True),
            sa.Column('ebay_size', sa.String(50), nullable=True),
            sa.Column('etsy_size', sa.String(50), nullable=True),
            sa.PrimaryKeyConstraint('name_en'),
            schema='product_attributes'
        )
        print("  + sizes")

    # Genders table
    if not table_exists(connection, 'product_attributes', 'genders'):
        op.create_table(
            'genders',
            sa.Column('name_en', sa.String(100), nullable=False),
            sa.Column('name_fr', sa.String(100), nullable=True),
            sa.Column('name_de', sa.String(100), nullable=True),
            sa.Column('name_it', sa.String(100), nullable=True),
            sa.Column('name_es', sa.String(100), nullable=True),
            sa.Column('name_nl', sa.String(100), nullable=True),
            sa.Column('name_pl', sa.String(100), nullable=True),
            sa.Column('vinted_id', sa.Integer(), nullable=True),
            sa.Column('ebay_gender', sa.String(50), nullable=True),
            sa.Column('etsy_gender', sa.String(50), nullable=True),
            sa.PrimaryKeyConstraint('name_en'),
            schema='product_attributes'
        )
        print("  + genders")

    # Materials table with vinted_id
    if table_exists(connection, 'product_attributes', 'materials'):
        try:
            connection.execute(text("ALTER TABLE product_attributes.materials ADD COLUMN IF NOT EXISTS vinted_id INTEGER"))
        except Exception:
            pass

    # condition_sups table
    if not table_exists(connection, 'product_attributes', 'condition_sups'):
        op.create_table(
            'condition_sups',
            sa.Column('name_en', sa.String(255), nullable=False),
            sa.Column('name_fr', sa.String(255), nullable=True),
            sa.Column('name_de', sa.String(255), nullable=True),
            sa.Column('name_it', sa.String(255), nullable=True),
            sa.Column('name_es', sa.String(255), nullable=True),
            sa.Column('name_nl', sa.String(255), nullable=True),
            sa.Column('name_pl', sa.String(255), nullable=True),
            sa.PrimaryKeyConstraint('name_en'),
            schema='product_attributes'
        )
        print("  + condition_sups")

    # unique_features table
    if not table_exists(connection, 'product_attributes', 'unique_features'):
        op.create_table(
            'unique_features',
            sa.Column('name_en', sa.String(255), nullable=False),
            sa.Column('name_fr', sa.String(255), nullable=True),
            sa.Column('name_de', sa.String(255), nullable=True),
            sa.Column('name_it', sa.String(255), nullable=True),
            sa.Column('name_es', sa.String(255), nullable=True),
            sa.Column('name_nl', sa.String(255), nullable=True),
            sa.Column('name_pl', sa.String(255), nullable=True),
            sa.PrimaryKeyConstraint('name_en'),
            schema='product_attributes'
        )
        print("  + unique_features")

    print("  Done.")

    # =========================================================================
    # PART 5: EBAY SCHEMA TABLES
    # =========================================================================
    print("\n[5/9] Creating ebay schema tables...")

    if not table_exists(connection, 'ebay', 'marketplace_config'):
        op.create_table(
            'marketplace_config',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('marketplace_id', sa.String(20), nullable=False),
            sa.Column('site_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(100), nullable=False),
            sa.Column('currency', sa.String(3), nullable=False),
            sa.Column('language', sa.String(5), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('marketplace_id'),
            schema='ebay'
        )
        print("  + marketplace_config")

    if not table_exists(connection, 'ebay', 'aspect_name_mapping'):
        op.create_table(
            'aspect_name_mapping',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('aspect_key', sa.String(50), nullable=False),
            sa.Column('ebay_fr', sa.String(100), nullable=True),
            sa.Column('ebay_gb', sa.String(100), nullable=True),
            sa.Column('ebay_de', sa.String(100), nullable=True),
            sa.Column('ebay_it', sa.String(100), nullable=True),
            sa.Column('ebay_es', sa.String(100), nullable=True),
            sa.Column('ebay_nl', sa.String(100), nullable=True),
            sa.Column('ebay_be', sa.String(100), nullable=True),
            sa.Column('ebay_pl', sa.String(100), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('aspect_key'),
            schema='ebay'
        )
        print("  + aspect_name_mapping")

    if not table_exists(connection, 'ebay', 'exchange_rate'):
        op.create_table(
            'exchange_rate',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('currency', sa.String(3), nullable=False),
            sa.Column('rate_to_eur', sa.Numeric(10, 6), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('currency'),
            schema='ebay'
        )
        print("  + exchange_rate")

    if not table_exists(connection, 'ebay', 'category_mapping'):
        op.create_table(
            'category_mapping',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('my_category', sa.String(100), nullable=False),
            sa.Column('my_gender', sa.String(20), nullable=True),
            sa.Column('ebay_category_id', sa.String(20), nullable=False),
            sa.Column('ebay_category_name', sa.String(255), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            schema='ebay'
        )
        op.create_index('idx_ebay_category_lookup', 'category_mapping', ['my_category', 'my_gender'], schema='ebay')
        print("  + category_mapping")

    print("  Done.")

    # =========================================================================
    # PART 6: VINTED SCHEMA TABLES
    # =========================================================================
    print("\n[6/9] Creating vinted schema tables...")

    # vinted_action_types
    if not table_exists(connection, 'vinted', 'action_types'):
        op.create_table(
            'action_types',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('code', sa.String(50), nullable=False),
            sa.Column('name', sa.String(100), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('priority', sa.Integer(), nullable=False, server_default='3'),
            sa.Column('is_batch', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('rate_limit_ms', sa.Integer(), nullable=False, server_default='2000'),
            sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'),
            sa.Column('timeout_seconds', sa.Integer(), nullable=False, server_default='60'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('code'),
            schema='vinted'
        )
        print("  + action_types")

    # vinted_categories
    if not table_exists(connection, 'vinted', 'categories'):
        op.create_table(
            'categories',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('parent_id', sa.Integer(), nullable=True),
            sa.Column('title', sa.String(255), nullable=False),
            sa.Column('title_fr', sa.String(255), nullable=True),
            sa.Column('code', sa.String(100), nullable=True),
            sa.Column('url', sa.String(500), nullable=True),
            sa.Column('gender', sa.String(20), nullable=True),
            sa.Column('is_leaf', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['parent_id'], ['vinted.categories.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
            schema='vinted'
        )
        print("  + categories")

    # vinted_mapping
    if not table_exists(connection, 'vinted', 'mapping'):
        op.create_table(
            'mapping',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('vinted_id', sa.Integer(), nullable=False),
            sa.Column('my_category', sa.String(100), nullable=False),
            sa.Column('my_gender', sa.String(20), nullable=True),
            sa.Column('my_fit', sa.String(100), nullable=True),
            sa.Column('my_length', sa.String(100), nullable=True),
            sa.Column('my_rise', sa.String(100), nullable=True),
            sa.Column('my_material', sa.String(100), nullable=True),
            sa.Column('my_pattern', sa.String(100), nullable=True),
            sa.Column('my_neckline', sa.String(100), nullable=True),
            sa.Column('my_sleeve_length', sa.String(100), nullable=True),
            sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['vinted_id'], ['vinted.categories.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['my_category'], ['product_attributes.categories.name_en'], onupdate='CASCADE'),
            sa.ForeignKeyConstraint(['my_gender'], ['product_attributes.genders.name_en'], onupdate='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            schema='vinted'
        )
        op.create_index('idx_vinted_mapping_vinted', 'mapping', ['vinted_id'], schema='vinted')
        op.create_index('idx_vinted_mapping_my', 'mapping', ['my_category', 'my_gender'], schema='vinted')
        op.create_index('idx_vinted_mapping_default', 'mapping', ['my_category', 'my_gender', 'is_default'], schema='vinted')
        print("  + mapping")

    # vinted_orders
    if not table_exists(connection, 'vinted', 'orders'):
        op.create_table(
            'orders',
            sa.Column('transaction_id', sa.BigInteger(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('item_id', sa.BigInteger(), nullable=True),
            sa.Column('item_name', sa.String(500), nullable=True),
            sa.Column('buyer_id', sa.BigInteger(), nullable=True),
            sa.Column('buyer_name', sa.String(255), nullable=True),
            sa.Column('price_in_eur', sa.Numeric(10, 2), nullable=True),
            sa.Column('shipping_price_eur', sa.Numeric(10, 2), nullable=True),
            sa.Column('status', sa.String(50), nullable=True),
            sa.Column('status_message', sa.String(255), nullable=True),
            sa.Column('created_at_vinted', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('transaction_id'),
            schema='vinted'
        )
        op.create_index('idx_orders_buyer_id', 'orders', ['buyer_id'], schema='vinted')
        op.create_index('idx_orders_status', 'orders', ['status'], schema='vinted')
        print("  + orders")

    # vinted_order_products
    if not table_exists(connection, 'vinted', 'order_products'):
        op.create_table(
            'order_products',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('transaction_id', sa.BigInteger(), nullable=False),
            sa.Column('product_id', sa.Integer(), nullable=True),
            sa.Column('vinted_item_id', sa.BigInteger(), nullable=True),
            sa.Column('sku', sa.String(100), nullable=True),
            sa.Column('title', sa.String(500), nullable=True),
            sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('unit_price_eur', sa.Numeric(10, 2), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['transaction_id'], ['vinted.orders.transaction_id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            schema='vinted'
        )
        print("  + order_products")

    # vinted_deletions
    if not table_exists(connection, 'vinted', 'deletions'):
        op.create_table(
            'deletions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('id_site', sa.Integer(), nullable=True),
            sa.Column('id_vinted', sa.BigInteger(), nullable=True),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('date_deleted', sa.Date(), nullable=True),
            sa.Column('days_active', sa.Integer(), nullable=True),
            sa.Column('price', sa.Numeric(10, 2), nullable=True),
            sa.Column('brand', sa.String(100), nullable=True),
            sa.Column('category', sa.String(100), nullable=True),
            sa.Column('deletion_reason', sa.String(255), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            schema='vinted'
        )
        op.create_index('idx_deletions_id_site', 'deletions', ['id_site'], schema='vinted')
        op.create_index('idx_deletions_id_vinted', 'deletions', ['id_vinted'], schema='vinted')
        op.create_index('idx_deletions_date_deleted', 'deletions', ['date_deleted'], schema='vinted')
        print("  + deletions")

    print("  Done.")

    # =========================================================================
    # PART 7: TEMPLATE_TENANT SCHEMA TABLES
    # =========================================================================
    print("\n[7/9] Creating template_tenant tables...")

    # products
    if not table_exists(connection, 'template_tenant', 'products'):
        op.create_table(
            'products',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(500), nullable=False),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('price', sa.Numeric(10, 2), nullable=False),
            sa.Column('category', sa.String(255), nullable=True),
            sa.Column('brand', sa.String(100), nullable=True),
            sa.Column('condition', sa.String(100), nullable=True),
            sa.Column('size_normalized', sa.String(100), nullable=True),
            sa.Column('size_original', sa.String(100), nullable=True),
            sa.Column('color', sa.String(100), nullable=True),
            sa.Column('material', sa.String(100), nullable=True),
            sa.Column('fit', sa.String(100), nullable=True),
            sa.Column('gender', sa.String(100), nullable=True),
            sa.Column('season', sa.String(100), nullable=True),
            sa.Column('neckline', sa.String(100), nullable=True),
            sa.Column('pattern', sa.String(100), nullable=True),
            sa.Column('sport', sa.String(100), nullable=True),
            sa.Column('length', sa.String(100), nullable=True),
            sa.Column('rise', sa.String(100), nullable=True),
            sa.Column('closure', sa.String(100), nullable=True),
            sa.Column('sleeve_length', sa.String(100), nullable=True),
            sa.Column('origin', sa.String(100), nullable=True),
            sa.Column('decade', sa.String(100), nullable=True),
            sa.Column('trend', sa.String(100), nullable=True),
            sa.Column('condition_sup', postgresql.JSONB(), nullable=True),
            sa.Column('unique_feature', postgresql.JSONB(), nullable=True),
            sa.Column('location', sa.String(100), nullable=True),
            sa.Column('model', sa.String(100), nullable=True),
            sa.Column('marking', sa.Text(), nullable=True),
            sa.Column('pricing_edit', sa.String(100), nullable=True),
            sa.Column('pricing_rarity', sa.String(100), nullable=True),
            sa.Column('pricing_quality', sa.String(100), nullable=True),
            sa.Column('pricing_details', sa.String(100), nullable=True),
            sa.Column('pricing_style', sa.String(100), nullable=True),
            sa.Column('dim1', sa.Integer(), nullable=True),
            sa.Column('dim2', sa.Integer(), nullable=True),
            sa.Column('dim3', sa.Integer(), nullable=True),
            sa.Column('dim4', sa.Integer(), nullable=True),
            sa.Column('dim5', sa.Integer(), nullable=True),
            sa.Column('stock_quantity', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('images', postgresql.JSONB(), nullable=True, server_default='[]'),
            sa.Column('status', postgresql.ENUM('DRAFT', 'PENDING_REVIEW', 'APPROVED', 'REJECTED', 'SCHEDULED', 'PUBLISHED', 'SUSPENDED', 'FLAGGED', 'SOLD', 'ARCHIVED', name='product_status', create_type=False), nullable=False, server_default='DRAFT'),
            sa.Column('sold_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.CheckConstraint('stock_quantity >= 0', name='check_stock_positive'),
            schema='template_tenant'
        )
        op.create_index('ix_template_tenant_products_id', 'products', ['id'], schema='template_tenant')
        op.create_index('ix_template_tenant_products_status', 'products', ['status'], schema='template_tenant')
        print("  + products")

    # vinted_products
    if not table_exists(connection, 'template_tenant', 'vinted_products'):
        op.create_table(
            'vinted_products',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('product_id', sa.Integer(), nullable=False),
            sa.Column('vinted_id', sa.BigInteger(), nullable=True),
            sa.Column('url', sa.String(500), nullable=True),
            sa.Column('status', sa.String(50), nullable=True),
            sa.Column('date', sa.DateTime(timezone=True), nullable=True),
            sa.Column('title', sa.String(500), nullable=True),
            sa.Column('price', sa.Numeric(10, 2), nullable=True),
            sa.Column('view_count', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('favourite_count', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('vinted_category_id', sa.Integer(), nullable=True),
            sa.Column('vinted_brand_id', sa.Integer(), nullable=True),
            sa.Column('vinted_color_ids', sa.String(100), nullable=True),
            sa.Column('vinted_size_id', sa.Integer(), nullable=True),
            sa.Column('vinted_status_id', sa.Integer(), nullable=True),
            sa.Column('brand', sa.String(100), nullable=True),
            sa.Column('size', sa.String(50), nullable=True),
            sa.Column('image_ids', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['product_id'], ['template_tenant.products.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('product_id'),
            sa.UniqueConstraint('vinted_id'),
            schema='template_tenant'
        )
        op.create_index('ix_template_tenant_vinted_products_status', 'vinted_products', ['status'], schema='template_tenant')
        print("  + vinted_products")

    # publication_history
    if not table_exists(connection, 'template_tenant', 'publication_history'):
        op.create_table(
            'publication_history',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('product_id', sa.Integer(), nullable=False),
            sa.Column('platform', postgresql.ENUM('VINTED', 'EBAY', 'ETSY', name='platform_type', create_type=False), nullable=False),
            sa.Column('status', postgresql.ENUM('PENDING', 'SUCCESS', 'FAILED', name='publication_status', create_type=False), nullable=False),
            sa.Column('platform_product_id', sa.String(100), nullable=True),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('metadata', postgresql.JSONB(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['product_id'], ['template_tenant.products.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            schema='template_tenant'
        )
        print("  + publication_history")

    # ai_generation_logs
    if not table_exists(connection, 'template_tenant', 'ai_generation_logs'):
        op.create_table(
            'ai_generation_logs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('product_id', sa.Integer(), nullable=False),
            sa.Column('model', sa.String(100), nullable=False),
            sa.Column('prompt_tokens', sa.Integer(), nullable=False),
            sa.Column('completion_tokens', sa.Integer(), nullable=False),
            sa.Column('total_tokens', sa.Integer(), nullable=False),
            sa.Column('total_cost', sa.Numeric(10, 6), nullable=False),
            sa.Column('cached', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('generation_time_ms', sa.Integer(), nullable=False),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['product_id'], ['template_tenant.products.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            schema='template_tenant'
        )
        print("  + ai_generation_logs")

    # vinted_connection
    if not table_exists(connection, 'template_tenant', 'vinted_connection'):
        op.create_table(
            'vinted_connection',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('is_connected', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('vinted_user_id', sa.BigInteger(), nullable=True),
            sa.Column('username', sa.String(255), nullable=True),
            sa.Column('session_id', sa.Text(), nullable=True),
            sa.Column('csrf_token', sa.Text(), nullable=True),
            sa.Column('datadome_cookie', sa.Text(), nullable=True),
            sa.Column('datadome_status', postgresql.ENUM('UNKNOWN', 'VALID', 'EXPIRED', 'BLOCKED', 'CAPTCHA_REQUIRED', name='datadomestatus', create_type=False), nullable=True, server_default='UNKNOWN'),
            sa.Column('datadome_last_check', sa.DateTime(timezone=True), nullable=True),
            sa.Column('item_count', sa.Integer(), nullable=True),
            sa.Column('total_items_count', sa.Integer(), nullable=True),
            sa.Column('given_item_count', sa.Integer(), nullable=True),
            sa.Column('taken_item_count', sa.Integer(), nullable=True),
            sa.Column('followers_count', sa.Integer(), nullable=True),
            sa.Column('feedback_count', sa.Integer(), nullable=True),
            sa.Column('feedback_reputation', sa.Float(), nullable=True),
            sa.Column('positive_feedback_count', sa.Integer(), nullable=True),
            sa.Column('negative_feedback_count', sa.Integer(), nullable=True),
            sa.Column('is_business', sa.Boolean(), nullable=True),
            sa.Column('is_on_holiday', sa.Boolean(), nullable=True),
            sa.Column('stats_updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['public.users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_id'),
            schema='template_tenant'
        )
        print("  + vinted_connection")

    # vinted_conversations
    if not table_exists(connection, 'template_tenant', 'vinted_conversations'):
        op.create_table(
            'vinted_conversations',
            sa.Column('conversation_id', sa.BigInteger(), nullable=False),
            sa.Column('opposite_user_id', sa.BigInteger(), nullable=True),
            sa.Column('opposite_user_login', sa.String(255), nullable=True),
            sa.Column('opposite_user_photo_url', sa.String(500), nullable=True),
            sa.Column('item_id', sa.BigInteger(), nullable=True),
            sa.Column('item_title', sa.String(500), nullable=True),
            sa.Column('item_photo_url', sa.String(500), nullable=True),
            sa.Column('item_count', sa.Integer(), nullable=True),
            sa.Column('is_unread', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('unread_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('last_message_preview', sa.Text(), nullable=True),
            sa.Column('transaction_id', sa.BigInteger(), nullable=True),
            sa.Column('updated_at_vinted', sa.DateTime(timezone=True), nullable=True),
            sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('conversation_id'),
            schema='template_tenant'
        )
        print("  + vinted_conversations")

    # vinted_messages
    if not table_exists(connection, 'template_tenant', 'vinted_messages'):
        op.create_table(
            'vinted_messages',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('conversation_id', sa.BigInteger(), nullable=False),
            sa.Column('vinted_message_id', sa.BigInteger(), nullable=True),
            sa.Column('entity_type', sa.String(50), nullable=True),
            sa.Column('sender_id', sa.BigInteger(), nullable=True),
            sa.Column('sender_login', sa.String(255), nullable=True),
            sa.Column('body', sa.Text(), nullable=True),
            sa.Column('title', sa.String(255), nullable=True),
            sa.Column('subtitle', sa.String(255), nullable=True),
            sa.Column('offer_price', sa.Numeric(10, 2), nullable=True),
            sa.Column('offer_status', sa.String(50), nullable=True),
            sa.Column('is_from_current_user', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('created_at_vinted', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['conversation_id'], ['template_tenant.vinted_conversations.conversation_id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            schema='template_tenant'
        )
        print("  + vinted_messages")

    # vinted_jobs
    if not table_exists(connection, 'template_tenant', 'vinted_jobs'):
        op.create_table(
            'vinted_jobs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('batch_id', sa.String(50), nullable=True),
            sa.Column('action_type_id', sa.Integer(), nullable=False),
            sa.Column('product_id', sa.Integer(), nullable=True),
            sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
            sa.Column('priority', sa.Integer(), nullable=False, server_default='3'),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('result_data', postgresql.JSONB(), nullable=True),
            sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['action_type_id'], ['vinted.action_types.id']),
            sa.ForeignKeyConstraint(['product_id'], ['template_tenant.products.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
            sa.CheckConstraint("status IN ('pending', 'running', 'paused', 'completed', 'failed', 'cancelled', 'expired')", name='valid_status'),
            schema='template_tenant'
        )
        op.create_index('ix_templatetenant_vinted_jobs_status', 'vinted_jobs', ['status'], schema='template_tenant')
        op.create_index('ix_templatetenant_vinted_jobs_batch_id', 'vinted_jobs', ['batch_id'], schema='template_tenant')
        print("  + vinted_jobs")

    # vinted_job_stats
    if not table_exists(connection, 'template_tenant', 'vinted_job_stats'):
        op.create_table(
            'vinted_job_stats',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('action_type_id', sa.Integer(), nullable=False),
            sa.Column('date', sa.Date(), nullable=False),
            sa.Column('total_jobs', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('success_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('failure_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('avg_duration_ms', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['action_type_id'], ['vinted.action_types.id']),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('action_type_id', 'date'),
            schema='template_tenant'
        )
        print("  + vinted_job_stats")

    # plugin_tasks
    if not table_exists(connection, 'template_tenant', 'plugin_tasks'):
        op.create_table(
            'plugin_tasks',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('task_type', sa.String(50), nullable=True),
            sa.Column('product_id', sa.Integer(), nullable=True),
            sa.Column('job_id', sa.Integer(), nullable=True),
            sa.Column('platform', sa.String(20), nullable=True),
            sa.Column('http_method', sa.String(10), nullable=True),
            sa.Column('path', sa.String(500), nullable=True),
            sa.Column('payload', postgresql.JSONB(), nullable=True),
            sa.Column('result', postgresql.JSONB(), nullable=True),
            sa.Column('status', postgresql.ENUM('pending', 'processing', 'success', 'failed', 'timeout', 'cancelled', name='taskstatus', create_type=False), nullable=False, server_default='pending'),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['product_id'], ['template_tenant.products.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['job_id'], ['template_tenant.vinted_jobs.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
            schema='template_tenant'
        )
        op.create_index('ix_template_tenant_plugin_tasks_status', 'plugin_tasks', ['status'], schema='template_tenant')
        op.create_index('ix_template_tenant_plugin_tasks_job_id', 'plugin_tasks', ['job_id'], schema='template_tenant')
        print("  + plugin_tasks")

    # ebay_credentials
    if not table_exists(connection, 'template_tenant', 'ebay_credentials'):
        op.create_table(
            'ebay_credentials',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('ebay_user_id', sa.String(255), nullable=True),
            sa.Column('access_token', sa.Text(), nullable=True),
            sa.Column('refresh_token', sa.Text(), nullable=True),
            sa.Column('token_expires_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('marketplace_id', sa.String(20), nullable=True, server_default='EBAY_FR'),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('account_type', sa.String(50), nullable=True),
            sa.Column('feedback_score', sa.Integer(), nullable=True),
            sa.Column('feedback_percentage', sa.Float(), nullable=True),
            sa.Column('seller_level', sa.String(50), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['public.users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_id'),
            schema='template_tenant'
        )
        print("  + ebay_credentials")

    # ebay_products
    if not table_exists(connection, 'template_tenant', 'ebay_products'):
        op.create_table(
            'ebay_products',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('product_id', sa.Integer(), nullable=False),
            sa.Column('ebay_sku', sa.String(100), nullable=False),
            sa.Column('title', sa.String(80), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('price', sa.Numeric(10, 2), nullable=False),
            sa.Column('currency', sa.String(3), nullable=False, server_default='EUR'),
            sa.Column('brand', sa.String(100), nullable=True),
            sa.Column('size', sa.String(50), nullable=True),
            sa.Column('color', sa.String(50), nullable=True),
            sa.Column('material', sa.String(100), nullable=True),
            sa.Column('category_id', sa.String(20), nullable=True),
            sa.Column('category_name', sa.String(255), nullable=True),
            sa.Column('condition', sa.String(50), nullable=True),
            sa.Column('condition_description', sa.Text(), nullable=True),
            sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('availability_type', sa.String(50), nullable=True, server_default='IN_STOCK'),
            sa.Column('marketplace_id', sa.String(20), nullable=True, server_default='EBAY_FR'),
            sa.Column('ebay_listing_id', sa.String(50), nullable=True),
            sa.Column('ebay_offer_id', sa.String(50), nullable=True),
            sa.Column('image_urls', postgresql.JSONB(), nullable=True),
            sa.Column('status', sa.String(50), nullable=False, server_default='DRAFT'),
            sa.Column('listing_format', sa.String(50), nullable=True, server_default='FIXED_PRICE'),
            sa.Column('listing_duration', sa.String(20), nullable=True, server_default='GTC'),
            sa.Column('package_weight_value', sa.Float(), nullable=True),
            sa.Column('package_weight_unit', sa.String(10), nullable=True, server_default='KILOGRAM'),
            sa.Column('location', sa.String(255), nullable=True),
            sa.Column('country', sa.String(2), nullable=True, server_default='FR'),
            sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['product_id'], ['template_tenant.products.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('product_id'),
            sa.UniqueConstraint('ebay_sku'),
            schema='template_tenant'
        )
        print("  + ebay_products")

    # ebay_products_marketplace
    if not table_exists(connection, 'template_tenant', 'ebay_products_marketplace'):
        op.create_table(
            'ebay_products_marketplace',
            sa.Column('sku_derived', sa.String(150), nullable=False),
            sa.Column('product_id', sa.Integer(), nullable=False),
            sa.Column('marketplace_id', sa.String(20), nullable=False),
            sa.Column('ebay_offer_id', sa.String(50), nullable=True),
            sa.Column('ebay_listing_id', sa.String(50), nullable=True),
            sa.Column('status', sa.String(50), nullable=False, server_default='DRAFT'),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('sold_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['product_id'], ['template_tenant.products.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('sku_derived'),
            schema='template_tenant'
        )
        print("  + ebay_products_marketplace")

    # ebay_promoted_listings
    if not table_exists(connection, 'template_tenant', 'ebay_promoted_listings'):
        op.create_table(
            'ebay_promoted_listings',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('campaign_id', sa.String(50), nullable=False),
            sa.Column('campaign_name', sa.String(255), nullable=True),
            sa.Column('marketplace_id', sa.String(20), nullable=False),
            sa.Column('product_id', sa.Integer(), nullable=False),
            sa.Column('sku_derived', sa.String(150), nullable=True),
            sa.Column('ad_id', sa.String(50), nullable=True),
            sa.Column('listing_id', sa.String(50), nullable=True),
            sa.Column('bid_percentage', sa.Float(), nullable=True),
            sa.Column('ad_status', sa.String(50), nullable=True),
            sa.Column('total_clicks', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('total_impressions', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('total_sales', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('total_sales_amount', sa.Numeric(10, 2), nullable=True),
            sa.Column('total_ad_fees', sa.Numeric(10, 2), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['product_id'], ['template_tenant.products.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('ad_id'),
            schema='template_tenant'
        )
        print("  + ebay_promoted_listings")

    # ebay_orders
    if not table_exists(connection, 'template_tenant', 'ebay_orders'):
        op.create_table(
            'ebay_orders',
            sa.Column('id', sa.BigInteger(), nullable=False),
            sa.Column('order_id', sa.String(50), nullable=False),
            sa.Column('marketplace_id', sa.String(20), nullable=True),
            sa.Column('buyer_username', sa.String(255), nullable=True),
            sa.Column('buyer_email', sa.String(255), nullable=True),
            sa.Column('shipping_name', sa.String(255), nullable=True),
            sa.Column('shipping_address', sa.Text(), nullable=True),
            sa.Column('shipping_city', sa.String(100), nullable=True),
            sa.Column('shipping_postal_code', sa.String(20), nullable=True),
            sa.Column('shipping_country', sa.String(2), nullable=True),
            sa.Column('total_price', sa.Numeric(10, 2), nullable=True),
            sa.Column('currency', sa.String(3), nullable=True),
            sa.Column('shipping_cost', sa.Numeric(10, 2), nullable=True),
            sa.Column('order_fulfillment_status', sa.String(50), nullable=True),
            sa.Column('order_payment_status', sa.String(50), nullable=True),
            sa.Column('tracking_number', sa.String(100), nullable=True),
            sa.Column('shipping_carrier', sa.String(50), nullable=True),
            sa.Column('creation_date', sa.DateTime(timezone=True), nullable=True),
            sa.Column('paid_date', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('order_id'),
            schema='template_tenant'
        )
        print("  + ebay_orders")

    # ebay_orders_products
    if not table_exists(connection, 'template_tenant', 'ebay_orders_products'):
        op.create_table(
            'ebay_orders_products',
            sa.Column('id', sa.BigInteger(), nullable=False),
            sa.Column('order_id', sa.BigInteger(), nullable=False),
            sa.Column('line_item_id', sa.String(50), nullable=True),
            sa.Column('sku', sa.String(100), nullable=True),
            sa.Column('sku_original', sa.String(100), nullable=True),
            sa.Column('title', sa.String(255), nullable=True),
            sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('unit_price', sa.Numeric(10, 2), nullable=True),
            sa.Column('total_price', sa.Numeric(10, 2), nullable=True),
            sa.Column('currency', sa.String(3), nullable=True),
            sa.Column('legacy_item_id', sa.String(50), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['order_id'], ['template_tenant.ebay_orders.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            schema='template_tenant'
        )
        print("  + ebay_orders_products")

    print("  Done.")

    # =========================================================================
    # PART 8: SEED DATA (only for new databases)
    # =========================================================================
    print("\n[8/9] Seeding reference data...")

    # Helper to check if table has data
    def table_has_data(schema: str, table: str) -> bool:
        result = connection.execute(text(
            f"SELECT EXISTS (SELECT 1 FROM {schema}.{table} LIMIT 1)"
        ))
        return result.scalar()

    # Seed subscription_quotas (only if empty)
    if not table_has_data('public', 'subscription_quotas'):
        connection.execute(text("""
            INSERT INTO public.subscription_quotas (id, tier, max_products, max_platforms, ai_credits_monthly)
            VALUES
                (1, 'FREE', 30, 2, 15),
                (2, 'STARTER', 150, 3, 75),
                (3, 'PRO', 500, 5, 250),
                (4, 'ENTERPRISE', 999999, 999999, 999999)
            ON CONFLICT (tier) DO NOTHING
        """))
        print("  + subscription_quotas seeded")
    else:
        print("  - subscription_quotas already has data, skipping")

    # Seed vinted action_types (only if empty)
    if not table_has_data('vinted', 'action_types'):
        connection.execute(text("""
            INSERT INTO vinted.action_types (id, code, name, description, priority, is_batch, rate_limit_ms, max_retries, timeout_seconds)
            VALUES
                (1, 'message', 'Respond to message', 'Reply to Vinted buyer messages', 1, false, 1000, 3, 30),
                (2, 'orders', 'Fetch orders', 'Retrieve new orders/sales from Vinted', 3, true, 1500, 3, 60),
                (3, 'publish', 'Publish product', 'Create a new listing on Vinted', 3, false, 2500, 3, 120),
                (4, 'update', 'Update product', 'Modify price, description, photos', 3, false, 2000, 3, 60),
                (5, 'delete', 'Delete product', 'Remove listing from Vinted', 4, false, 2000, 3, 30),
                (6, 'sync', 'Sync products', 'Synchronize all products with Vinted', 4, true, 1500, 3, 300)
            ON CONFLICT (code) DO NOTHING
        """))
        print("  + vinted.action_types seeded")
    else:
        print("  - vinted.action_types already has data, skipping")

    # Seed ebay marketplace_config (only if empty - uses country_code for existing DBs)
    if not table_has_data('ebay', 'marketplace_config'):
        # Check if table has 'name' column (new schema) or not (old schema)
        has_name_column = connection.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'ebay' AND table_name = 'marketplace_config' AND column_name = 'name'
            )
        """)).scalar()

        if has_name_column:
            connection.execute(text("""
                INSERT INTO ebay.marketplace_config (id, marketplace_id, site_id, name, currency, language, is_active)
                VALUES
                    (1, 'EBAY_FR', 71, 'eBay France', 'EUR', 'fr-FR', true),
                    (2, 'EBAY_GB', 3, 'eBay UK', 'GBP', 'en-GB', true),
                    (3, 'EBAY_DE', 77, 'eBay Germany', 'EUR', 'de-DE', true),
                    (4, 'EBAY_IT', 101, 'eBay Italy', 'EUR', 'it-IT', true),
                    (5, 'EBAY_ES', 186, 'eBay Spain', 'EUR', 'es-ES', true),
                    (6, 'EBAY_NL', 146, 'eBay Netherlands', 'EUR', 'nl-NL', true),
                    (7, 'EBAY_BE', 23, 'eBay Belgium', 'EUR', 'fr-BE', true),
                    (8, 'EBAY_PL', 212, 'eBay Poland', 'PLN', 'pl-PL', true)
                ON CONFLICT (marketplace_id) DO NOTHING
            """))
        else:
            # Old schema with country_code instead of name/language
            connection.execute(text("""
                INSERT INTO ebay.marketplace_config (marketplace_id, country_code, site_id, currency, is_active)
                VALUES
                    ('EBAY_FR', 'FR', 71, 'EUR', true),
                    ('EBAY_GB', 'GB', 3, 'GBP', true),
                    ('EBAY_DE', 'DE', 77, 'EUR', true),
                    ('EBAY_IT', 'IT', 101, 'EUR', true),
                    ('EBAY_ES', 'ES', 186, 'EUR', true),
                    ('EBAY_NL', 'NL', 146, 'EUR', true),
                    ('EBAY_BE', 'BE', 23, 'EUR', true),
                    ('EBAY_PL', 'PL', 212, 'PLN', true)
                ON CONFLICT (marketplace_id) DO NOTHING
            """))
        print("  + ebay.marketplace_config seeded")
    else:
        print("  - ebay.marketplace_config already has data, skipping")

    # Seed basic genders (only if empty)
    if not table_has_data('product_attributes', 'genders'):
        connection.execute(text("""
            INSERT INTO product_attributes.genders (name_en, name_fr, vinted_id)
            VALUES
                ('Men', 'Homme', 1),
                ('Women', 'Femme', 2),
                ('Unisex', 'Unisexe', NULL)
            ON CONFLICT (name_en) DO NOTHING
        """))
        print("  + product_attributes.genders seeded")
    else:
        print("  - product_attributes.genders already has data, skipping")

    # Seed basic conditions (only if empty)
    if not table_has_data('product_attributes', 'conditions'):
        connection.execute(text("""
            INSERT INTO product_attributes.conditions (note, name_en, name_fr, vinted_id)
            VALUES
                (5, 'New with tags', 'Neuf avec etiquette', 6),
                (4, 'New without tags', 'Neuf sans etiquette', 1),
                (3, 'Very good', 'Tres bon etat', 2),
                (2, 'Good', 'Bon etat', 3),
                (1, 'Satisfactory', 'Satisfaisant', 4)
            ON CONFLICT (note) DO NOTHING
        """))
        print("  + product_attributes.conditions seeded")
    else:
        print("  - product_attributes.conditions already has data, skipping")

    # Seed basic sizes (only if empty)
    if not table_has_data('product_attributes', 'sizes'):
        connection.execute(text("""
            INSERT INTO product_attributes.sizes (name_en, name_fr)
            VALUES
                ('XS', 'XS'), ('S', 'S'), ('M', 'M'), ('L', 'L'), ('XL', 'XL'), ('XXL', 'XXL'),
                ('One size', 'Taille unique')
            ON CONFLICT (name_en) DO NOTHING
        """))
        print("  + product_attributes.sizes seeded")
    else:
        print("  - product_attributes.sizes already has data, skipping")

    # Seed basic seasons (only if empty)
    if not table_has_data('product_attributes', 'seasons'):
        connection.execute(text("""
            INSERT INTO product_attributes.seasons (name_en, name_fr)
            VALUES
                ('Spring', 'Printemps'), ('Summer', 'Ete'), ('Autumn', 'Automne'),
                ('Winter', 'Hiver'), ('All seasons', 'Toutes saisons')
            ON CONFLICT (name_en) DO NOTHING
        """))
        print("  + product_attributes.seasons seeded")
    else:
        print("  - product_attributes.seasons already has data, skipping")

    # Seed basic fits (only if empty)
    if not table_has_data('product_attributes', 'fits'):
        connection.execute(text("""
            INSERT INTO product_attributes.fits (name_en, name_fr)
            VALUES
                ('regular', 'Regular'), ('slim', 'Slim'), ('oversized', 'Oversized'),
                ('relaxed', 'Relaxed'), ('loose', 'Loose'), ('skinny', 'Skinny'),
                ('straight', 'Straight'), ('tapered', 'Tapered'), ('wide', 'Wide'),
                ('cropped', 'Cropped'), ('bootcut', 'Bootcut'), ('flared', 'Flared')
            ON CONFLICT (name_en) DO NOTHING
        """))
        print("  + product_attributes.fits seeded")
    else:
        print("  - product_attributes.fits already has data, skipping")

    print("  Done.")

    # =========================================================================
    # PART 9: CREATE VIEWS AND FUNCTIONS
    # =========================================================================
    print("\n[9/9] Creating views and functions...")

    # Create get_vinted_category function
    connection.execute(text("""
        CREATE OR REPLACE FUNCTION vinted.get_vinted_category(
            p_category TEXT,
            p_gender TEXT DEFAULT NULL,
            p_fit TEXT DEFAULT NULL,
            p_length TEXT DEFAULT NULL,
            p_rise TEXT DEFAULT NULL,
            p_material TEXT DEFAULT NULL,
            p_pattern TEXT DEFAULT NULL,
            p_neckline TEXT DEFAULT NULL,
            p_sleeve_length TEXT DEFAULT NULL
        ) RETURNS INTEGER AS $$
        DECLARE
            v_result INTEGER;
        BEGIN
            -- Try to find exact match with attributes
            SELECT m.vinted_id INTO v_result
            FROM vinted.mapping m
            WHERE m.my_category = p_category
              AND (p_gender IS NULL OR m.my_gender = p_gender OR m.my_gender IS NULL)
              AND (p_fit IS NULL OR m.my_fit = p_fit OR m.my_fit IS NULL)
              AND (p_length IS NULL OR m.my_length = p_length OR m.my_length IS NULL)
              AND (p_rise IS NULL OR m.my_rise = p_rise OR m.my_rise IS NULL)
              AND (p_material IS NULL OR m.my_material = p_material OR m.my_material IS NULL)
              AND (p_pattern IS NULL OR m.my_pattern = p_pattern OR m.my_pattern IS NULL)
              AND (p_neckline IS NULL OR m.my_neckline = p_neckline OR m.my_neckline IS NULL)
              AND (p_sleeve_length IS NULL OR m.my_sleeve_length = p_sleeve_length OR m.my_sleeve_length IS NULL)
            ORDER BY
                CASE WHEN m.my_gender = p_gender THEN 10 ELSE 0 END +
                CASE WHEN m.my_fit = p_fit THEN 10 ELSE 0 END +
                CASE WHEN m.my_length = p_length THEN 10 ELSE 0 END +
                CASE WHEN m.my_rise = p_rise THEN 10 ELSE 0 END +
                CASE WHEN m.my_material = p_material THEN 5 ELSE 0 END +
                CASE WHEN m.my_pattern = p_pattern THEN 3 ELSE 0 END +
                CASE WHEN m.my_neckline = p_neckline THEN 3 ELSE 0 END +
                CASE WHEN m.my_sleeve_length = p_sleeve_length THEN 2 ELSE 0 END DESC,
                m.priority DESC
            LIMIT 1;

            -- Fallback to default mapping
            IF v_result IS NULL THEN
                SELECT m.vinted_id INTO v_result
                FROM vinted.mapping m
                WHERE m.my_category = p_category
                  AND m.is_default = true
                  AND (p_gender IS NULL OR m.my_gender = p_gender OR m.my_gender IS NULL)
                LIMIT 1;
            END IF;

            RETURN v_result;
        END;
        $$ LANGUAGE plpgsql;
    """))
    print("  + vinted.get_vinted_category() function created")

    print("  Done.")

    print("\n" + "=" * 70)
    print("SQUASHED MIGRATION COMPLETE!")
    print("=" * 70 + "\n")


def downgrade() -> None:
    """Drop all tables and schemas in reverse order."""
    connection = op.get_bind()

    print("\n" + "=" * 70)
    print("DOWNGRADE: Dropping all schemas and tables")
    print("=" * 70)

    # Drop schemas with CASCADE (will drop all contained objects)
    schemas_to_drop = ['template_tenant', 'vinted', 'ebay', 'product_attributes']
    for schema in schemas_to_drop:
        connection.execute(text(f"DROP SCHEMA IF EXISTS {schema} CASCADE"))
        print(f"  - Dropped schema: {schema}")

    # Drop public tables
    public_tables = [
        'admin_audit_logs', 'role_permissions', 'permissions',
        'doc_articles', 'doc_categories', 'ai_credits',
        'clothing_prices', 'users', 'subscription_quotas'
    ]
    for table in public_tables:
        connection.execute(text(f"DROP TABLE IF EXISTS public.{table} CASCADE"))
        print(f"  - Dropped table: public.{table}")

    # Drop ENUMs
    enums = [
        'datadomestatus', 'jobstatus', 'taskstatus', 'gender',
        'estimated_products', 'business_type', 'account_type',
        'publication_status', 'product_status', 'platform_type',
        'subscription_tier', 'user_role'
    ]
    for enum in enums:
        connection.execute(text(f"DROP TYPE IF EXISTS {enum} CASCADE"))
        print(f"  - Dropped ENUM: {enum}")

    print("\nDOWNGRADE COMPLETE!\n")
