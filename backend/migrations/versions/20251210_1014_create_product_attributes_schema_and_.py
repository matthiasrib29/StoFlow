"""create_product_attributes_schema_and_tables

Revision ID: c5a428da8142
Revises: 46aad9f85d14
Create Date: 2025-12-10 10:14:38.628036+01:00

IMPORTANT: Cette migration crée le schema product_attributes et toutes les tables d'attributs.
Ces tables sont partagées entre tous les tenants (users) pour éviter la duplication de données.

Tables créées:
- brands (marques)
- categories (catégories avec hiérarchie)
- colors (couleurs multilingues)
- conditions (états du produit)
- condition_sup (états supplémentaires)
- closures (types de fermeture)
- decades (décennies pour vintage)
- fits (coupes)
- genders (genres)
- materials (matières)
- origins (origines/provenances)
- rises (hauteurs de taille pour pantalons)
- seasons (saisons)
- sizes (tailles)
- sleeve_lengths (longueurs de manche)
- trends (tendances/styles)
- unique_features (caractéristiques uniques)

Author: Claude
Date: 2025-12-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c5a428da8142'
down_revision: Union[str, None] = '46aad9f85d14'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Crée le schema product_attributes et toutes les tables d'attributs.
    """

    # ===== 1. CRÉER LE SCHEMA product_attributes =====
    op.execute("CREATE SCHEMA IF NOT EXISTS product_attributes")

    # ===== 2. TABLE brands =====
    op.create_table(
        'brands',
        sa.Column('name', sa.String(length=100), nullable=False, comment="Nom de la marque (EN)"),
        sa.Column('name_fr', sa.String(length=100), nullable=True, comment="Nom de la marque (FR)"),
        sa.Column('description', sa.Text(), nullable=True, comment="Description de la marque"),
        sa.Column('vinted_id', sa.Text(), nullable=True, comment="ID Vinted pour intégration marketplace"),
        sa.Column('monitoring', sa.Boolean(), nullable=False, server_default='false', comment="Marque surveillée (tracking spécial)"),
        sa.Column('sector_jeans', sa.String(length=20), nullable=True, comment="Segment de marché pour les jeans: BUDGET, STANDARD, HYPE, PREMIUM, ULTRA PREMIUM"),
        sa.Column('sector_jacket', sa.String(length=20), nullable=True, comment="Segment de marché pour les vestes: BUDGET, STANDARD, HYPE, PREMIUM, ULTRA PREMIUM"),
        sa.PrimaryKeyConstraint('name'),
        schema='product_attributes'
    )
    op.create_index('ix_product_attributes_brands_name', 'brands', ['name'], unique=False, schema='product_attributes')

    # ===== 3. TABLE categories =====
    op.create_table(
        'categories',
        sa.Column('name_en', sa.String(length=100), nullable=False, comment="Nom de la catégorie (EN)"),
        sa.Column('parent_category', sa.String(length=100), nullable=True, comment="Catégorie parente (self-reference)"),
        sa.Column('name_fr', sa.String(length=255), nullable=True, comment="Nom de la catégorie (FR)"),
        sa.Column('name_de', sa.String(length=255), nullable=True, comment="Nom de la catégorie (DE)"),
        sa.Column('name_it', sa.String(length=255), nullable=True, comment="Nom de la catégorie (IT)"),
        sa.Column('name_es', sa.String(length=255), nullable=True, comment="Nom de la catégorie (ES)"),
        sa.Column('name_nl', sa.String(length=255), nullable=True, comment="Nom de la catégorie (NL)"),
        sa.Column('name_pl', sa.String(length=255), nullable=True, comment="Nom de la catégorie (PL)"),
        sa.Column('default_gender', sa.String(length=20), nullable=True, comment="Genre par défaut: male, female, unisex"),
        sa.ForeignKeyConstraint(['parent_category'], ['product_attributes.categories.name_en'], onupdate='CASCADE', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('name_en'),
        schema='product_attributes'
    )
    op.create_index('ix_product_attributes_categories_name_en', 'categories', ['name_en'], unique=False, schema='product_attributes')
    op.create_index('ix_product_attributes_categories_parent_category', 'categories', ['parent_category'], unique=False, schema='product_attributes')

    # ===== 4. TABLE colors =====
    op.create_table(
        'colors',
        sa.Column('name_en', sa.String(length=100), nullable=False, comment="Nom de la couleur (EN)"),
        sa.Column('name_fr', sa.String(length=100), nullable=True, comment="Nom de la couleur (FR)"),
        sa.Column('name_de', sa.String(length=100), nullable=True, comment="Nom de la couleur (DE)"),
        sa.Column('name_it', sa.String(length=100), nullable=True, comment="Nom de la couleur (IT)"),
        sa.Column('name_es', sa.String(length=100), nullable=True, comment="Nom de la couleur (ES)"),
        sa.Column('name_nl', sa.String(length=100), nullable=True, comment="Nom de la couleur (NL)"),
        sa.Column('name_pl', sa.String(length=100), nullable=True, comment="Nom de la couleur (PL)"),
        sa.Column('hex_code', sa.String(length=7), nullable=True, comment="Code couleur hexadécimal (#RRGGBB)"),
        sa.PrimaryKeyConstraint('name_en'),
        schema='product_attributes'
    )
    op.create_index('ix_product_attributes_colors_name_en', 'colors', ['name_en'], unique=False, schema='product_attributes')

    # ===== 5. TABLE conditions =====
    op.create_table(
        'conditions',
        sa.Column('name_en', sa.String(length=100), nullable=False, comment="Nom de l'état (EN)"),
        sa.Column('name_fr', sa.String(length=100), nullable=True, comment="Nom de l'état (FR)"),
        sa.Column('name_de', sa.String(length=100), nullable=True, comment="Nom de l'état (DE)"),
        sa.Column('name_it', sa.String(length=100), nullable=True, comment="Nom de l'état (IT)"),
        sa.Column('name_es', sa.String(length=100), nullable=True, comment="Nom de l'état (ES)"),
        sa.Column('name_nl', sa.String(length=100), nullable=True, comment="Nom de l'état (NL)"),
        sa.Column('name_pl', sa.String(length=100), nullable=True, comment="Nom de l'état (PL)"),
        sa.Column('vinted_id', sa.Integer(), nullable=True, comment="ID condition Vinted"),
        sa.Column('ebay_condition', sa.String(length=50), nullable=True, comment="Condition eBay correspondante"),
        sa.Column('etsy_condition', sa.String(length=50), nullable=True, comment="Condition Etsy correspondante"),
        sa.PrimaryKeyConstraint('name_en'),
        schema='product_attributes'
    )
    op.create_index('ix_product_attributes_conditions_name_en', 'conditions', ['name_en'], unique=False, schema='product_attributes')

    # ===== 6. TABLE condition_sup =====
    op.create_table(
        'condition_sup',
        sa.Column('name_en', sa.String(length=255), nullable=False, comment="Détail d'état supplémentaire (EN)"),
        sa.Column('name_fr', sa.String(length=255), nullable=True, comment="Détail d'état supplémentaire (FR)"),
        sa.Column('name_de', sa.String(length=255), nullable=True, comment="Détail d'état supplémentaire (DE)"),
        sa.Column('name_it', sa.String(length=255), nullable=True, comment="Détail d'état supplémentaire (IT)"),
        sa.Column('name_es', sa.String(length=255), nullable=True, comment="Détail d'état supplémentaire (ES)"),
        sa.Column('name_nl', sa.String(length=255), nullable=True, comment="Détail d'état supplémentaire (NL)"),
        sa.Column('name_pl', sa.String(length=255), nullable=True, comment="Détail d'état supplémentaire (PL)"),
        sa.PrimaryKeyConstraint('name_en'),
        schema='product_attributes'
    )
    op.create_index('ix_product_attributes_condition_sup_name_en', 'condition_sup', ['name_en'], unique=False, schema='product_attributes')

    # ===== 7. TABLE closures =====
    op.create_table(
        'closures',
        sa.Column('name_en', sa.String(length=100), nullable=False, comment="Type de fermeture (EN)"),
        sa.Column('name_fr', sa.String(length=100), nullable=True, comment="Type de fermeture (FR)"),
        sa.Column('name_de', sa.String(length=100), nullable=True, comment="Type de fermeture (DE)"),
        sa.Column('name_it', sa.String(length=100), nullable=True, comment="Type de fermeture (IT)"),
        sa.Column('name_es', sa.String(length=100), nullable=True, comment="Type de fermeture (ES)"),
        sa.Column('name_nl', sa.String(length=100), nullable=True, comment="Type de fermeture (NL)"),
        sa.Column('name_pl', sa.String(length=100), nullable=True, comment="Type de fermeture (PL)"),
        sa.PrimaryKeyConstraint('name_en'),
        schema='product_attributes'
    )
    op.create_index('ix_product_attributes_closures_name_en', 'closures', ['name_en'], unique=False, schema='product_attributes')

    # ===== 8. TABLE decades =====
    op.create_table(
        'decades',
        sa.Column('name_en', sa.String(length=100), nullable=False, comment="Décennie (EN)"),
        sa.Column('name_fr', sa.String(length=100), nullable=True, comment="Décennie (FR)"),
        sa.Column('name_de', sa.String(length=100), nullable=True, comment="Décennie (DE)"),
        sa.Column('name_it', sa.String(length=100), nullable=True, comment="Décennie (IT)"),
        sa.Column('name_es', sa.String(length=100), nullable=True, comment="Décennie (ES)"),
        sa.Column('name_nl', sa.String(length=100), nullable=True, comment="Décennie (NL)"),
        sa.Column('name_pl', sa.String(length=100), nullable=True, comment="Décennie (PL)"),
        sa.PrimaryKeyConstraint('name_en'),
        schema='product_attributes'
    )
    op.create_index('ix_product_attributes_decades_name_en', 'decades', ['name_en'], unique=False, schema='product_attributes')

    # ===== 9. TABLE fits =====
    op.create_table(
        'fits',
        sa.Column('name_en', sa.String(length=100), nullable=False, comment="Coupe (EN)"),
        sa.Column('name_fr', sa.String(length=100), nullable=True, comment="Coupe (FR)"),
        sa.Column('name_de', sa.String(length=100), nullable=True, comment="Coupe (DE)"),
        sa.Column('name_it', sa.String(length=100), nullable=True, comment="Coupe (IT)"),
        sa.Column('name_es', sa.String(length=100), nullable=True, comment="Coupe (ES)"),
        sa.Column('name_nl', sa.String(length=100), nullable=True, comment="Coupe (NL)"),
        sa.Column('name_pl', sa.String(length=100), nullable=True, comment="Coupe (PL)"),
        sa.PrimaryKeyConstraint('name_en'),
        schema='product_attributes'
    )
    op.create_index('ix_product_attributes_fits_name_en', 'fits', ['name_en'], unique=False, schema='product_attributes')

    # ===== 10. TABLE genders =====
    op.create_table(
        'genders',
        sa.Column('name_en', sa.String(length=100), nullable=False, comment="Genre (EN)"),
        sa.Column('name_fr', sa.String(length=100), nullable=True, comment="Genre (FR)"),
        sa.Column('name_de', sa.String(length=100), nullable=True, comment="Genre (DE)"),
        sa.Column('name_it', sa.String(length=100), nullable=True, comment="Genre (IT)"),
        sa.Column('name_es', sa.String(length=100), nullable=True, comment="Genre (ES)"),
        sa.Column('name_nl', sa.String(length=100), nullable=True, comment="Genre (NL)"),
        sa.Column('name_pl', sa.String(length=100), nullable=True, comment="Genre (PL)"),
        sa.Column('vinted_id', sa.Integer(), nullable=True, comment="ID genre Vinted"),
        sa.Column('ebay_gender', sa.String(length=50), nullable=True, comment="Genre eBay correspondant"),
        sa.Column('etsy_gender', sa.String(length=50), nullable=True, comment="Genre Etsy correspondant"),
        sa.PrimaryKeyConstraint('name_en'),
        schema='product_attributes'
    )
    op.create_index('ix_product_attributes_genders_name_en', 'genders', ['name_en'], unique=False, schema='product_attributes')

    # ===== 11. TABLE materials =====
    op.create_table(
        'materials',
        sa.Column('name_en', sa.String(length=100), nullable=False, comment="Matière (EN)"),
        sa.Column('name_fr', sa.String(length=100), nullable=True, comment="Matière (FR)"),
        sa.Column('name_de', sa.String(length=100), nullable=True, comment="Matière (DE)"),
        sa.Column('name_it', sa.String(length=100), nullable=True, comment="Matière (IT)"),
        sa.Column('name_es', sa.String(length=100), nullable=True, comment="Matière (ES)"),
        sa.Column('name_nl', sa.String(length=100), nullable=True, comment="Matière (NL)"),
        sa.Column('name_pl', sa.String(length=100), nullable=True, comment="Matière (PL)"),
        sa.PrimaryKeyConstraint('name_en'),
        schema='product_attributes'
    )
    op.create_index('ix_product_attributes_materials_name_en', 'materials', ['name_en'], unique=False, schema='product_attributes')

    # ===== 12. TABLE origins =====
    op.create_table(
        'origins',
        sa.Column('name_en', sa.String(length=100), nullable=False, comment="Origine/Provenance (EN)"),
        sa.Column('name_fr', sa.String(length=100), nullable=True, comment="Origine/Provenance (FR)"),
        sa.Column('name_de', sa.String(length=100), nullable=True, comment="Origine/Provenance (DE)"),
        sa.Column('name_it', sa.String(length=100), nullable=True, comment="Origine/Provenance (IT)"),
        sa.Column('name_es', sa.String(length=100), nullable=True, comment="Origine/Provenance (ES)"),
        sa.Column('name_nl', sa.String(length=100), nullable=True, comment="Origine/Provenance (NL)"),
        sa.Column('name_pl', sa.String(length=100), nullable=True, comment="Origine/Provenance (PL)"),
        sa.PrimaryKeyConstraint('name_en'),
        schema='product_attributes'
    )
    op.create_index('ix_product_attributes_origins_name_en', 'origins', ['name_en'], unique=False, schema='product_attributes')

    # ===== 13. TABLE rises =====
    op.create_table(
        'rises',
        sa.Column('name_en', sa.String(length=100), nullable=False, comment="Hauteur de taille (EN)"),
        sa.Column('name_fr', sa.String(length=100), nullable=True, comment="Hauteur de taille (FR)"),
        sa.Column('name_de', sa.String(length=100), nullable=True, comment="Hauteur de taille (DE)"),
        sa.Column('name_it', sa.String(length=100), nullable=True, comment="Hauteur de taille (IT)"),
        sa.Column('name_es', sa.String(length=100), nullable=True, comment="Hauteur de taille (ES)"),
        sa.Column('name_nl', sa.String(length=100), nullable=True, comment="Hauteur de taille (NL)"),
        sa.Column('name_pl', sa.String(length=100), nullable=True, comment="Hauteur de taille (PL)"),
        sa.PrimaryKeyConstraint('name_en'),
        schema='product_attributes'
    )
    op.create_index('ix_product_attributes_rises_name_en', 'rises', ['name_en'], unique=False, schema='product_attributes')

    # ===== 14. TABLE seasons =====
    op.create_table(
        'seasons',
        sa.Column('name_en', sa.String(length=100), nullable=False, comment="Saison (EN)"),
        sa.Column('name_fr', sa.String(length=100), nullable=True, comment="Saison (FR)"),
        sa.Column('name_de', sa.String(length=100), nullable=True, comment="Saison (DE)"),
        sa.Column('name_it', sa.String(length=100), nullable=True, comment="Saison (IT)"),
        sa.Column('name_es', sa.String(length=100), nullable=True, comment="Saison (ES)"),
        sa.Column('name_nl', sa.String(length=100), nullable=True, comment="Saison (NL)"),
        sa.Column('name_pl', sa.String(length=100), nullable=True, comment="Saison (PL)"),
        sa.PrimaryKeyConstraint('name_en'),
        schema='product_attributes'
    )
    op.create_index('ix_product_attributes_seasons_name_en', 'seasons', ['name_en'], unique=False, schema='product_attributes')

    # ===== 15. TABLE sizes =====
    op.create_table(
        'sizes',
        sa.Column('name_en', sa.String(length=100), nullable=False, comment="Taille (EN)"),
        sa.Column('name_fr', sa.String(length=100), nullable=True, comment="Taille (FR)"),
        sa.Column('name_de', sa.String(length=100), nullable=True, comment="Taille (DE)"),
        sa.Column('name_it', sa.String(length=100), nullable=True, comment="Taille (IT)"),
        sa.Column('name_es', sa.String(length=100), nullable=True, comment="Taille (ES)"),
        sa.Column('name_nl', sa.String(length=100), nullable=True, comment="Taille (NL)"),
        sa.Column('name_pl', sa.String(length=100), nullable=True, comment="Taille (PL)"),
        sa.Column('vinted_id', sa.Integer(), nullable=True, comment="ID taille Vinted"),
        sa.Column('ebay_size', sa.String(length=50), nullable=True, comment="Taille eBay correspondante"),
        sa.Column('etsy_size', sa.String(length=50), nullable=True, comment="Taille Etsy correspondante"),
        sa.PrimaryKeyConstraint('name_en'),
        schema='product_attributes'
    )
    op.create_index('ix_product_attributes_sizes_name_en', 'sizes', ['name_en'], unique=False, schema='product_attributes')

    # ===== 16. TABLE sleeve_lengths =====
    op.create_table(
        'sleeve_lengths',
        sa.Column('name_en', sa.String(length=100), nullable=False, comment="Longueur de manche (EN)"),
        sa.Column('name_fr', sa.String(length=100), nullable=True, comment="Longueur de manche (FR)"),
        sa.Column('name_de', sa.String(length=100), nullable=True, comment="Longueur de manche (DE)"),
        sa.Column('name_it', sa.String(length=100), nullable=True, comment="Longueur de manche (IT)"),
        sa.Column('name_es', sa.String(length=100), nullable=True, comment="Longueur de manche (ES)"),
        sa.Column('name_nl', sa.String(length=100), nullable=True, comment="Longueur de manche (NL)"),
        sa.Column('name_pl', sa.String(length=100), nullable=True, comment="Longueur de manche (PL)"),
        sa.PrimaryKeyConstraint('name_en'),
        schema='product_attributes'
    )
    op.create_index('ix_product_attributes_sleeve_lengths_name_en', 'sleeve_lengths', ['name_en'], unique=False, schema='product_attributes')

    # ===== 17. TABLE trends =====
    op.create_table(
        'trends',
        sa.Column('name_en', sa.String(length=100), nullable=False, comment="Tendance/Style (EN)"),
        sa.Column('name_fr', sa.String(length=100), nullable=True, comment="Tendance/Style (FR)"),
        sa.Column('name_de', sa.String(length=100), nullable=True, comment="Tendance/Style (DE)"),
        sa.Column('name_it', sa.String(length=100), nullable=True, comment="Tendance/Style (IT)"),
        sa.Column('name_es', sa.String(length=100), nullable=True, comment="Tendance/Style (ES)"),
        sa.Column('name_nl', sa.String(length=100), nullable=True, comment="Tendance/Style (NL)"),
        sa.Column('name_pl', sa.String(length=100), nullable=True, comment="Tendance/Style (PL)"),
        sa.PrimaryKeyConstraint('name_en'),
        schema='product_attributes'
    )
    op.create_index('ix_product_attributes_trends_name_en', 'trends', ['name_en'], unique=False, schema='product_attributes')

    # ===== 18. TABLE unique_features =====
    op.create_table(
        'unique_features',
        sa.Column('name_en', sa.String(length=255), nullable=False, comment="Caractéristique unique (EN)"),
        sa.Column('name_fr', sa.String(length=255), nullable=True, comment="Caractéristique unique (FR)"),
        sa.Column('name_de', sa.String(length=255), nullable=True, comment="Caractéristique unique (DE)"),
        sa.Column('name_it', sa.String(length=255), nullable=True, comment="Caractéristique unique (IT)"),
        sa.Column('name_es', sa.String(length=255), nullable=True, comment="Caractéristique unique (ES)"),
        sa.Column('name_nl', sa.String(length=255), nullable=True, comment="Caractéristique unique (NL)"),
        sa.Column('name_pl', sa.String(length=255), nullable=True, comment="Caractéristique unique (PL)"),
        sa.PrimaryKeyConstraint('name_en'),
        schema='product_attributes'
    )
    op.create_index('ix_product_attributes_unique_features_name_en', 'unique_features', ['name_en'], unique=False, schema='product_attributes')


def downgrade() -> None:
    """
    Supprime toutes les tables d'attributs et le schema product_attributes.
    """
    # Supprimer toutes les tables dans l'ordre inverse
    op.drop_table('unique_features', schema='product_attributes')
    op.drop_table('trends', schema='product_attributes')
    op.drop_table('sleeve_lengths', schema='product_attributes')
    op.drop_table('sizes', schema='product_attributes')
    op.drop_table('seasons', schema='product_attributes')
    op.drop_table('rises', schema='product_attributes')
    op.drop_table('origins', schema='product_attributes')
    op.drop_table('materials', schema='product_attributes')
    op.drop_table('genders', schema='product_attributes')
    op.drop_table('fits', schema='product_attributes')
    op.drop_table('decades', schema='product_attributes')
    op.drop_table('closures', schema='product_attributes')
    op.drop_table('condition_sup', schema='product_attributes')
    op.drop_table('conditions', schema='product_attributes')
    op.drop_table('colors', schema='product_attributes')
    op.drop_table('categories', schema='product_attributes')
    op.drop_table('brands', schema='product_attributes')

    # Supprimer le schema
    op.execute("DROP SCHEMA IF EXISTS product_attributes CASCADE")
