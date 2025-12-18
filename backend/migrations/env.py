"""
Alembic environment configuration with multi-tenant support.
"""
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config
from sqlalchemy import pool, text

from alembic import context

# Ajouter le projet au path Python
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Importer configuration et models
from shared.config import settings
from shared.database import Base

# Import all models here pour autodétection
# NOTE (2025-12-09): Seuls les models actifs sont importés
# Les tables d'attributs (brands, categories, etc.) ont été désactivées
from models.public.user import User, SubscriptionTier
from models.public.platform_mapping import PlatformMapping
from models.public.subscription_quota import SubscriptionQuota
from models.public.ai_credit import AICredit
# DISABLED: Attribute tables (do not exist in DB)
# from models.public.brand import Brand
# from models.public.category import Category
# from models.public.color import Color
# from models.public.condition import Condition
# from models.public.fit import Fit
# from models.public.gender import Gender
# from models.public.material import Material
# from models.public.season import Season
# from models.public.size import Size
from models.user.product import Product
from models.user.product_image import ProductImage
from models.user.vinted_product import VintedProduct
from models.user.publication_history import PublicationHistory
from models.user.ai_generation_log import AIGenerationLog

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_url():
    """
    Get database URL from settings.

    Priorité:
    1. Variable d'environnement TEST_DATABASE_URL (tests)
    2. Configuration Alembic (override via conftest.py)
    3. Settings par défaut (dev/prod)
    """
    import os

    # 1. Mode test: priorité à TEST_DATABASE_URL
    test_url = os.getenv("TEST_DATABASE_URL")
    if test_url:
        return test_url

    # 2. Configuration Alembic (set via alembic.ini ou conftest.py)
    alembic_url = config.get_main_option("sqlalchemy.url")
    if alembic_url and alembic_url != "driver://user:pass@localhost/dbname":
        return alembic_url

    # 3. Settings par défaut (dev/prod)
    return str(settings.database_url)


def get_all_client_schemas(connection):
    """
    Récupère tous les schemas utilisateurs existants.

    Returns:
        Liste des noms de schemas (ex: ['user_1', 'user_2'])
    """
    result = connection.execute(
        text(f"""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name LIKE '{settings.user_schema_prefix}%'
            ORDER BY schema_name
        """)
    )
    return [row[0] for row in result.fetchall()]


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

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
    Support multi-schema pour multi-tenant.
    """
    # Configuration engine
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # 1. Migration du schema PUBLIC (tables communes)
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=False,  # Seulement public
        )

        with context.begin_transaction():
            # Set search_path to public
            connection.execute(text("SET search_path TO public"))
            context.run_migrations()

        # 2. Migration de tous les schemas CLIENTS
        client_schemas = get_all_client_schemas(connection)

        for schema_name in client_schemas:
            print(f"🔄 Migrating schema: {schema_name}")

            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                version_table_schema=schema_name,
            )

            with context.begin_transaction():
                # Set search_path to client schema
                connection.execute(text(f"SET search_path TO {schema_name}, public"))
                context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
