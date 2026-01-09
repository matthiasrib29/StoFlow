"""add_patterns_table_and_product_pattern_column

Revision ID: 8h9i0j1k2l3m
Revises: 7f8g9h0i1j2k
Create Date: 2025-12-11 17:18:00.000000+01:00

Cette migration ajoute la table patterns dans le schema product_attributes
et ajoute la colonne pattern dans la table products.

Tables créées:
- product_attributes.patterns (20 motifs pré-remplis)

Colonnes ajoutées:
- pattern (String(100), nullable) dans template_tenant.products et tous les user schemas

Author: Claude
Date: 2025-12-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8h9i0j1k2l3m'
down_revision: Union[str, None] = '7f8g9h0i1j2k'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ===== DATA: 20 PATTERNS =====
PATTERNS_DATA = [
    ("Solid", "Uni"),
    ("Striped", "Rayé"),
    ("Checkered", "À carreaux"),
    ("Plaid", "Tartan"),
    ("Floral", "Fleuri"),
    ("Polka Dot", "À pois"),
    ("Graphic", "Graphique"),
    ("Printed", "Imprimé"),
    ("Camouflage", "Camouflage"),
    ("Animal Print", "Imprimé animal"),
    ("Tie-Dye", "Tie-dye"),
    ("Abstract", "Abstrait"),
    ("Geometric", "Géométrique"),
    ("Tropical", "Tropical"),
    ("Paisley", "Cachemire"),
    ("Houndstooth", "Pied-de-poule"),
    ("Herringbone", "Chevrons"),
    ("Color Block", "Color block"),
    ("Ombre", "Dégradé"),
    ("Embroidered", "Brodé"),
]


def upgrade() -> None:
    """
    Ajoute la table patterns et la colonne pattern dans products.
    """
    connection = op.get_bind()

    # ===== 1. CRÉER LA TABLE patterns DANS product_attributes (SI ELLE N'EXISTE PAS) =====
    table_exists = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'product_attributes'
            AND table_name = 'patterns'
        )
    """)).scalar()

    if not table_exists:
        op.create_table(
            'patterns',
            sa.Column('name_en', sa.String(length=100), nullable=False, comment="Nom du motif (EN)"),
            sa.Column('name_fr', sa.String(length=100), nullable=True, comment="Nom du motif (FR)"),
            sa.Column('description', sa.Text(), nullable=True, comment="Description du motif"),
            sa.PrimaryKeyConstraint('name_en'),
            schema='product_attributes'
        )
        op.create_index('ix_product_attributes_patterns_name_en', 'patterns', ['name_en'], unique=False, schema='product_attributes')
        print("  ✓ Created patterns table")

        # ===== 2. INSÉRER LES 20 PATTERNS =====
        for name_en, name_fr in PATTERNS_DATA:
            connection.execute(
                sa.text(
                    "INSERT INTO product_attributes.patterns (name_en, name_fr) VALUES (:name_en, :name_fr)"
                ),
                {"name_en": name_en, "name_fr": name_fr}
            )
        print(f"  ✓ Inserted {len(PATTERNS_DATA)} patterns into product_attributes.patterns")
    else:
        print("  ⏭️  Patterns table already exists, skipping creation")

    # ===== 3. AJOUTER LA COLONNE pattern DANS template_tenant.products (SI ELLE N'EXISTE PAS) =====
    column_exists = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns
            WHERE table_schema = 'template_tenant'
            AND table_name = 'products'
            AND column_name = 'pattern'
        )
    """)).scalar()

    if not column_exists:
        op.add_column(
            'products',
            sa.Column('pattern', sa.String(length=100), nullable=True, comment="Motif (FK product_attributes.patterns)"),
            schema='template_tenant'
        )
        op.create_index(
            'ix_template_tenant_products_pattern',
            'products',
            ['pattern'],
            unique=False,
            schema='template_tenant'
        )
        print("  ✓ Added pattern column to template_tenant.products")
    else:
        print("  ⏭️  Pattern column already exists in template_tenant.products, skipping")

    # ===== 4. AJOUTER LA COLONNE pattern DANS TOUS LES SCHEMAS USER EXISTANTS =====
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
                AND column_name = 'pattern'
            )
        """)).scalar()

        if not column_exists:
            # Ajouter la colonne pattern
            op.add_column(
                'products',
                sa.Column('pattern', sa.String(length=100), nullable=True, comment="Motif (FK product_attributes.patterns)"),
                schema=schema_name
            )
            # Créer l'index
            op.create_index(
                f'ix_{schema_name}_products_pattern',
                'products',
                ['pattern'],
                unique=False,
                schema=schema_name
            )
            print(f"  ✓ Added pattern column to {schema_name}.products")
        else:
            print(f"  ⏭️  Pattern column already exists in {schema_name}.products, skipping")


def downgrade() -> None:
    """
    Supprime la colonne pattern et la table patterns.
    """

    # ===== 1. SUPPRIMER LA COLONNE pattern DES SCHEMAS USER EXISTANTS =====
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
                AND indexname = 'ix_{schema_name}_products_pattern'
            )
        """)).scalar()

        if index_exists:
            op.drop_index(f'ix_{schema_name}_products_pattern', table_name='products', schema=schema_name)

        # Vérifier si la colonne existe avant de la supprimer
        column_exists = connection.execute(sa.text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_schema = '{schema_name}'
                AND table_name = 'products'
                AND column_name = 'pattern'
            )
        """)).scalar()

        if column_exists:
            op.drop_column('products', 'pattern', schema=schema_name)

    # ===== 2. SUPPRIMER LA COLONNE pattern DE template_tenant.products =====
    column_exists = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns
            WHERE table_schema = 'template_tenant'
            AND table_name = 'products'
            AND column_name = 'pattern'
        )
    """)).scalar()

    if column_exists:
        op.drop_index('ix_template_tenant_products_pattern', table_name='products', schema='template_tenant')
        op.drop_column('products', 'pattern', schema='template_tenant')

    # ===== 3. SUPPRIMER LA TABLE patterns =====
    table_exists = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'product_attributes'
            AND table_name = 'patterns'
        )
    """)).scalar()

    if table_exists:
        op.drop_index('ix_product_attributes_patterns_name_en', table_name='patterns', schema='product_attributes')
        op.drop_table('patterns', schema='product_attributes')
