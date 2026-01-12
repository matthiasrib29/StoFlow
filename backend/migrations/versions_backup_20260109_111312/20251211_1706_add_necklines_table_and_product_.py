"""add_necklines_table_and_product_neckline_column

Revision ID: 4e5f6a7b8c9d
Revises: c7c1128b7a30
Create Date: 2025-12-11 17:06:00.000000+01:00

Cette migration ajoute la table necklines dans le schema product_attributes
et ajoute la colonne neckline dans la table products.

Tables créées:
- product_attributes.necklines (19 encolures pré-remplies)

Colonnes ajoutées:
- neckline (String(100), nullable) dans template_tenant.products et tous les user schemas

Author: Claude
Date: 2025-12-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4e5f6a7b8c9d'
down_revision: Union[str, None] = 'c7c1128b7a30'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ===== DATA: 19 NECKLINES =====
NECKLINES_DATA = [
    ("Round Neck", "Col rond"),
    ("V-Neck", "Col V"),
    ("Crew Neck", "Col ras du cou"),
    ("Scoop Neck", "Col dégagé"),
    ("Square Neck", "Col carré"),
    ("Boat Neck", "Col bateau"),
    ("Turtleneck", "Col roulé"),
    ("Mock Neck", "Col montant"),
    ("Polo Collar", "Col polo"),
    ("Henley", "Col tunisien"),
    ("Mandarin Collar", "Col mao"),
    ("Off-Shoulder", "Épaules dénudées"),
    ("Halter", "Dos-nu"),
    ("Cowl Neck", "Col bénitier"),
    ("Hood", "Capuche"),
    ("Collared", "Col chemise"),
    ("Shawl Collar", "Col châle"),
    ("Notch Lapel", "Revers cranté"),
    ("Peak Lapel", "Revers pointu"),
]


def upgrade() -> None:
    """
    Ajoute la table necklines et la colonne neckline dans products.
    """
    connection = op.get_bind()

    # ===== 1. CRÉER LA TABLE necklines DANS product_attributes (SI ELLE N'EXISTE PAS) =====
    table_exists = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'product_attributes'
            AND table_name = 'necklines'
        )
    """)).scalar()

    if not table_exists:
        op.create_table(
            'necklines',
            sa.Column('name_en', sa.String(length=100), nullable=False, comment="Nom de l'encolure (EN)"),
            sa.Column('name_fr', sa.String(length=100), nullable=True, comment="Nom de l'encolure (FR)"),
            sa.Column('description', sa.Text(), nullable=True, comment="Description de l'encolure"),
            sa.PrimaryKeyConstraint('name_en'),
            schema='product_attributes'
        )
        op.create_index('ix_product_attributes_necklines_name_en', 'necklines', ['name_en'], unique=False, schema='product_attributes')
        print("  ✓ Created necklines table")

        # ===== 2. INSÉRER LES 19 NECKLINES =====
        for name_en, name_fr in NECKLINES_DATA:
            connection.execute(
                sa.text(
                    "INSERT INTO product_attributes.necklines (name_en, name_fr) VALUES (:name_en, :name_fr)"
                ),
                {"name_en": name_en, "name_fr": name_fr}
            )
        print(f"  ✓ Inserted {len(NECKLINES_DATA)} necklines into product_attributes.necklines")
    else:
        print("  ⏭️  Necklines table already exists, skipping creation")

    # ===== 3. AJOUTER LA COLONNE neckline DANS template_tenant.products (SI ELLE N'EXISTE PAS) =====
    column_exists = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns
            WHERE table_schema = 'template_tenant'
            AND table_name = 'products'
            AND column_name = 'neckline'
        )
    """)).scalar()

    if not column_exists:
        op.add_column(
            'products',
            sa.Column('neckline', sa.String(length=100), nullable=True, comment="Encolure (FK product_attributes.necklines)"),
            schema='template_tenant'
        )
        op.create_index(
            'ix_template_tenant_products_neckline',
            'products',
            ['neckline'],
            unique=False,
            schema='template_tenant'
        )
        print("  ✓ Added neckline column to template_tenant.products")
    else:
        print("  ⏭️  Neckline column already exists in template_tenant.products, skipping")

    # ===== 4. AJOUTER LA COLONNE neckline DANS TOUS LES SCHEMAS USER EXISTANTS =====
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
                AND column_name = 'neckline'
            )
        """)).scalar()

        if not column_exists:
            # Ajouter la colonne neckline
            op.add_column(
                'products',
                sa.Column('neckline', sa.String(length=100), nullable=True, comment="Encolure (FK product_attributes.necklines)"),
                schema=schema_name
            )
            # Créer l'index
            op.create_index(
                f'ix_{schema_name}_products_neckline',
                'products',
                ['neckline'],
                unique=False,
                schema=schema_name
            )
            print(f"  ✓ Added neckline column to {schema_name}.products")
        else:
            print(f"  ⏭️  Neckline column already exists in {schema_name}.products, skipping")


def downgrade() -> None:
    """
    Supprime la colonne neckline et la table necklines.
    """

    # ===== 1. SUPPRIMER LA COLONNE neckline DES SCHEMAS USER EXISTANTS =====
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
                AND indexname = 'ix_{schema_name}_products_neckline'
            )
        """)).scalar()

        if index_exists:
            op.drop_index(f'ix_{schema_name}_products_neckline', table_name='products', schema=schema_name)

        # Vérifier si la colonne existe avant de la supprimer
        column_exists = connection.execute(sa.text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_schema = '{schema_name}'
                AND table_name = 'products'
                AND column_name = 'neckline'
            )
        """)).scalar()

        if column_exists:
            op.drop_column('products', 'neckline', schema=schema_name)

    # ===== 2. SUPPRIMER LA COLONNE neckline DE template_tenant.products =====
    column_exists = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns
            WHERE table_schema = 'template_tenant'
            AND table_name = 'products'
            AND column_name = 'neckline'
        )
    """)).scalar()

    if column_exists:
        op.drop_index('ix_template_tenant_products_neckline', table_name='products', schema='template_tenant')
        op.drop_column('products', 'neckline', schema='template_tenant')

    # ===== 3. SUPPRIMER LA TABLE necklines =====
    table_exists = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'product_attributes'
            AND table_name = 'necklines'
        )
    """)).scalar()

    if table_exists:
        op.drop_index('ix_product_attributes_necklines_name_en', table_name='necklines', schema='product_attributes')
        op.drop_table('necklines', schema='product_attributes')
