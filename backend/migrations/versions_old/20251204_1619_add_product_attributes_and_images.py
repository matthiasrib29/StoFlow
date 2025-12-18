"""add_product_attributes_and_images

Migration pour ajouter:
1. Tables d'attributs dans schema public (brands, colors, conditions, etc.)
2. Nouvelles colonnes Product (26+ attributs)
3. Table product_images
4. Foreign keys cross-schema
5. Seed data de base

⚠️ IMPORTANT: Cette migration s'applique à TOUS les schemas tenant existants!

Revision ID: d59ff27961f4
Revises: bcd3b2f021aa
Create Date: 2025-12-04 16:19:11.788225+01:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = "d59ff27961f4"
down_revision: Union[str, None] = "bcd3b2f021aa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Applique les changements:
    1. Crée les tables d'attributs dans public
    2. Seed les données de base
    3. Pour chaque tenant, ajoute colonnes et tables
    """
    conn = op.get_bind()

    # ===== ÉTAPE 1: CRÉER TABLES D'ATTRIBUTS DANS PUBLIC =====
    print("Creating attribute tables in public schema...")

    # Table: brands
    op.create_table(
        "brands",
        sa.Column("name", sa.String(100), primary_key=True, nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        schema="public",
    )

    # Table: colors (multilingue)
    op.create_table(
        "colors",
        sa.Column("name_en", sa.String(100), primary_key=True, nullable=False),
        sa.Column("name_fr", sa.String(100), nullable=True),
        sa.Column("name_de", sa.String(100), nullable=True),
        sa.Column("name_it", sa.String(100), nullable=True),
        sa.Column("name_es", sa.String(100), nullable=True),
        schema="public",
    )

    # Table: conditions
    op.create_table(
        "conditions",
        sa.Column("name", sa.String(100), primary_key=True, nullable=False),
        sa.Column("description_fr", sa.String(255), nullable=True),
        sa.Column("description_en", sa.String(255), nullable=True),
        schema="public",
    )

    # Table: sizes
    op.create_table(
        "sizes",
        sa.Column("name", sa.String(100), primary_key=True, nullable=False),
        schema="public",
    )

    # Table: materials (multilingue)
    op.create_table(
        "materials",
        sa.Column("name_en", sa.String(100), primary_key=True, nullable=False),
        sa.Column("name_fr", sa.String(100), nullable=True),
        sa.Column("name_de", sa.String(100), nullable=True),
        sa.Column("name_it", sa.String(100), nullable=True),
        sa.Column("name_es", sa.String(100), nullable=True),
        schema="public",
    )

    # Table: fits (multilingue)
    op.create_table(
        "fits",
        sa.Column("name_en", sa.String(100), primary_key=True, nullable=False),
        sa.Column("name_fr", sa.String(100), nullable=True),
        sa.Column("name_de", sa.String(100), nullable=True),
        sa.Column("name_it", sa.String(100), nullable=True),
        sa.Column("name_es", sa.String(100), nullable=True),
        schema="public",
    )

    # Table: genders (multilingue)
    op.create_table(
        "genders",
        sa.Column("name_en", sa.String(100), primary_key=True, nullable=False),
        sa.Column("name_fr", sa.String(100), nullable=True),
        sa.Column("name_de", sa.String(100), nullable=True),
        sa.Column("name_it", sa.String(100), nullable=True),
        sa.Column("name_es", sa.String(100), nullable=True),
        schema="public",
    )

    # Table: seasons (multilingue)
    op.create_table(
        "seasons",
        sa.Column("name_en", sa.String(100), primary_key=True, nullable=False),
        sa.Column("name_fr", sa.String(100), nullable=True),
        sa.Column("name_de", sa.String(100), nullable=True),
        sa.Column("name_it", sa.String(100), nullable=True),
        sa.Column("name_es", sa.String(100), nullable=True),
        schema="public",
    )

    # Table: categories (avec hiérarchie)
    op.create_table(
        "categories",
        sa.Column("name_en", sa.String(100), primary_key=True, nullable=False),
        sa.Column(
            "parent_category",
            sa.String(100),
            sa.ForeignKey("public.categories.name_en", onupdate="CASCADE", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("name_fr", sa.String(255), nullable=True),
        sa.Column("name_de", sa.String(255), nullable=True),
        sa.Column("name_it", sa.String(255), nullable=True),
        sa.Column("name_es", sa.String(255), nullable=True),
        schema="public",
    )
    op.create_index(
        "idx_categories_parent", "categories", ["parent_category"], schema="public", unique=False
    )

    # ===== ÉTAPE 2: SEED DONNÉES DE BASE =====
    print("Seeding base data...")

    # Seed conditions
    conn.execute(
        text(
            """
        INSERT INTO public.conditions (name, description_en, description_fr) VALUES
        ('NEW', 'Brand new with tags', 'Neuf avec étiquettes'),
        ('EXCELLENT', 'Excellent condition, barely worn', 'Excellent état, à peine porté'),
        ('GOOD', 'Good condition, normal wear', 'Bon état, usure normale'),
        ('FAIR', 'Fair condition, visible wear', 'État correct, usure visible'),
        ('POOR', 'Poor condition, heavy wear', 'Mauvais état, forte usure')
        """
        )
    )

    # Seed colors (exemples de base)
    conn.execute(
        text(
            """
        INSERT INTO public.colors (name_en, name_fr) VALUES
        ('Black', 'Noir'),
        ('White', 'Blanc'),
        ('Blue', 'Bleu'),
        ('Red', 'Rouge'),
        ('Green', 'Vert'),
        ('Yellow', 'Jaune'),
        ('Gray', 'Gris'),
        ('Brown', 'Marron'),
        ('Beige', 'Beige'),
        ('Pink', 'Rose')
        """
        )
    )

    # Seed categories (hiérarchie simple)
    conn.execute(
        text(
            """
        INSERT INTO public.categories (name_en, parent_category, name_fr) VALUES
        ('Clothing', NULL, 'Vêtements'),
        ('Jeans', 'Clothing', 'Jeans'),
        ('T-Shirts', 'Clothing', 'T-Shirts'),
        ('Jackets', 'Clothing', 'Vestes'),
        ('Dresses', 'Clothing', 'Robes'),
        ('Accessories', NULL, 'Accessoires'),
        ('Shoes', NULL, 'Chaussures'),
        ('Bags', NULL, 'Sacs')
        """
        )
    )

    # Seed sizes (exemples)
    conn.execute(
        text(
            """
        INSERT INTO public.sizes (name) VALUES
        ('XS'), ('S'), ('M'), ('L'), ('XL'), ('XXL'),
        ('W28L32'), ('W30L32'), ('W32L32'), ('W32L34'), ('W34L34'),
        ('36'), ('38'), ('40'), ('42'), ('44'), ('46')
        """
        )
    )

    # Seed fits
    conn.execute(
        text(
            """
        INSERT INTO public.fits (name_en, name_fr) VALUES
        ('Slim', 'Ajusté'),
        ('Regular', 'Classique'),
        ('Relaxed', 'Ample'),
        ('Oversized', 'Oversize')
        """
        )
    )

    # Seed genders
    conn.execute(
        text(
            """
        INSERT INTO public.genders (name_en, name_fr) VALUES
        ('Men', 'Homme'),
        ('Women', 'Femme'),
        ('Unisex', 'Mixte'),
        ('Kids', 'Enfant')
        """
        )
    )

    # Seed seasons
    conn.execute(
        text(
            """
        INSERT INTO public.seasons (name_en, name_fr) VALUES
        ('Spring', 'Printemps'),
        ('Summer', 'Été'),
        ('Fall', 'Automne'),
        ('Winter', 'Hiver'),
        ('All-Season', 'Toute-Saison')
        """
        )
    )

    # Seed materials
    conn.execute(
        text(
            """
        INSERT INTO public.materials (name_en, name_fr) VALUES
        ('Cotton', 'Coton'),
        ('Polyester', 'Polyester'),
        ('Denim', 'Denim'),
        ('Leather', 'Cuir'),
        ('Wool', 'Laine'),
        ('Silk', 'Soie'),
        ('Linen', 'Lin')
        """
        )
    )

    # Seed brands (exemples populaires)
    conn.execute(
        text(
            """
        INSERT INTO public.brands (name) VALUES
        ('Levi''s'), ('Nike'), ('Adidas'), ('Zara'), ('H&M'),
        ('Uniqlo'), ('Gap'), ('Tommy Hilfiger'), ('Calvin Klein'), ('Ralph Lauren')
        """
        )
    )

    # ===== ÉTAPE 3: APPLIQUER CHANGEMENTS À TOUS LES SCHEMAS TENANT =====
    print("Applying changes to all tenant schemas...")

    # Récupérer tous les tenants existants
    tenants = conn.execute(text("SELECT id FROM public.tenants")).fetchall()
    print(f"Found {len(tenants)} tenant(s)")

    for tenant in tenants:
        tenant_id = tenant[0]
        schema_name = f"client_{tenant_id}"

        # Vérifier si le schema existe et contient la table products
        schema_exists = conn.execute(
            text(f"""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.schemata
                    WHERE schema_name = '{schema_name}'
                )
            """)
        ).scalar()

        if not schema_exists:
            print(f"  Skipping {schema_name} (schema does not exist)")
            continue

        table_exists = conn.execute(
            text(f"""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = '{schema_name}' AND table_name = 'products'
                )
            """)
        ).scalar()

        if not table_exists:
            print(f"  Skipping {schema_name} (products table does not exist)")
            continue

        print(f"  Processing schema: {schema_name}")

        # ===== A. AJOUTER COLONNES À PRODUCTS =====

        # Foreign keys vers public
        op.add_column(
            "products",
            sa.Column("label_size", sa.String(100), nullable=True),
            schema=schema_name,
        )
        op.add_column("products", sa.Column("color", sa.String(100), nullable=True), schema=schema_name)
        op.add_column(
            "products",
            sa.Column("material", sa.String(100), nullable=True),
            schema=schema_name,
        )
        op.add_column("products", sa.Column("fit", sa.String(100), nullable=True), schema=schema_name)
        op.add_column("products", sa.Column("gender", sa.String(100), nullable=True), schema=schema_name)
        op.add_column("products", sa.Column("season", sa.String(100), nullable=True), schema=schema_name)

        # Attributs supplémentaires (sans FK)
        op.add_column(
            "products",
            sa.Column("condition_sup", sa.String(255), nullable=True),
            schema=schema_name,
        )
        op.add_column("products", sa.Column("rise", sa.String(100), nullable=True), schema=schema_name)
        op.add_column("products", sa.Column("closure", sa.String(100), nullable=True), schema=schema_name)
        op.add_column(
            "products",
            sa.Column("sleeve_length", sa.String(100), nullable=True),
            schema=schema_name,
        )
        op.add_column("products", sa.Column("origin", sa.String(100), nullable=True), schema=schema_name)
        op.add_column("products", sa.Column("decade", sa.String(100), nullable=True), schema=schema_name)
        op.add_column("products", sa.Column("trend", sa.String(100), nullable=True), schema=schema_name)
        op.add_column("products", sa.Column("name_sup", sa.String(100), nullable=True), schema=schema_name)
        op.add_column("products", sa.Column("location", sa.String(100), nullable=True), schema=schema_name)
        op.add_column("products", sa.Column("model", sa.String(100), nullable=True), schema=schema_name)

        # Dimensions (measurements)
        op.add_column("products", sa.Column("dim1", sa.Integer(), nullable=True), schema=schema_name)
        op.add_column("products", sa.Column("dim2", sa.Integer(), nullable=True), schema=schema_name)
        op.add_column("products", sa.Column("dim3", sa.Integer(), nullable=True), schema=schema_name)
        op.add_column("products", sa.Column("dim4", sa.Integer(), nullable=True), schema=schema_name)
        op.add_column("products", sa.Column("dim5", sa.Integer(), nullable=True), schema=schema_name)
        op.add_column("products", sa.Column("dim6", sa.Integer(), nullable=True), schema=schema_name)

        # Stock
        op.add_column(
            "products",
            sa.Column("stock_quantity", sa.Integer(), nullable=False, server_default="0"),
            schema=schema_name,
        )

        # Soft delete
        op.add_column(
            "products",
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            schema=schema_name,
        )

        # ===== B. MODIFIER COLONNES EXISTANTES (TYPES) =====
        # Agrandir brand pour correspondre à public.brands (String(100))
        with op.batch_alter_table("products", schema=schema_name) as batch_op:
            batch_op.alter_column(
                "brand", type_=sa.String(100), existing_type=sa.String(255), nullable=True
            )
            batch_op.alter_column(
                "condition", type_=sa.String(100), existing_type=sa.String(50), nullable=False
            )

        # ===== C. CRÉER FOREIGN KEYS CROSS-SCHEMA =====
        op.create_foreign_key(
            "fk_products_brand",
            "products",
            "brands",
            ["brand"],
            ["name"],
            source_schema=schema_name,
            referent_schema="public",
            onupdate="CASCADE",
            ondelete="SET NULL",
        )
        op.create_foreign_key(
            "fk_products_category",
            "products",
            "categories",
            ["category"],
            ["name_en"],
            source_schema=schema_name,
            referent_schema="public",
            onupdate="CASCADE",
            ondelete="RESTRICT",
        )
        op.create_foreign_key(
            "fk_products_condition",
            "products",
            "conditions",
            ["condition"],
            ["name"],
            source_schema=schema_name,
            referent_schema="public",
            onupdate="CASCADE",
            ondelete="RESTRICT",
        )
        op.create_foreign_key(
            "fk_products_size",
            "products",
            "sizes",
            ["label_size"],
            ["name"],
            source_schema=schema_name,
            referent_schema="public",
            onupdate="CASCADE",
            ondelete="SET NULL",
        )
        op.create_foreign_key(
            "fk_products_color",
            "products",
            "colors",
            ["color"],
            ["name_en"],
            source_schema=schema_name,
            referent_schema="public",
            onupdate="CASCADE",
            ondelete="SET NULL",
        )
        op.create_foreign_key(
            "fk_products_material",
            "products",
            "materials",
            ["material"],
            ["name_en"],
            source_schema=schema_name,
            referent_schema="public",
            onupdate="CASCADE",
            ondelete="SET NULL",
        )
        op.create_foreign_key(
            "fk_products_fit",
            "products",
            "fits",
            ["fit"],
            ["name_en"],
            source_schema=schema_name,
            referent_schema="public",
            onupdate="CASCADE",
            ondelete="SET NULL",
        )
        op.create_foreign_key(
            "fk_products_gender",
            "products",
            "genders",
            ["gender"],
            ["name_en"],
            source_schema=schema_name,
            referent_schema="public",
            onupdate="CASCADE",
            ondelete="SET NULL",
        )
        op.create_foreign_key(
            "fk_products_season",
            "products",
            "seasons",
            ["season"],
            ["name_en"],
            source_schema=schema_name,
            referent_schema="public",
            onupdate="CASCADE",
            ondelete="SET NULL",
        )

        # ===== D. CRÉER INDEXES SUPPLÉMENTAIRES =====
        op.create_index(
            "idx_product_color", "products", ["color"], schema=schema_name, unique=False
        )
        op.create_index(
            "idx_product_deleted_at", "products", ["deleted_at"], schema=schema_name, unique=False
        )

        # ===== E. CRÉER TABLE PRODUCT_IMAGES =====
        op.create_table(
            "product_images",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column(
                "product_id",
                sa.Integer(),
                sa.ForeignKey(f"{schema_name}.products.id", ondelete="CASCADE"),
                nullable=False,
                index=True,
            ),
            sa.Column("image_path", sa.String(1000), nullable=False),
            sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            schema=schema_name,
        )
        op.create_index(
            "idx_product_image_product_id_order",
            "product_images",
            ["product_id", "display_order"],
            schema=schema_name,
            unique=False,
        )

        # ===== F. CRÉER CHECK CONSTRAINT =====
        conn.execute(
            text(
                f"""
            ALTER TABLE {schema_name}.products
            ADD CONSTRAINT check_stock_positive CHECK (stock_quantity >= 0)
        """
            )
        )

    print("✅ Migration completed successfully!")


def downgrade() -> None:
    """
    Rollback des changements.
    ⚠️ ATTENTION: Supprime les données!
    """
    conn = op.get_bind()

    # Récupérer tous les tenants
    tenants = conn.execute(text("SELECT id FROM public.tenants")).fetchall()

    # Pour chaque tenant, supprimer les changements
    for tenant in tenants:
        tenant_id = tenant[0]
        schema_name = f"client_{tenant_id}"

        # Supprimer table product_images
        op.drop_table("product_images", schema=schema_name)

        # Supprimer foreign keys
        op.drop_constraint("fk_products_brand", "products", schema=schema_name, type_="foreignkey")
        op.drop_constraint("fk_products_category", "products", schema=schema_name, type_="foreignkey")
        op.drop_constraint("fk_products_condition", "products", schema=schema_name, type_="foreignkey")
        op.drop_constraint("fk_products_size", "products", schema=schema_name, type_="foreignkey")
        op.drop_constraint("fk_products_color", "products", schema=schema_name, type_="foreignkey")
        op.drop_constraint("fk_products_material", "products", schema=schema_name, type_="foreignkey")
        op.drop_constraint("fk_products_fit", "products", schema=schema_name, type_="foreignkey")
        op.drop_constraint("fk_products_gender", "products", schema=schema_name, type_="foreignkey")
        op.drop_constraint("fk_products_season", "products", schema=schema_name, type_="foreignkey")

        # Supprimer indexes
        op.drop_index("idx_product_color", "products", schema=schema_name)
        op.drop_index("idx_product_deleted_at", "products", schema=schema_name)

        # Supprimer check constraint
        conn.execute(
            text(f"ALTER TABLE {schema_name}.products DROP CONSTRAINT check_stock_positive")
        )

        # Supprimer colonnes
        op.drop_column("products", "deleted_at", schema=schema_name)
        op.drop_column("products", "stock_quantity", schema=schema_name)
        op.drop_column("products", "dim6", schema=schema_name)
        op.drop_column("products", "dim5", schema=schema_name)
        op.drop_column("products", "dim4", schema=schema_name)
        op.drop_column("products", "dim3", schema=schema_name)
        op.drop_column("products", "dim2", schema=schema_name)
        op.drop_column("products", "dim1", schema=schema_name)
        op.drop_column("products", "model", schema=schema_name)
        op.drop_column("products", "location", schema=schema_name)
        op.drop_column("products", "name_sup", schema=schema_name)
        op.drop_column("products", "trend", schema=schema_name)
        op.drop_column("products", "decade", schema=schema_name)
        op.drop_column("products", "origin", schema=schema_name)
        op.drop_column("products", "sleeve_length", schema=schema_name)
        op.drop_column("products", "closure", schema=schema_name)
        op.drop_column("products", "rise", schema=schema_name)
        op.drop_column("products", "condition_sup", schema=schema_name)
        op.drop_column("products", "season", schema=schema_name)
        op.drop_column("products", "gender", schema=schema_name)
        op.drop_column("products", "fit", schema=schema_name)
        op.drop_column("products", "material", schema=schema_name)
        op.drop_column("products", "color", schema=schema_name)
        op.drop_column("products", "label_size", schema=schema_name)

    # Supprimer tables d'attributs dans public
    op.drop_table("categories", schema="public")
    op.drop_table("seasons", schema="public")
    op.drop_table("genders", schema="public")
    op.drop_table("fits", schema="public")
    op.drop_table("materials", schema="public")
    op.drop_table("sizes", schema="public")
    op.drop_table("conditions", schema="public")
    op.drop_table("colors", schema="public")
    op.drop_table("brands", schema="public")
