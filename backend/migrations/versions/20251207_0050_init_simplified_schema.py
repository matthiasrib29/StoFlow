"""init simplified schema

Revision ID: 46aad9f85d14
Revises:
Create Date: 2025-12-07 00:50:54.127707+01:00

IMPORTANT: Cette migration crée toutes les tables de base du schema public.
Elle est basée sur la structure de la DB de dev (stoflow_db).
Toutes les migrations suivantes supposent que ces tables existent.

Author: Claude
Date: 2025-12-09
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '46aad9f85d14'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Crée toutes les tables de base du schema public.

    Tables créées:
    - subscription_quotas (table de référence pour les quotas)
    - users (utilisateurs avec foreign key vers subscription_quotas)
    - platform_mappings (mappings plateformes)
    - clothing_prices (prix de référence brand/category)
    - products (produits dans schema public, sera dans user_X en prod)
    - product_images (images produits)
    - vinted_products (données spécifiques Vinted)
    - publication_history (historique publications)
    - ai_generation_logs (logs génération IA)
    """

    # ===== 1. ENUMS =====

    # UserRole
    op.execute("CREATE TYPE user_role AS ENUM ('ADMIN', 'USER', 'SUPPORT')")

    # SubscriptionTier
    op.execute("CREATE TYPE subscription_tier AS ENUM ('FREE', 'STARTER', 'PRO', 'ENTERPRISE')")

    # PlatformType
    op.execute("CREATE TYPE platform_type AS ENUM ('VINTED', 'EBAY', 'ETSY')")

    # ProductStatus
    op.execute("""
        CREATE TYPE product_status AS ENUM (
            'DRAFT', 'PENDING_REVIEW', 'APPROVED', 'REJECTED',
            'SCHEDULED', 'PUBLISHED', 'SUSPENDED', 'FLAGGED',
            'SOLD', 'ARCHIVED'
        )
    """)

    # PublicationStatus
    op.execute("CREATE TYPE publication_status AS ENUM ('PENDING', 'SUCCESS', 'FAILED')")

    # AccountType
    op.execute("CREATE TYPE account_type AS ENUM ('individual', 'professional')")

    # BusinessType
    op.execute("CREATE TYPE business_type AS ENUM ('resale', 'dropshipping', 'artisan', 'retail', 'other')")

    # EstimatedProducts
    op.execute("CREATE TYPE estimated_products AS ENUM ('0-50', '50-200', '200-500', '500+')")

    # Gender (public enum)
    op.execute("CREATE TYPE gender AS ENUM ('male', 'female', 'unisex')")

    # ===== 2. TABLE subscription_quotas (référence) =====

    op.create_table(
        'subscription_quotas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tier', postgresql.ENUM('FREE', 'STARTER', 'PRO', 'ENTERPRISE', name='subscription_tier', create_type=False), nullable=False),
        sa.Column('max_products', sa.Integer(), nullable=False, comment="Nombre maximum de produits actifs"),
        sa.Column('max_platforms', sa.Integer(), nullable=False, comment="Nombre maximum de plateformes connectées"),
        sa.Column('ai_credits_monthly', sa.Integer(), nullable=False, comment="Crédits IA mensuels"),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tier', name='uq_subscription_quotas_tier'),
        schema='public'
    )
    op.create_index('ix_subscription_quotas_id', 'subscription_quotas', ['id'], unique=False, schema='public')
    op.create_index('ix_subscription_quotas_tier', 'subscription_quotas', ['tier'], unique=False, schema='public')

    # ===== 3. TABLE users =====

    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('role', postgresql.ENUM('ADMIN', 'USER', 'SUPPORT', name='user_role', create_type=False), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('subscription_tier', postgresql.ENUM('FREE', 'STARTER', 'PRO', 'ENTERPRISE', name='subscription_tier', create_type=False), nullable=False),
        sa.Column('subscription_status', sa.String(length=50), nullable=False, comment="active, suspended, cancelled"),
        sa.Column('vinted_cookies', sa.String(length=2000), nullable=True, comment="Cookies Vinted chiffrés (JSON string)"),
        sa.Column('vinted_user_id', sa.Integer(), nullable=True),
        sa.Column('vinted_username', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        # Onboarding fields (added 2025-12-08)
        sa.Column('business_name', sa.String(length=255), nullable=True, comment="Nom de l'entreprise ou de la boutique"),
        sa.Column('account_type', postgresql.ENUM('individual', 'professional', name='account_type', create_type=False), nullable=False, server_default="individual", comment="Type de compte: individual (particulier) ou professional (entreprise)"),
        sa.Column('business_type', postgresql.ENUM('resale', 'dropshipping', 'artisan', 'retail', 'other', name='business_type', create_type=False), nullable=True, comment="Type d'activité: resale, dropshipping, artisan, retail, other"),
        sa.Column('estimated_products', postgresql.ENUM('0-50', '50-200', '200-500', '500+', name='estimated_products', create_type=False), nullable=True, comment="Nombre de produits estimé: 0-50, 50-200, 200-500, 500+"),
        sa.Column('siret', sa.String(length=14), nullable=True, comment="Numéro SIRET (France) - uniquement pour les professionnels"),
        sa.Column('vat_number', sa.String(length=20), nullable=True, comment="Numéro de TVA intracommunautaire - uniquement pour les professionnels"),
        sa.Column('phone', sa.String(length=20), nullable=True, comment="Numéro de téléphone"),
        sa.Column('country', sa.String(length=2), nullable=False, server_default="FR", comment="Code pays ISO 3166-1 alpha-2 (FR, BE, CH, etc.)"),
        sa.Column('language', sa.String(length=2), nullable=False, server_default="fr", comment="Code langue ISO 639-1 (fr, en, etc.)"),
        sa.Column('subscription_tier_id', sa.Integer(), nullable=False, comment="FK vers subscription_quotas"),
        sa.ForeignKeyConstraint(['subscription_tier_id'], ['subscription_quotas.id'], name='fk_users_subscription_tier_id'),
        sa.PrimaryKeyConstraint('id'),
        schema='public'
    )
    op.create_index('ix_public_users_id', 'users', ['id'], unique=False, schema='public')
    op.create_index('ix_public_users_email', 'users', ['email'], unique=True, schema='public')

    # ===== 4. TABLE platform_mappings =====

    op.create_table(
        'platform_mappings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, comment="ID de l'utilisateur (FK users.id)"),
        sa.Column('platform', postgresql.ENUM('VINTED', 'EBAY', 'ETSY', name='platform_type', create_type=False), nullable=False),
        sa.Column('credentials', sa.Text(), nullable=True, comment="Credentials chiffrés (JSON string)"),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_platform_mappings_user_id', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='public'
    )
    op.create_index('ix_platform_mappings_id', 'platform_mappings', ['id'], unique=False, schema='public')
    op.create_index('ix_platform_mappings_user_id', 'platform_mappings', ['user_id'], unique=False, schema='public')

    # ===== 5. TABLE clothing_prices =====

    op.create_table(
        'clothing_prices',
        sa.Column('brand', sa.String(length=100), nullable=False, comment="Marque (FK product_attributes.brands.name)"),
        sa.Column('category', sa.String(length=255), nullable=False, comment="Catégorie (FK product_attributes.categories.name_en)"),
        sa.Column('base_price', sa.Numeric(precision=10, scale=2), nullable=False, comment="Prix de base en euros"),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment="Date de dernière mise à jour du prix"),
        sa.PrimaryKeyConstraint('brand', 'category'),
        sa.CheckConstraint('base_price >= 0', name='check_base_price_positive'),
        schema='public',
        comment='Prix de base par brand/category pour calcul automatique'
    )

    # ===== 6. TABLE products =====

    op.create_table(
        'products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sku', sa.String(length=100), nullable=True, comment="SKU du produit"),
        sa.Column('title', sa.String(length=500), nullable=False, comment="Titre du produit"),
        sa.Column('description', sa.Text(), nullable=False, comment="Description complète"),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False, comment="Prix de vente"),
        sa.Column('category', sa.String(length=255), nullable=False, comment="Catégorie (FK public.categories)"),
        sa.Column('brand', sa.String(length=100), nullable=True, comment="Marque (FK public.brands)"),
        sa.Column('condition', sa.String(length=100), nullable=False, comment="État (FK public.conditions)"),
        sa.Column('label_size', sa.String(length=100), nullable=True, comment="Taille étiquette (FK public.sizes)"),
        sa.Column('color', sa.String(length=100), nullable=True, comment="Couleur (FK public.colors)"),
        sa.Column('material', sa.String(length=100), nullable=True, comment="Matière (FK public.materials)"),
        sa.Column('fit', sa.String(length=100), nullable=True, comment="Coupe (FK public.fits)"),
        sa.Column('gender', sa.String(length=100), nullable=True, comment="Genre (FK public.genders)"),
        sa.Column('season', sa.String(length=100), nullable=True, comment="Saison (FK public.seasons)"),
        sa.Column('condition_sup', sa.String(length=255), nullable=True, comment="État supplémentaire/détails"),
        sa.Column('rise', sa.String(length=100), nullable=True, comment="Hauteur de taille (pantalons)"),
        sa.Column('closure', sa.String(length=100), nullable=True, comment="Type de fermeture"),
        sa.Column('sleeve_length', sa.String(length=100), nullable=True, comment="Longueur de manche"),
        sa.Column('origin', sa.String(length=100), nullable=True, comment="Origine/provenance"),
        sa.Column('decade', sa.String(length=100), nullable=True, comment="Décennie (vintage)"),
        sa.Column('trend', sa.String(length=100), nullable=True, comment="Tendance"),
        sa.Column('name_sup', sa.String(length=100), nullable=True, comment="Nom supplémentaire"),
        sa.Column('location', sa.String(length=100), nullable=True, comment="Localisation"),
        sa.Column('model', sa.String(length=100), nullable=True, comment="Modèle"),
        sa.Column('dim1', sa.Integer(), nullable=True, comment="Dimension 1 (cm)"),
        sa.Column('dim2', sa.Integer(), nullable=True, comment="Dimension 2 (cm)"),
        sa.Column('dim3', sa.Integer(), nullable=True, comment="Dimension 3 (cm)"),
        sa.Column('dim4', sa.Integer(), nullable=True, comment="Dimension 4 (cm)"),
        sa.Column('dim5', sa.Integer(), nullable=True, comment="Dimension 5 (cm)"),
        sa.Column('dim6', sa.Integer(), nullable=True, comment="Dimension 6 (cm)"),
        sa.Column('stock_quantity', sa.Integer(), nullable=False),
        sa.Column('images', sa.Text(), nullable=True, comment="Images URLs (JSON array)"),
        sa.Column('status', postgresql.ENUM('DRAFT', 'PENDING_REVIEW', 'APPROVED', 'REJECTED', 'SCHEDULED', 'PUBLISHED', 'SUSPENDED', 'FLAGGED', 'SOLD', 'ARCHIVED', name='product_status', create_type=False), nullable=False),
        sa.Column('scheduled_publish_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sold_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('integration_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('pricing_edit', sa.String(length=100), nullable=True, comment="Édition limitée/exclusive"),
        sa.Column('pricing_rarity', sa.String(length=100), nullable=True, comment="Rareté du produit"),
        sa.Column('pricing_quality', sa.String(length=100), nullable=True, comment="Qualité exceptionnelle"),
        sa.Column('pricing_details', sa.String(length=100), nullable=True, comment="Détails valorisants"),
        sa.Column('pricing_style', sa.String(length=100), nullable=True, comment="Style iconique"),
        sa.Column('unique_feature', sa.Text(), nullable=True, comment="Caractéristiques uniques"),
        sa.Column('marking', sa.Text(), nullable=True, comment="Marquages/logos"),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('stock_quantity >= 0', name='check_stock_positive'),
        schema='public'
    )
    op.create_index('ix_products_id', 'products', ['id'], unique=False, schema='public')

    # ===== 7. TABLE product_images =====

    op.create_table(
        'product_images',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False, comment="ID du produit (FK products.id, cascade delete)"),
        sa.Column('image_path', sa.String(length=1000), nullable=False, comment="Chemin relatif de l'image"),
        sa.Column('display_order', sa.Integer(), nullable=False, comment="Ordre d'affichage (0 = première)"),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], name='fk_product_images_product_id', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='public'
    )
    op.create_index('ix_product_images_id', 'product_images', ['id'], unique=False, schema='public')
    op.create_index('ix_product_images_product_id', 'product_images', ['product_id'], unique=False, schema='public')

    # ===== 8. TABLE vinted_products =====

    op.create_table(
        'vinted_products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False, comment="ID du produit Stoflow (FK products.id)"),
        sa.Column('vinted_item_id', sa.BigInteger(), nullable=True, comment="ID du produit sur Vinted"),
        sa.Column('vinted_url', sa.String(length=500), nullable=True, comment="URL du produit sur Vinted"),
        sa.Column('vinted_category_id', sa.Integer(), nullable=True, comment="ID catégorie Vinted"),
        sa.Column('vinted_brand_id', sa.Integer(), nullable=True, comment="ID marque Vinted"),
        sa.Column('vinted_color_ids', sa.String(length=100), nullable=True, comment="IDs couleurs Vinted (CSV)"),
        sa.Column('vinted_size_id', sa.Integer(), nullable=True, comment="ID taille Vinted"),
        sa.Column('vinted_status_id', sa.Integer(), nullable=True, comment="ID statut Vinted"),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], name='fk_vinted_products_product_id', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='public'
    )
    op.create_index('ix_vinted_products_id', 'vinted_products', ['id'], unique=False, schema='public')
    op.create_index('ix_vinted_products_product_id', 'vinted_products', ['product_id'], unique=False, schema='public')
    op.create_index('ix_vinted_products_vinted_item_id', 'vinted_products', ['vinted_item_id'], unique=False, schema='public')

    # ===== 9. TABLE publication_history =====

    op.create_table(
        'publication_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False, comment="ID du produit (FK products.id)"),
        sa.Column('platform', postgresql.ENUM('VINTED', 'EBAY', 'ETSY', name='platform_type', create_type=False), nullable=False, comment="Plateforme de publication"),
        sa.Column('status', postgresql.ENUM('PENDING', 'SUCCESS', 'FAILED', name='publication_status', create_type=False), nullable=False, comment="Statut de la publication"),
        sa.Column('platform_product_id', sa.String(length=100), nullable=True, comment="ID du produit sur la plateforme"),
        sa.Column('error_message', sa.Text(), nullable=True, comment="Message d'erreur si échec"),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment="Métadonnées supplémentaires"),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], name='fk_publication_history_product_id', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='public'
    )
    op.create_index('ix_publication_history_id', 'publication_history', ['id'], unique=False, schema='public')
    op.create_index('ix_publication_history_product_id', 'publication_history', ['product_id'], unique=False, schema='public')

    # ===== 10. TABLE ai_generation_logs =====

    op.create_table(
        'ai_generation_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False, comment="ID du produit (FK products.id)"),
        sa.Column('model', sa.String(length=100), nullable=False, comment="Modèle utilisé (gpt-4o-mini, etc.)"),
        sa.Column('prompt_tokens', sa.Integer(), nullable=False, comment="Tokens utilisés dans le prompt"),
        sa.Column('completion_tokens', sa.Integer(), nullable=False, comment="Tokens générés dans la réponse"),
        sa.Column('total_tokens', sa.Integer(), nullable=False, comment="Total tokens (prompt + completion)"),
        sa.Column('total_cost', sa.Numeric(precision=10, scale=6), nullable=False, comment="Coût total en $ (6 decimales)"),
        sa.Column('cached', sa.Boolean(), nullable=False, comment="Résultat depuis cache ou API"),
        sa.Column('generation_time_ms', sa.Integer(), nullable=False, comment="Temps de génération en ms"),
        sa.Column('error_message', sa.Text(), nullable=True, comment="Message d'erreur si échec"),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], name='fk_ai_generation_logs_product_id', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='public'
    )
    op.create_index('ix_ai_generation_logs_id', 'ai_generation_logs', ['id'], unique=False, schema='public')
    op.create_index('ix_ai_generation_logs_product_id', 'ai_generation_logs', ['product_id'], unique=False, schema='public')


def downgrade() -> None:
    """
    Supprime toutes les tables créées par upgrade().
    """

    # Supprimer tables dans l'ordre inverse (Foreign Keys)
    op.drop_table('ai_generation_logs', schema='public')
    op.drop_table('publication_history', schema='public')
    op.drop_table('vinted_products', schema='public')
    op.drop_table('product_images', schema='public')
    op.drop_table('products', schema='public')
    op.drop_table('clothing_prices', schema='public')
    op.drop_table('platform_mappings', schema='public')
    op.drop_table('users', schema='public')
    op.drop_table('subscription_quotas', schema='public')

    # Supprimer ENUMs
    op.execute('DROP TYPE IF EXISTS gender CASCADE')
    op.execute('DROP TYPE IF EXISTS estimated_products CASCADE')
    op.execute('DROP TYPE IF EXISTS business_type CASCADE')
    op.execute('DROP TYPE IF EXISTS account_type CASCADE')
    op.execute('DROP TYPE IF EXISTS publication_status CASCADE')
    op.execute('DROP TYPE IF EXISTS product_status CASCADE')
    op.execute('DROP TYPE IF EXISTS platform_type CASCADE')
    op.execute('DROP TYPE IF EXISTS subscription_tier CASCADE')
    op.execute('DROP TYPE IF EXISTS user_role CASCADE')
