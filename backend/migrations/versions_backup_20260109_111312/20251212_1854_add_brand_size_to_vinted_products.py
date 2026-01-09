"""add_brand_size_to_vinted_products

Revision ID: c53c8e6b804b
Revises: f1a2b3c4d5e6
Create Date: 2025-12-12 18:54:37.114795+01:00

Ajoute les colonnes brand et size à la table vinted_products
pour stocker les informations de marque et taille depuis l'API Vinted.

Author: Claude
Date: 2025-12-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c53c8e6b804b'
down_revision: Union[str, None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Ajoute les colonnes brand et size à vinted_products."""

    # Ajouter colonnes brand et size dans template_tenant
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'template_tenant'
                AND table_name = 'vinted_products'
                AND column_name = 'brand'
            ) THEN
                ALTER TABLE template_tenant.vinted_products
                ADD COLUMN brand VARCHAR(100);
                COMMENT ON COLUMN template_tenant.vinted_products.brand IS 'Nom de la marque sur Vinted';
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'template_tenant'
                AND table_name = 'vinted_products'
                AND column_name = 'size'
            ) THEN
                ALTER TABLE template_tenant.vinted_products
                ADD COLUMN size VARCHAR(50);
                COMMENT ON COLUMN template_tenant.vinted_products.size IS 'Taille affichée sur Vinted';
            END IF;
        END $$;
    """)

    # Appliquer aux schemas user existants (uniquement si la table existe)
    op.execute("""
        DO $$
        DECLARE
            schema_name TEXT;
        BEGIN
            FOR schema_name IN
                SELECT nspname FROM pg_namespace
                WHERE nspname LIKE 'user_%'
            LOOP
                -- Vérifier si la table vinted_products existe dans ce schema
                IF EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = schema_name
                    AND table_name = 'vinted_products'
                ) THEN
                    -- Ajouter brand si n'existe pas
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_schema = schema_name
                        AND table_name = 'vinted_products'
                        AND column_name = 'brand'
                    ) THEN
                        EXECUTE format('ALTER TABLE %I.vinted_products ADD COLUMN brand VARCHAR(100)', schema_name);
                    END IF;

                    -- Ajouter size si n'existe pas
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_schema = schema_name
                        AND table_name = 'vinted_products'
                        AND column_name = 'size'
                    ) THEN
                        EXECUTE format('ALTER TABLE %I.vinted_products ADD COLUMN size VARCHAR(50)', schema_name);
                    END IF;
                END IF;
            END LOOP;
        END $$;
    """)


def downgrade() -> None:
    """Supprime les colonnes brand et size de vinted_products."""

    # Supprimer de template_tenant
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'template_tenant'
                AND table_name = 'vinted_products'
                AND column_name = 'brand'
            ) THEN
                ALTER TABLE template_tenant.vinted_products DROP COLUMN brand;
            END IF;

            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'template_tenant'
                AND table_name = 'vinted_products'
                AND column_name = 'size'
            ) THEN
                ALTER TABLE template_tenant.vinted_products DROP COLUMN size;
            END IF;
        END $$;
    """)

    # Supprimer des schemas user existants (uniquement si la table existe)
    op.execute("""
        DO $$
        DECLARE
            schema_name TEXT;
        BEGIN
            FOR schema_name IN
                SELECT nspname FROM pg_namespace
                WHERE nspname LIKE 'user_%'
            LOOP
                -- Vérifier si la table vinted_products existe
                IF EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = schema_name
                    AND table_name = 'vinted_products'
                ) THEN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_schema = schema_name
                        AND table_name = 'vinted_products'
                        AND column_name = 'brand'
                    ) THEN
                        EXECUTE format('ALTER TABLE %I.vinted_products DROP COLUMN brand', schema_name);
                    END IF;

                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_schema = schema_name
                        AND table_name = 'vinted_products'
                        AND column_name = 'size'
                    ) THEN
                        EXECUTE format('ALTER TABLE %I.vinted_products DROP COLUMN size', schema_name);
                    END IF;
                END IF;
            END LOOP;
        END $$;
    """)
