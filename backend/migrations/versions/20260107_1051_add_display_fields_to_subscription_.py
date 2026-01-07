"""add_display_fields_to_subscription_quotas

Adds display fields to subscription_quotas table for pricing page:
- price (DECIMAL)
- display_name, description, cta_text (VARCHAR)
- annual_discount_percent, display_order (INT)
- is_popular (BOOLEAN)

Revision ID: 303159a94619
Revises: 00021459a310
Create Date: 2026-01-07 10:51:07.575439+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '303159a94619'
down_revision: Union[str, None] = '00021459a310'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add display fields to subscription_quotas table."""
    # Add price column
    op.add_column(
        'subscription_quotas',
        sa.Column('price', sa.DECIMAL(10, 2), nullable=False, server_default='0.00',
                  comment='Prix mensuel de l\'abonnement en euros'),
        schema='public'
    )

    # Add display_name column
    op.add_column(
        'subscription_quotas',
        sa.Column('display_name', sa.String(50), nullable=False, server_default='',
                  comment='Display name on pricing page (e.g., \'Gratuit\', \'Pro\')'),
        schema='public'
    )

    # Add description column
    op.add_column(
        'subscription_quotas',
        sa.Column('description', sa.String(200), nullable=True,
                  comment='Short description (e.g., \'Pour découvrir Stoflow\')'),
        schema='public'
    )

    # Add annual_discount_percent column
    op.add_column(
        'subscription_quotas',
        sa.Column('annual_discount_percent', sa.Integer(), nullable=False, server_default='20',
                  comment='Annual discount percentage (e.g., 20 for -20%)'),
        schema='public'
    )

    # Add is_popular column
    op.add_column(
        'subscription_quotas',
        sa.Column('is_popular', sa.Boolean(), nullable=False, server_default='false',
                  comment='Show \'Populaire\' badge'),
        schema='public'
    )

    # Add cta_text column
    op.add_column(
        'subscription_quotas',
        sa.Column('cta_text', sa.String(100), nullable=True,
                  comment='Call-to-action button text (e.g., \'Essai gratuit 14 jours\')'),
        schema='public'
    )

    # Add display_order column
    op.add_column(
        'subscription_quotas',
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0',
                  comment='Order of display on pricing page (lower = first)'),
        schema='public'
    )


def downgrade() -> None:
    """Remove display fields from subscription_quotas table."""
    op.drop_column('subscription_quotas', 'display_order', schema='public')
    op.drop_column('subscription_quotas', 'cta_text', schema='public')
    op.drop_column('subscription_quotas', 'is_popular', schema='public')
    op.drop_column('subscription_quotas', 'annual_discount_percent', schema='public')
    op.drop_column('subscription_quotas', 'description', schema='public')
    op.drop_column('subscription_quotas', 'display_name', schema='public')
    op.drop_column('subscription_quotas', 'price', schema='public')
