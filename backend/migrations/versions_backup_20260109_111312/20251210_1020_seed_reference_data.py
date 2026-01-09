"""seed_reference_data

Revision ID: a1b2c3d4e5f6
Revises: 8f9e5a3c1b2d
Create Date: 2025-12-10 10:20:00.000000+01:00

IMPORTANT: Cette migration seed les données de référence essentielles.
Ces données sont nécessaires pour le bon fonctionnement de l'application.

Données créées:
1. subscription_quotas (FREE, STARTER, PRO, ENTERPRISE)
2. Quelques attributs de base pour les tests (brands, categories, colors, conditions, sizes)

NOTE: Les données complètes d'attributs (toutes les marques, toutes les catégories, etc.)
seront chargées séparément via scripts/seed_product_attributes.py

Author: Claude
Date: 2025-12-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '8f9e5a3c1b2d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Seed les données de référence essentielles.
    """

    # ===== 1. SUBSCRIPTION QUOTAS =====
    print("📦 Seeding subscription quotas...")

    subscription_quotas = table('subscription_quotas',
        column('id', sa.Integer),
        column('tier', sa.String),
        column('max_products', sa.Integer),
        column('max_platforms', sa.Integer),
        column('ai_credits_monthly', sa.Integer),
        schema='public'
    )

    op.bulk_insert(subscription_quotas, [
        {
            'id': 1,
            'tier': 'FREE',
            'max_products': 30,
            'max_platforms': 2,
            'ai_credits_monthly': 15
        },
        {
            'id': 2,
            'tier': 'STARTER',
            'max_products': 150,
            'max_platforms': 3,
            'ai_credits_monthly': 75
        },
        {
            'id': 3,
            'tier': 'PRO',
            'max_products': 500,
            'max_platforms': 5,
            'ai_credits_monthly': 250
        },
        {
            'id': 4,
            'tier': 'ENTERPRISE',
            'max_products': 999999,
            'max_platforms': 999999,
            'ai_credits_monthly': 999999
        }
    ])

    print("✅ Subscription quotas seeded (4 tiers)")

    # ===== 2. BASIC PRODUCT ATTRIBUTES (pour tests) =====
    print("📦 Seeding basic product attributes for tests...")

    # Brands
    brands = table('brands',
        column('name', sa.String),
        column('name_fr', sa.String),
        schema='product_attributes'
    )

    op.bulk_insert(brands, [
        {'name': 'Nike', 'name_fr': 'Nike'},
        {'name': 'Adidas', 'name_fr': 'Adidas'},
        {'name': 'Zara', 'name_fr': 'Zara'},
        {'name': 'H&M', 'name_fr': 'H&M'},
        {'name': 'Uniqlo', 'name_fr': 'Uniqlo'},
    ])

    # Categories
    categories = table('categories',
        column('name_en', sa.String),
        column('name_fr', sa.String),
        column('parent_category', sa.String),
        schema='product_attributes'
    )

    op.bulk_insert(categories, [
        {'name_en': 'Clothing', 'name_fr': 'Vêtements', 'parent_category': None},
        {'name_en': 'Shoes', 'name_fr': 'Chaussures', 'parent_category': None},
        {'name_en': 'T-Shirts', 'name_fr': 'T-shirts', 'parent_category': 'Clothing'},
        {'name_en': 'Jeans', 'name_fr': 'Jeans', 'parent_category': 'Clothing'},
        {'name_en': 'Jackets', 'name_fr': 'Vestes', 'parent_category': 'Clothing'},
    ])

    # Colors
    colors = table('colors',
        column('name_en', sa.String),
        column('name_fr', sa.String),
        column('hex_code', sa.String),
        schema='product_attributes'
    )

    op.bulk_insert(colors, [
        {'name_en': 'Black', 'name_fr': 'Noir', 'hex_code': '#000000'},
        {'name_en': 'White', 'name_fr': 'Blanc', 'hex_code': '#FFFFFF'},
        {'name_en': 'Blue', 'name_fr': 'Bleu', 'hex_code': '#0000FF'},
        {'name_en': 'Red', 'name_fr': 'Rouge', 'hex_code': '#FF0000'},
        {'name_en': 'Green', 'name_fr': 'Vert', 'hex_code': '#00FF00'},
    ])

    # Conditions
    conditions = table('conditions',
        column('name_en', sa.String),
        column('name_fr', sa.String),
        schema='product_attributes'
    )

    op.bulk_insert(conditions, [
        {'name_en': 'New with tags', 'name_fr': 'Neuf avec étiquette'},
        {'name_en': 'New without tags', 'name_fr': 'Neuf sans étiquette'},
        {'name_en': 'Very good condition', 'name_fr': 'Très bon état'},
        {'name_en': 'Good condition', 'name_fr': 'Bon état'},
        {'name_en': 'Satisfactory', 'name_fr': 'Satisfaisant'},
    ])

    # Sizes
    sizes = table('sizes',
        column('name_en', sa.String),
        column('name_fr', sa.String),
        schema='product_attributes'
    )

    op.bulk_insert(sizes, [
        {'name_en': 'XS', 'name_fr': 'XS'},
        {'name_en': 'S', 'name_fr': 'S'},
        {'name_en': 'M', 'name_fr': 'M'},
        {'name_en': 'L', 'name_fr': 'L'},
        {'name_en': 'XL', 'name_fr': 'XL'},
    ])

    # Materials
    materials = table('materials',
        column('name_en', sa.String),
        column('name_fr', sa.String),
        schema='product_attributes'
    )

    op.bulk_insert(materials, [
        {'name_en': 'Cotton', 'name_fr': 'Coton'},
        {'name_en': 'Polyester', 'name_fr': 'Polyester'},
        {'name_en': 'Wool', 'name_fr': 'Laine'},
        {'name_en': 'Leather', 'name_fr': 'Cuir'},
        {'name_en': 'Denim', 'name_fr': 'Denim'},
    ])

    # Genders
    genders = table('genders',
        column('name_en', sa.String),
        column('name_fr', sa.String),
        schema='product_attributes'
    )

    op.bulk_insert(genders, [
        {'name_en': 'Men', 'name_fr': 'Homme'},
        {'name_en': 'Women', 'name_fr': 'Femme'},
        {'name_en': 'Unisex', 'name_fr': 'Unisexe'},
    ])

    # Seasons
    seasons = table('seasons',
        column('name_en', sa.String),
        column('name_fr', sa.String),
        schema='product_attributes'
    )

    op.bulk_insert(seasons, [
        {'name_en': 'Spring', 'name_fr': 'Printemps'},
        {'name_en': 'Summer', 'name_fr': 'Été'},
        {'name_en': 'Autumn', 'name_fr': 'Automne'},
        {'name_en': 'Winter', 'name_fr': 'Hiver'},
        {'name_en': 'All seasons', 'name_fr': 'Toutes saisons'},
    ])

    print("✅ Basic product attributes seeded")


def downgrade() -> None:
    """
    Supprime les données de référence seeded.
    """

    # Supprimer dans l'ordre inverse
    print("🗑️  Removing seeded data...")

    # Supprimer subscription_quotas
    op.execute("DELETE FROM public.subscription_quotas")

    # Supprimer product attributes
    op.execute("DELETE FROM product_attributes.seasons")
    op.execute("DELETE FROM product_attributes.genders")
    op.execute("DELETE FROM product_attributes.materials")
    op.execute("DELETE FROM product_attributes.sizes")
    op.execute("DELETE FROM product_attributes.conditions")
    op.execute("DELETE FROM product_attributes.colors")
    op.execute("DELETE FROM product_attributes.categories")
    op.execute("DELETE FROM product_attributes.brands")

    print("✅ Seeded data removed")
