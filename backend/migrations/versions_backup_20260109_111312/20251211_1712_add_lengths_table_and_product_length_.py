"""add_lengths_table_and_product_length_column

Revision ID: 7f8g9h0i1j2k
Revises: 4e5f6a7b8c9d
Create Date: 2025-12-11 17:12:00.000000+01:00

Cette migration ajoute la table lengths dans le schema product_attributes
et ajoute la colonne length dans la table products.

Tables créées:
- product_attributes.lengths (12 longueurs pré-remplies)

Colonnes ajoutées:
- length (String(100), nullable) dans template_tenant.products et tous les user schemas

Author: Claude
Date: 2025-12-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f8g9h0i1j2k'
down_revision: Union[str, None] = '4e5f6a7b8c9d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ===== DATA: 12 LENGTHS =====
LENGTHS_DATA = [
    ("Cropped", "Court (au-dessus des hanches)"),
    ("Short", "Court"),
    ("Regular", "Standard"),
    ("Long", "Long"),
    ("Extra Long", "Très long"),
    ("Mini", "Mini"),
    ("Knee Length", "Au genou"),
    ("Midi", "Mi-mollet"),
    ("Maxi", "Long (cheville)"),
    ("Floor Length", "Au sol"),
    ("Ankle", "Cheville"),
    ("Capri", "3/4"),
]


def upgrade() -> None:
    """
    Ajoute la table lengths et la colonne length dans products.
    """
    connection = op.get_bind()

    # ===== 1. CRÉER LA TABLE lengths DANS product_attributes (SI ELLE N'EXISTE PAS) =====
    table_exists = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'product_attributes'
            AND table_name = 'lengths'
        )
    """)).scalar()

    if not table_exists:
        op.create_table(
            'lengths',
            sa.Column('name_en', sa.String(length=100), nullable=False, comment="Nom de la longueur (EN)"),
            sa.Column('name_fr', sa.String(length=100), nullable=True, comment="Nom de la longueur (FR)"),
            sa.Column('description', sa.Text(), nullable=True, comment="Description de la longueur"),
            sa.PrimaryKeyConstraint('name_en'),
            schema='product_attributes'
        )
        op.create_index('ix_product_attributes_lengths_name_en', 'lengths', ['name_en'], unique=False, schema='product_attributes')
        print("  ✓ Created lengths table")

        # ===== 2. INSÉRER LES 12 LENGTHS =====
        for name_en, name_fr in LENGTHS_DATA:
            connection.execute(
                sa.text(
                    "INSERT INTO product_attributes.lengths (name_en, name_fr) VALUES (:name_en, :name_fr)"
                ),
                {"name_en": name_en, "name_fr": name_fr}
            )
        print(f"  ✓ Inserted {len(LENGTHS_DATA)} lengths into product_attributes.lengths")
    else:
        print("  ⏭️  Lengths table already exists, skipping creation")

    # ===== 3. AJOUTER LA COLONNE length DANS template_tenant.products (SI ELLE N'EXISTE PAS) =====
    column_exists = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns
            WHERE table_schema = 'template_tenant'
            AND table_name = 'products'
            AND column_name = 'length'
        )
    """)).scalar()

    if not column_exists:
        op.add_column(
            'products',
            sa.Column('length', sa.String(length=100), nullable=True, comment="Longueur (FK product_attributes.lengths)"),
            schema='template_tenant'
        )
        op.create_index(
            'ix_template_tenant_products_length',
            'products',
            ['length'],
            unique=False,
            schema='template_tenant'
        )
        print("  ✓ Added length column to template_tenant.products")
    else:
        print("  ⏭️  Length column already exists in template_tenant.products, skipping")

    # ===== 4. AJOUTER LA COLONNE length DANS TOUS LES SCHEMAS USER EXISTANTS =====
    # Vérifier que la table products existe avant d'ajouter la colonne
    result = connection.execute(sa.text("""
        SELECT DISTINCT table_schema
        FROM information_schema.tables
        WHERE table_schema LIKE 'user_%'
        AND table_name = 'products'
    """))
    user_schemas = [row[0] for row in result]

    for schema_name in user_schemas:
        # Vérifier si la colonne existe déjà
        column_exists = connection.execute(sa.text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_schema = '{schema_name}'
                AND table_name = 'products'
                AND column_name = 'length'
            )
        """)).scalar()

        if not column_exists:
            # Ajouter la colonne length
            op.add_column(
                'products',
                sa.Column('length', sa.String(length=100), nullable=True, comment="Longueur (FK product_attributes.lengths)"),
                schema=schema_name
            )
            # Créer l'index
            op.create_index(
                f'ix_{schema_name}_products_length',
                'products',
                ['length'],
                unique=False,
                schema=schema_name
            )
            print(f"  ✓ Added length column to {schema_name}.products")
        else:
            print(f"  ⏭️  Length column already exists in {schema_name}.products, skipping")


def downgrade() -> None:
    """
    Supprime la colonne length et la table lengths.
    """

    # ===== 1. SUPPRIMER LA COLONNE length DES SCHEMAS USER EXISTANTS =====
    connection = op.get_bind()
    result = connection.execute(sa.text(
        "SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'user_%'"
    ))
    user_schemas = [row[0] for row in result]

    for schema_name in user_schemas:
        # Vérifier si l'index existe avant de le supprimer
        index_exists = connection.execute(sa.text(f"""
            SELECT EXISTS (
                SELECT FROM pg_indexes
                WHERE schemaname = '{schema_name}'
                AND indexname = 'ix_{schema_name}_products_length'
            )
        """)).scalar()

        if index_exists:
            op.drop_index(f'ix_{schema_name}_products_length', table_name='products', schema=schema_name)

        # Vérifier si la colonne existe avant de la supprimer
        column_exists = connection.execute(sa.text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_schema = '{schema_name}'
                AND table_name = 'products'
                AND column_name = 'length'
            )
        """)).scalar()

        if column_exists:
            op.drop_column('products', 'length', schema=schema_name)

    # ===== 2. SUPPRIMER LA COLONNE length DE template_tenant.products =====
    column_exists = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns
            WHERE table_schema = 'template_tenant'
            AND table_name = 'products'
            AND column_name = 'length'
        )
    """)).scalar()

    if column_exists:
        op.drop_index('ix_template_tenant_products_length', table_name='products', schema='template_tenant')
        op.drop_column('products', 'length', schema='template_tenant')

    # ===== 3. SUPPRIMER LA TABLE lengths =====
    table_exists = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'product_attributes'
            AND table_name = 'lengths'
        )
    """)).scalar()

    if table_exists:
        op.drop_index('ix_product_attributes_lengths_name_en', table_name='lengths', schema='product_attributes')
        op.drop_table('lengths', schema='product_attributes')
