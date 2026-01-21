"""
Alembic environment configuration with multi-tenant support.

Architecture:
- template_tenant: Template schema for user models (autogenerate target)
- user_X: Cloned from template_tenant (synced via scripts/sync_user_schemas.py)
- public, vinted, ebay: Fixed schemas (manual migrations only)

Autogenerate Strategy:
- Only user models (without explicit schema) are imported
- SET search_path TO template_tenant makes autogenerate work
- Models with explicit schema (vinted, ebay, public) require manual migrations

Usage:
    alembic revision --autogenerate -m "description"  # For template_tenant
    alembic upgrade head                              # Apply to all schemas
"""
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config
from sqlalchemy import pool, text

from alembic import context

# Add project to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import configuration and base
from shared.config import settings
from shared.database import Base

# =============================================================================
# IMPORT ONLY USER MODELS (no explicit schema)
# =============================================================================
# These models use search_path resolution (template_tenant)
# Models with explicit schema (vinted, ebay, public) are NOT imported
# because autogenerate doesn't work well with mixed schema declarations.
#
# For changes to vinted/ebay/public schemas, write manual migrations.
# =============================================================================

from models.user.product import Product
from models.user.vinted_product import VintedProduct
# PublicationHistory removed (2026-01-21): Obsolete, replaced by MarketplaceJob
from models.user.ai_generation_log import AIGenerationLog
from models.user.marketplace_batch import MarketplaceBatch
from models.user.marketplace_job import MarketplaceJob
from models.user.marketplace_task import MarketplaceTask
from models.user.vinted_connection import VintedConnection
from models.user.vinted_conversation import VintedConversation, VintedMessage
# VintedErrorLog removed (2026-01-21): Never used
# MarketplaceJobStats removed (2026-01-20): Not used
from models.user.ebay_credentials import EbayCredentials
from models.user.ebay_product import EbayProduct
from models.user.ebay_order import EbayOrder, EbayOrderProduct
# EbayPromotedListing removed (2026-01-20): Merged into EbayProduct
from models.user.etsy_credentials import EtsyCredentials

# Alembic Config object
config = context.config

# Setup logging from config file
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
target_metadata = Base.metadata


# User model table names (tables without explicit schema)
USER_MODEL_TABLES = {
    t.name for t in Base.metadata.tables.values() if t.schema is None
}


def include_object(object, name, type_, reflected, compare_to):
    """
    Filter which objects to include in autogenerate.

    Only include tables that:
    1. From metadata: have no explicit schema (user models)
    2. From database: match a user model table name

    Args:
        object: The SQLAlchemy object (Table, Column, Index, etc.)
        name: Name of the object
        type_: Type of object ('table', 'column', 'index', etc.)
        reflected: True if object was reflected from database
        compare_to: The object being compared to (or None)
    """
    if type_ == "table":
        if reflected:
            # Database table: only include if it matches a user model
            return name in USER_MODEL_TABLES
        else:
            # Metadata table: only include if no explicit schema
            schema = getattr(object, 'schema', None)
            return schema is None
    return True


def get_url():
    """
    Get database URL from settings.

    Priority:
    1. TEST_DATABASE_URL environment variable (tests)
    2. Alembic config (override via conftest.py)
    3. Default settings (dev/prod)
    """
    import os

    # 1. Test mode: priority to TEST_DATABASE_URL
    test_url = os.getenv("TEST_DATABASE_URL")
    if test_url:
        return test_url

    # 2. Alembic config (set via alembic.ini or conftest.py)
    alembic_url = config.get_main_option("sqlalchemy.url")
    if alembic_url and alembic_url != "driver://user:pass@localhost/dbname":
        return alembic_url

    # 3. Default settings (dev/prod)
    return str(settings.database_url)


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine.
    Calls to context.execute() emit the given string to the script output.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    Best practices for multi-tenant PostgreSQL:
    1. SET search_path to target schema (template_tenant)
    2. Use include_schemas=False (models don't have explicit schema)
    3. Set dialect.default_schema_name for proper reflection

    Note: user_X schemas are NOT migrated here.
    They are synced with template_tenant via: python scripts/sync_user_schemas.py
    """
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # Set search_path to template_tenant for autogenerate
        # This makes all unqualified table references resolve to template_tenant
        connection.execute(text("SET search_path TO template_tenant, public"))
        connection.commit()

        # Set default schema name for proper reflection (recommended workaround)
        # See: https://alembic.sqlalchemy.org/en/latest/cookbook.html
        connection.dialect.default_schema_name = "template_tenant"

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=False,  # Required for search_path approach
            include_object=include_object,  # Filter out tables with explicit schema
            version_table_schema="public",  # Single version table in public
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
