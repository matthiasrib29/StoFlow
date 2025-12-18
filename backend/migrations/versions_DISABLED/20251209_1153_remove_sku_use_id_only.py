"""remove_sku_use_id_only

Revision ID: fffe76d430c3
Revises: 24d10525915b
Create Date: 2025-12-09 11:53:19.069077+01:00

Business Decision (2025-12-09):
- Simplifier l'architecture en gardant uniquement l'ID auto-incrémenté
- Supprimer toute la logique SKU (colonne + séquences)
- L'ID PostgreSQL SERIAL suffit comme identifiant unique
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fffe76d430c3'
down_revision: Union[str, None] = '24d10525915b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Supprimer les colonnes SKU et les séquences product_sku_seq.

    Steps:
    1. Drop la colonne SKU de tous les schemas user_*
    2. Drop toutes les séquences product_sku_seq
    """
    connection = op.get_bind()

    # Step 1: Get all user schemas
    result = connection.execute(sa.text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
    """))

    user_schemas = [row[0] for row in result]

    # Step 2: Drop SKU column from products table in each schema
    for schema in user_schemas:
        # Drop la contrainte unique d'abord (si elle existe)
        try:
            connection.execute(sa.text(f"""
                ALTER TABLE {schema}.products
                DROP CONSTRAINT IF EXISTS uq_product_sku
            """))
        except Exception:
            pass  # Ignore if constraint doesn't exist

        # Drop la colonne SKU
        connection.execute(sa.text(f"""
            ALTER TABLE {schema}.products
            DROP COLUMN IF EXISTS sku
        """))

    # Step 3: Drop all product_sku_seq sequences
    for schema in user_schemas:
        connection.execute(sa.text(f"""
            DROP SEQUENCE IF EXISTS {schema}.product_sku_seq
        """))


def downgrade() -> None:
    """
    Rollback: Restaurer les colonnes SKU et séquences.

    ATTENTION: Les valeurs SKU seront NULL après le rollback.
    """
    connection = op.get_bind()

    # Get all user schemas
    result = connection.execute(sa.text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
    """))

    user_schemas = [row[0] for row in result]

    # Restore sequences
    for schema in user_schemas:
        connection.execute(sa.text(f"""
            CREATE SEQUENCE IF NOT EXISTS {schema}.product_sku_seq
            START WITH 1000
            INCREMENT BY 1
            NO MINVALUE
            NO MAXVALUE
            CACHE 1
        """))

    # Restore SKU column
    for schema in user_schemas:
        connection.execute(sa.text(f"""
            ALTER TABLE {schema}.products
            ADD COLUMN IF NOT EXISTS sku VARCHAR(100) UNIQUE
        """))

        # Add unique constraint
        try:
            connection.execute(sa.text(f"""
                ALTER TABLE {schema}.products
                ADD CONSTRAINT uq_product_sku UNIQUE (sku)
            """))
        except Exception:
            pass  # Ignore if already exists
