"""add_metadata_jsonb_to_products

Revision ID: 05ab399d382a
Revises: e3a9c8f12345
Create Date: 2025-12-06 19:13:58.782885+01:00

Business Rules (2025-12-06):
- Ajoute colonne integration_metadata JSONB pour stocker métadonnées intégrations
- Utilisé pour: vinted_id, source, imported_at, etc.
- Permet détection duplicatas lors de l'import Vinted
- Note: Nommé integration_metadata car 'metadata' est réservé par SQLAlchemy
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '05ab399d382a'
down_revision: Union[str, None] = 'e3a9c8f12345'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Ajoute la colonne integration_metadata JSONB à la table products dans TOUS les schemas tenant.

    Business Rules:
    - Column integration_metadata est nullable (JSONB, default NULL)
    - Utilisé pour stocker vinted_id, source, imported_at
    - Permet de détecter les duplicatas lors de l'import
    """
    conn = op.get_bind()

    # 1. Récupérer tous les tenants existants
    tenants = conn.execute(text("SELECT id FROM public.tenants")).fetchall()

    # 2. Pour chaque schema tenant, ajouter la colonne integration_metadata
    for tenant in tenants:
        schema_name = f"client_{tenant.id}"

        # Vérifier si le schema existe
        schema_exists = conn.execute(
            text(f"SELECT schema_name FROM information_schema.schemata WHERE schema_name = '{schema_name}'")
        ).first()

        if not schema_exists:
            print(f"Warning: Schema {schema_name} does not exist, skipping...")
            continue

        # Vérifier si la table products existe
        table_exists = conn.execute(
            text(f"""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = '{schema_name}' AND table_name = 'products'
            """)
        ).first()

        if not table_exists:
            print(f"Warning: Table products does not exist in {schema_name}, skipping...")
            continue

        # Ajouter colonne integration_metadata JSONB
        with op.batch_alter_table('products', schema=schema_name) as batch_op:
            batch_op.add_column(
                sa.Column(
                    'integration_metadata',
                    JSONB,
                    nullable=True,
                    comment='Métadonnées pour intégrations (vinted_id, source, etc.)'
                )
            )


def downgrade() -> None:
    """Supprime la colonne integration_metadata de tous les schemas tenant."""
    conn = op.get_bind()

    # Récupérer tous les tenants
    tenants = conn.execute(text("SELECT id FROM public.tenants")).fetchall()

    # Pour chaque schema tenant, supprimer la colonne integration_metadata
    for tenant in tenants:
        schema_name = f"client_{tenant.id}"

        with op.batch_alter_table('products', schema=schema_name) as batch_op:
            batch_op.drop_column('integration_metadata')
