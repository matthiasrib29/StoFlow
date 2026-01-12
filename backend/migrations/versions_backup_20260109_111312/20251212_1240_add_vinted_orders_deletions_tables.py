"""add_vinted_orders_deletions_tables

Revision ID: d948e068256d
Revises: c837d967145c
Create Date: 2025-12-12 12:40:00.000000+01:00

Cette migration ajoute les tables pour la gestion des commandes Vinted
et l'archivage des produits supprimés.

Tables créées (dans les schémas user_X):
- vinted_orders: Commandes Vinted (transaction_id comme PK)
- vinted_order_products: Produits dans les commandes (relation 1-N)
- vinted_deletions: Archive des produits supprimés avec statistiques

Business Rules (2025-12-12):
- Les commandes utilisent transaction_id de Vinted comme clé primaire
- Une commande peut contenir plusieurs produits (bundle)
- Les deletions conservent les stats au moment de la suppression

Source: pythonApiWOO/Models/vinted/
Author: Claude
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd948e068256d'
down_revision: Union[str, None] = 'c837d967145c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crée les tables vinted_orders, vinted_order_products et vinted_deletions."""

    # Table vinted_orders
    op.create_table(
        'vinted_orders',
        sa.Column('transaction_id', sa.BigInteger(), nullable=False, comment='ID transaction Vinted (PK)'),
        sa.Column('buyer_id', sa.BigInteger(), nullable=True, comment='ID acheteur Vinted'),
        sa.Column('buyer_login', sa.String(255), nullable=True, comment='Login acheteur'),
        sa.Column('seller_id', sa.BigInteger(), nullable=True, comment='ID vendeur Vinted'),
        sa.Column('seller_login', sa.String(255), nullable=True, comment='Login vendeur'),
        sa.Column('status', sa.String(50), nullable=True, comment='Statut commande'),
        sa.Column('total_price', sa.Numeric(10, 2), nullable=True, comment='Prix total'),
        sa.Column('currency', sa.String(3), nullable=True, server_default='EUR', comment='Devise'),
        sa.Column('shipping_price', sa.Numeric(10, 2), nullable=True, comment='Frais de port'),
        sa.Column('service_fee', sa.Numeric(10, 2), nullable=True, comment='Frais de service'),
        sa.Column('buyer_protection_fee', sa.Numeric(10, 2), nullable=True, comment='Protection acheteur'),
        sa.Column('seller_revenue', sa.Numeric(10, 2), nullable=True, comment='Revenu vendeur net'),
        sa.Column('tracking_number', sa.String(100), nullable=True, comment='Numéro de suivi'),
        sa.Column('carrier', sa.String(100), nullable=True, comment='Transporteur'),
        sa.Column('shipping_tracking_code', sa.String(100), nullable=True, comment='Code suivi transporteur'),
        sa.Column('created_at_vinted', sa.DateTime(timezone=True), nullable=True, comment='Date création Vinted'),
        sa.Column('shipped_at', sa.DateTime(timezone=True), nullable=True, comment='Date expédition'),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True, comment='Date livraison'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True, comment='Date finalisation'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='Date création locale'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='Date MAJ locale'),
        sa.PrimaryKeyConstraint('transaction_id')
    )

    # Index pour vinted_orders
    op.create_index('idx_vinted_orders_buyer_id', 'vinted_orders', ['buyer_id'])
    op.create_index('idx_vinted_orders_status', 'vinted_orders', ['status'])
    op.create_index('idx_vinted_orders_created_at_vinted', 'vinted_orders', ['created_at_vinted'])

    # Table vinted_order_products
    op.create_table(
        'vinted_order_products',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('transaction_id', sa.BigInteger(), nullable=False, comment='FK vers vinted_orders'),
        sa.Column('vinted_item_id', sa.BigInteger(), nullable=True, comment='ID article Vinted'),
        sa.Column('product_id', sa.BigInteger(), nullable=True, comment='ID produit Stoflow'),
        sa.Column('title', sa.String(255), nullable=True, comment='Titre produit'),
        sa.Column('price', sa.Numeric(10, 2), nullable=True, comment='Prix unitaire'),
        sa.Column('size', sa.String(100), nullable=True, comment='Taille'),
        sa.Column('brand', sa.String(255), nullable=True, comment='Marque'),
        sa.Column('photo_url', sa.Text(), nullable=True, comment='URL photo principale'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['transaction_id'], ['vinted_orders.transaction_id'], ondelete='CASCADE')
    )

    # Index pour vinted_order_products
    op.create_index('idx_vinted_order_products_transaction_id', 'vinted_order_products', ['transaction_id'])
    op.create_index('idx_vinted_order_products_vinted_item_id', 'vinted_order_products', ['vinted_item_id'])
    op.create_index('idx_vinted_order_products_product_id', 'vinted_order_products', ['product_id'])

    # Table vinted_deletions
    op.create_table(
        'vinted_deletions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('id_vinted', sa.BigInteger(), nullable=True, comment='ID Vinted du produit supprimé'),
        sa.Column('id_site', sa.BigInteger(), nullable=True, comment='ID produit Stoflow'),
        sa.Column('price', sa.Numeric(10, 2), nullable=True, comment='Prix au moment suppression'),
        sa.Column('date_published', sa.Date(), nullable=True, comment='Date publication initiale'),
        sa.Column('date_deleted', sa.Date(), nullable=True, comment='Date suppression'),
        sa.Column('view_count', sa.Integer(), nullable=True, server_default='0', comment='Nombre de vues'),
        sa.Column('favourite_count', sa.Integer(), nullable=True, server_default='0', comment='Nombre de favoris'),
        sa.Column('conversations', sa.Integer(), nullable=True, server_default='0', comment='Nombre de conversations'),
        sa.Column('days_active', sa.Integer(), nullable=True, comment='Jours en ligne'),
        sa.PrimaryKeyConstraint('id')
    )

    # Index pour vinted_deletions
    op.create_index('idx_vinted_deletions_id_vinted', 'vinted_deletions', ['id_vinted'])
    op.create_index('idx_vinted_deletions_id_site', 'vinted_deletions', ['id_site'])
    op.create_index('idx_vinted_deletions_date_deleted', 'vinted_deletions', ['date_deleted'])
    op.create_index('idx_vinted_deletions_days_active', 'vinted_deletions', ['days_active'])


def downgrade() -> None:
    """Supprime les tables vinted_orders, vinted_order_products et vinted_deletions."""

    # Drop indexes first
    op.drop_index('idx_vinted_deletions_days_active', table_name='vinted_deletions')
    op.drop_index('idx_vinted_deletions_date_deleted', table_name='vinted_deletions')
    op.drop_index('idx_vinted_deletions_id_site', table_name='vinted_deletions')
    op.drop_index('idx_vinted_deletions_id_vinted', table_name='vinted_deletions')

    op.drop_index('idx_vinted_order_products_product_id', table_name='vinted_order_products')
    op.drop_index('idx_vinted_order_products_vinted_item_id', table_name='vinted_order_products')
    op.drop_index('idx_vinted_order_products_transaction_id', table_name='vinted_order_products')

    op.drop_index('idx_vinted_orders_created_at_vinted', table_name='vinted_orders')
    op.drop_index('idx_vinted_orders_status', table_name='vinted_orders')
    op.drop_index('idx_vinted_orders_buyer_id', table_name='vinted_orders')

    # Drop tables (order matters due to FK)
    op.drop_table('vinted_deletions')
    op.drop_table('vinted_order_products')
    op.drop_table('vinted_orders')
