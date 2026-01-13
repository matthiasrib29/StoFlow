"""add ai_max_images_per_analysis to subscription_quotas

Revision ID: 20260112_1750
Revises: 20260112_1901
Create Date: 2026-01-12 17:50:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20260112_1750'
down_revision: Union[str, None] = '20260112_1901'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add ai_max_images_per_analysis column to subscription_quotas
    op.add_column(
        'subscription_quotas',
        sa.Column(
            'ai_max_images_per_analysis',
            sa.Integer(),
            nullable=False,
            server_default='5',
            comment='Nombre max d\'images par analyse IA Vision'
        ),
        schema='public'
    )

    # Update values based on tier
    # FREE: 5 (default), STARTER: 10, PRO: 20, ENTERPRISE: 20
    op.execute("""
        UPDATE public.subscription_quotas
        SET ai_max_images_per_analysis = CASE tier
            WHEN 'STARTER' THEN 10
            WHEN 'PRO' THEN 20
            WHEN 'ENTERPRISE' THEN 20
            ELSE 5
        END
    """)


def downgrade() -> None:
    op.drop_column('subscription_quotas', 'ai_max_images_per_analysis', schema='public')
