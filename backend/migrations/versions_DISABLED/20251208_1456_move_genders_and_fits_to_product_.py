"""move_genders_and_fits_to_product_attributes

Revision ID: a17332e07bb1
Revises: 375ae2b4815c
Create Date: 2025-12-08 14:56:52.533107+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a17332e07bb1'
down_revision: Union[str, None] = '375ae2b4815c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ===== MOVE genders AND fits FROM public TO product_attributes =====
    op.execute("ALTER TABLE public.genders SET SCHEMA product_attributes")
    op.execute("ALTER TABLE public.fits SET SCHEMA product_attributes")


def downgrade() -> None:
    # ===== MOVE genders AND fits BACK FROM product_attributes TO public =====
    op.execute("ALTER TABLE product_attributes.genders SET SCHEMA public")
    op.execute("ALTER TABLE product_attributes.fits SET SCHEMA public")
