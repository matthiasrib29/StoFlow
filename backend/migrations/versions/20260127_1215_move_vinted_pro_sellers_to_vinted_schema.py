"""move_vinted_pro_sellers_to_vinted_schema

Revision ID: 56c6e9d7806a
Revises: c0215cd307b0
Create Date: 2026-01-27 12:15:15.330643+01:00

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '56c6e9d7806a'
down_revision: Union[str, None] = 'c0215cd307b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Move vinted_pro_sellers table from public to vinted schema."""
    conn = op.get_bind()
    conn.execute(text("ALTER TABLE public.vinted_pro_sellers SET SCHEMA vinted"))


def downgrade() -> None:
    """Move vinted_pro_sellers table back to public schema."""
    conn = op.get_bind()
    conn.execute(text("ALTER TABLE vinted.vinted_pro_sellers SET SCHEMA public"))
