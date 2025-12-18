"""add_missing_pricing_columns_to_products

Revision ID: c2e26345985d
Revises: 8d3caab9361a
Create Date: 2025-12-09 12:15:30.543118+01:00

Business Decision (2025-12-09):
- Ajouter les colonnes pricing manquantes dans tous les schemas user_*
- Ces colonnes sont utilisées pour le calcul automatique des prix
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'c2e26345985d'
down_revision: Union[str, None] = '46aad9f85d14'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Ajouter les colonnes pricing manquantes dans tous les schemas user_*.
    """
    connection = op.get_bind()

    # Get all user schemas
    result = connection.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
    """))

    user_schemas = [row[0] for row in result]

    # Add pricing columns to each schema
    for schema in user_schemas:
        # Pricing columns
        connection.execute(text(f"""
            ALTER TABLE {schema}.products
            ADD COLUMN IF NOT EXISTS pricing_edit VARCHAR(100),
            ADD COLUMN IF NOT EXISTS pricing_rarity VARCHAR(100),
            ADD COLUMN IF NOT EXISTS pricing_quality VARCHAR(100),
            ADD COLUMN IF NOT EXISTS pricing_details VARCHAR(100),
            ADD COLUMN IF NOT EXISTS pricing_style VARCHAR(100)
        """))

        # Features columns
        connection.execute(text(f"""
            ALTER TABLE {schema}.products
            ADD COLUMN IF NOT EXISTS unique_feature TEXT,
            ADD COLUMN IF NOT EXISTS marking TEXT
        """))


def downgrade() -> None:
    """
    Supprimer les colonnes pricing de tous les schemas user_*.
    """
    connection = op.get_bind()

    # Get all user schemas
    result = connection.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
    """))

    user_schemas = [row[0] for row in result]

    # Remove pricing columns from each schema
    for schema in user_schemas:
        connection.execute(text(f"""
            ALTER TABLE {schema}.products
            DROP COLUMN IF EXISTS pricing_edit,
            DROP COLUMN IF EXISTS pricing_rarity,
            DROP COLUMN IF EXISTS pricing_quality,
            DROP COLUMN IF EXISTS pricing_details,
            DROP COLUMN IF EXISTS pricing_style,
            DROP COLUMN IF EXISTS unique_feature,
            DROP COLUMN IF EXISTS marking
        """))
