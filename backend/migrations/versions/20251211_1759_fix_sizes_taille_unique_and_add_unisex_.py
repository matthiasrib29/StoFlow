"""fix_sizes_taille_unique_and_add_unisex_gender

Revision ID: 3m4n5o6p7q8r
Revises: 2l3m4n5o6p7q
Create Date: 2025-12-11 17:59:00.000000+01:00

Cette migration corrige deux problèmes dans les tables product_attributes:

Business Rules (Validé 2025-12-11):
1. SIZES: "TAILLE UNIQUE" est en français → doit être "one-size" en anglais
2. GENDERS: manque la valeur "unisex" (mixte/unisexe)

Actions:
1. Renommer "TAILLE UNIQUE" → "one-size" dans sizes (avec update des références products)
2. Ajouter "unisex" dans genders

Author: Claude
Date: 2025-12-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3m4n5o6p7q8r'
down_revision: Union[str, None] = '2l3m4n5o6p7q'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Corrige TAILLE UNIQUE et ajoute unisex.
    """
    connection = op.get_bind()

    # ===== 1. CORRIGER "TAILLE UNIQUE" → "one-size" DANS SIZES =====
    print("\n  🔄 Processing SIZES...")

    # Vérifier si "TAILLE UNIQUE" existe
    result = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT FROM product_attributes.sizes
            WHERE name = 'TAILLE UNIQUE'
        )
    """))

    taille_unique_exists = result.scalar()

    if taille_unique_exists:
        # Vérifier si "one-size" existe déjà
        result = connection.execute(sa.text("""
            SELECT EXISTS (
                SELECT FROM product_attributes.sizes
                WHERE name = 'one-size'
            )
        """))

        one_size_exists = result.scalar()

        if one_size_exists:
            # Conflit : merger TAILLE UNIQUE dans one-size
            print('  ⚠️  "one-size" exists, merging "TAILLE UNIQUE" into it')

            # Mettre à jour les références dans products
            connection.execute(sa.text("""
                UPDATE template_tenant.products
                SET label_size = 'one-size'
                WHERE label_size = 'TAILLE UNIQUE'
            """))

            # Mettre à jour dans tous les user schemas
            result = connection.execute(sa.text("""
                SELECT DISTINCT table_schema
                FROM information_schema.tables
                WHERE table_schema LIKE 'user_%'
                AND table_name = 'products'
            """))
            user_schemas = [row[0] for row in result]

            for schema in user_schemas:
                connection.execute(sa.text(f"""
                    UPDATE {schema}.products
                    SET label_size = 'one-size'
                    WHERE label_size = 'TAILLE UNIQUE'
                """))

            # Supprimer TAILLE UNIQUE
            connection.execute(sa.text("""
                DELETE FROM product_attributes.sizes
                WHERE name = 'TAILLE UNIQUE'
            """))

            print('  ✓ Merged "TAILLE UNIQUE" into "one-size" and updated references')

        else:
            # Pas de conflit : renommer directement
            # D'abord mettre à jour les références
            connection.execute(sa.text("""
                UPDATE template_tenant.products
                SET label_size = 'one-size'
                WHERE label_size = 'TAILLE UNIQUE'
            """))

            result = connection.execute(sa.text("""
                SELECT DISTINCT table_schema
                FROM information_schema.tables
                WHERE table_schema LIKE 'user_%'
                AND table_name = 'products'
            """))
            user_schemas = [row[0] for row in result]

            for schema in user_schemas:
                connection.execute(sa.text(f"""
                    UPDATE {schema}.products
                    SET label_size = 'one-size'
                    WHERE label_size = 'TAILLE UNIQUE'
                """))

            # Renommer la PK
            connection.execute(sa.text("""
                UPDATE product_attributes.sizes
                SET name = 'one-size', name_fr = 'taille unique'
                WHERE name = 'TAILLE UNIQUE'
            """))

            print('  ✓ Renamed "TAILLE UNIQUE" → "one-size"')

    else:
        print('  ⏭️  "TAILLE UNIQUE" not found, skipping')

    # ===== 2. AJOUTER "unisex" DANS GENDERS =====
    print("\n  🔄 Processing GENDERS...")

    # Vérifier si "unisex" existe déjà
    result = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT FROM product_attributes.genders
            WHERE name_en = 'unisex'
        )
    """))

    unisex_exists = result.scalar()

    if not unisex_exists:
        # Ajouter unisex
        connection.execute(sa.text("""
            INSERT INTO product_attributes.genders (name_en, name_fr)
            VALUES ('unisex', 'mixte')
        """))
        print('  ✓ Added "unisex" to genders')
    else:
        print('  ⏭️  "unisex" already exists, skipping')

    print("\n  📊 Fixes completed successfully")


def downgrade() -> None:
    """
    Restaure les valeurs d'origine.
    """
    connection = op.get_bind()

    # 1. Supprimer "unisex" de genders
    result = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT FROM product_attributes.genders
            WHERE name_en = 'unisex'
        )
    """))

    if result.scalar():
        connection.execute(sa.text("""
            DELETE FROM product_attributes.genders
            WHERE name_en = 'unisex'
        """))
        print('  ✓ Removed "unisex" from genders')

    # 2. Restaurer "TAILLE UNIQUE" dans sizes
    # Note: Complexe car on doit savoir s'il y avait conflit ou pas
    # On ne restaure pas dans ce cas (migration irréversible)
    print('  ⚠️  Cannot restore "TAILLE UNIQUE" (references already updated)')
