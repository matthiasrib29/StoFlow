"""add_sports_table_and_product_sport_column

Revision ID: c7c1128b7a30
Revises: ea3f385f012e
Create Date: 2025-12-11 16:58:17.968315+01:00

Cette migration ajoute la table sports dans le schema product_attributes
et ajoute la colonne sport dans la table products.

Tables créées:
- product_attributes.sports (29 sports pré-remplis)

Colonnes ajoutées:
- sport (String(100), nullable) dans template_tenant.products et tous les user schemas

Author: Claude
Date: 2025-12-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7c1128b7a30'
down_revision: Union[str, None] = 'ea3f385f012e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ===== DATA: 29 SPORTS =====
SPORTS_DATA = [
    ("Baseball", "Baseball"),
    ("American Football", "Football américain"),
    ("Football/Soccer", "Football"),
    ("Basketball", "Basketball"),
    ("Hockey", "Hockey"),
    ("Rugby", "Rugby"),
    ("Cycling", "Cyclisme"),
    ("Running", "Course à pied"),
    ("Tennis", "Tennis"),
    ("Ski", "Ski"),
    ("Snowboard", "Snowboard"),
    ("Swimming", "Natation"),
    ("Yoga", "Yoga"),
    ("Fitness", "Fitness"),
    ("Boxing", "Boxe"),
    ("Martial Arts", "Arts martiaux"),
    ("Golf", "Golf"),
    ("Volleyball", "Volleyball"),
    ("Surfing", "Surf"),
    ("Skateboarding", "Skateboard"),
    ("Hiking", "Randonnée"),
    ("Climbing", "Escalade"),
    ("Gymnastics", "Gymnastique"),
    ("Dance", "Danse"),
    ("CrossFit", "CrossFit"),
    ("Pilates", "Pilates"),
    ("Motorsport", "Sport automobile"),
    ("Equestrian", "Équitation"),
]


def upgrade() -> None:
    """
    Ajoute la table sports et la colonne sport dans products.
    """
    connection = op.get_bind()

    # ===== 1. CRÉER LA TABLE sports DANS product_attributes (SI ELLE N'EXISTE PAS) =====
    table_exists = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'product_attributes'
            AND table_name = 'sports'
        )
    """)).scalar()

    if not table_exists:
        op.create_table(
            'sports',
            sa.Column('name_en', sa.String(length=100), nullable=False, comment="Nom du sport (EN)"),
            sa.Column('name_fr', sa.String(length=100), nullable=True, comment="Nom du sport (FR)"),
            sa.Column('description', sa.Text(), nullable=True, comment="Description du sport"),
            sa.PrimaryKeyConstraint('name_en'),
            schema='product_attributes'
        )
        op.create_index('ix_product_attributes_sports_name_en', 'sports', ['name_en'], unique=False, schema='product_attributes')
        print("  ✓ Created sports table")

        # ===== 2. INSÉRER LES 29 SPORTS =====
        for name_en, name_fr in SPORTS_DATA:
            connection.execute(
                sa.text(
                    "INSERT INTO product_attributes.sports (name_en, name_fr) VALUES (:name_en, :name_fr)"
                ),
                {"name_en": name_en, "name_fr": name_fr}
            )
        print(f"  ✓ Inserted {len(SPORTS_DATA)} sports into product_attributes.sports")
    else:
        print("  ⏭️  Sports table already exists, skipping creation")

    # ===== 3. AJOUTER LA COLONNE sport DANS template_tenant.products (SI ELLE N'EXISTE PAS) =====
    column_exists = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns
            WHERE table_schema = 'template_tenant'
            AND table_name = 'products'
            AND column_name = 'sport'
        )
    """)).scalar()

    if not column_exists:
        op.add_column(
            'products',
            sa.Column('sport', sa.String(length=100), nullable=True, comment="Sport (FK product_attributes.sports)"),
            schema='template_tenant'
        )
        op.create_index(
            'ix_template_tenant_products_sport',
            'products',
            ['sport'],
            unique=False,
            schema='template_tenant'
        )
        print("  ✓ Added sport column to template_tenant.products")
    else:
        print("  ⏭️  Sport column already exists in template_tenant.products, skipping")

    # ===== 4. AJOUTER LA COLONNE sport DANS TOUS LES SCHEMAS USER EXISTANTS =====
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
                AND column_name = 'sport'
            )
        """)).scalar()

        if not column_exists:
            # Ajouter la colonne sport
            op.add_column(
                'products',
                sa.Column('sport', sa.String(length=100), nullable=True, comment="Sport (FK product_attributes.sports)"),
                schema=schema_name
            )
            # Créer l'index
            op.create_index(
                f'ix_{schema_name}_products_sport',
                'products',
                ['sport'],
                unique=False,
                schema=schema_name
            )
            print(f"  ✓ Added sport column to {schema_name}.products")
        else:
            print(f"  ⏭️  Sport column already exists in {schema_name}.products, skipping")


def downgrade() -> None:
    """
    Supprime la colonne sport et la table sports.
    """

    # ===== 1. SUPPRIMER LA COLONNE sport DES SCHEMAS USER EXISTANTS =====
    connection = op.get_bind()
    result = connection.execute(sa.text(
        "SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'user_%'"
    ))
    user_schemas = [row[0] for row in result]

    for schema_name in user_schemas:
        op.drop_index(f'ix_{schema_name}_products_sport', table_name='products', schema=schema_name)
        op.drop_column('products', 'sport', schema=schema_name)

    # ===== 2. SUPPRIMER LA COLONNE sport DE template_tenant.products =====
    op.drop_index('ix_template_tenant_products_sport', table_name='products', schema='template_tenant')
    op.drop_column('products', 'sport', schema='template_tenant')

    # ===== 3. SUPPRIMER LA TABLE sports =====
    op.drop_index('ix_product_attributes_sports_name_en', table_name='sports', schema='product_attributes')
    op.drop_table('sports', schema='product_attributes')
