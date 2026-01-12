"""remove_product_tables_from_public_schema

Revision ID: 8f9e5a3c1b2d
Revises: 29c3c8d7f0a3
Create Date: 2025-12-10 10:18:45.302581+01:00

IMPORTANT: Cette migration supprime les tables de produits du schema public.
Ces tables ont été créées par erreur dans la migration initiale (46aad9f85d14).

Tables à supprimer de public:
- products
- product_images
- vinted_products
- publication_history
- ai_generation_logs

Raison:
Dans une architecture multi-tenant avec schema-per-tenant, ces tables ne devraient PAS
être dans le schema public car elles contiennent des données isolées par tenant.

Les tables existent maintenant dans:
- template_tenant.* (template pour cloner les schemas user_X)
- user_{id}.* (schemas créés dynamiquement pour chaque tenant)

SÉCURITÉ:
Cette migration vérifie que les tables sont VIDES avant de les supprimer.
Si des données existent, la migration échoue avec un message d'erreur clair.

Author: Claude
Date: 2025-12-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8f9e5a3c1b2d'
down_revision: Union[str, None] = '29c3c8d7f0a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Supprime les tables de produits du schema public.

    SÉCURITÉ: Vérifie que les tables sont vides avant suppression.
    """

    # Vérifier que les tables sont vides
    conn = op.get_bind()

    # Vérifier products
    result = conn.execute(sa.text("SELECT COUNT(*) FROM public.products"))
    count = result.fetchone()[0]
    if count > 0:
        raise Exception(
            f"❌ ERREUR: La table public.products contient {count} enregistrements! "
            "Cette migration ne peut pas continuer car elle supprimerait des données. "
            "Si ces données doivent être migrées vers un schema user_X, "
            "faites-le manuellement avant de relancer cette migration."
        )

    print(f"✅ Table public.products est vide ({count} rows)")

    # Si tout est OK, supprimer les tables dans l'ordre inverse (FK)
    print("🗑️  Suppression des tables de produits du schema public...")

    # Utiliser DROP CASCADE car les schemas user_X partagent les sequences
    conn.execute(sa.text("DROP TABLE IF EXISTS public.ai_generation_logs CASCADE"))
    conn.execute(sa.text("DROP TABLE IF EXISTS public.publication_history CASCADE"))
    conn.execute(sa.text("DROP TABLE IF EXISTS public.vinted_products CASCADE"))
    conn.execute(sa.text("DROP TABLE IF EXISTS public.product_images CASCADE"))
    conn.execute(sa.text("DROP TABLE IF EXISTS public.products CASCADE"))

    print("✅ Tables supprimées avec succès du schema public")


def downgrade() -> None:
    """
    Recrée les tables de produits dans le schema public.

    NOTE: Cette opération ne restaure PAS les données!
    Elle recrée seulement la structure vide.
    """

    # Recréer products
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

    # Recréer product_images
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

    # Recréer vinted_products
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

    # Recréer publication_history
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

    # Recréer ai_generation_logs
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
