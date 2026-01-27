"""create_vinted_keyword_scan_logs_table

Revision ID: 31179c7ddf09
Revises: 56c6e9d7806a
Create Date: 2026-01-27 14:03:48.306682+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '31179c7ddf09'
down_revision: Union[str, None] = '56c6e9d7806a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # Idempotency check
    result = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'vinted' AND table_name = 'vinted_keyword_scan_logs'
        )
    """))
    if result.scalar():
        return

    op.create_table(
        "vinted_keyword_scan_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("keyword", sa.String(255), nullable=False),
        sa.Column("marketplace", sa.String(50), nullable=False, server_default="vinted_fr"),
        sa.Column("last_page_scanned", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_pro_sellers_found", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("exhausted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "last_scanned_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        schema="vinted",
    )

    op.create_index(
        "idx_vinted_kw_scan_keyword_mp",
        "vinted_keyword_scan_logs",
        ["keyword", "marketplace"],
        unique=True,
        schema="vinted",
    )


def downgrade() -> None:
    op.drop_index(
        "idx_vinted_kw_scan_keyword_mp",
        table_name="vinted_keyword_scan_logs",
        schema="vinted",
    )
    op.drop_table("vinted_keyword_scan_logs", schema="vinted")
