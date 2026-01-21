"""add stripe_events table for webhook idempotency

Revision ID: 20260120_2330
Revises: 20260120_1000
Create Date: 2026-01-20 23:30:00

Security Fix: Stripe webhook idempotency to prevent duplicate processing
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260120_2330"
down_revision = "20260120_1000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create stripe_events table for webhook idempotency tracking."""
    op.create_table(
        "stripe_events",
        sa.Column("event_id", sa.String(255), primary_key=True),
        sa.Column("event_type", sa.String(255), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="processed"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "processed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now()
        ),
    )

    # Create indexes
    op.create_index(
        "idx_stripe_events_event_id",
        "stripe_events",
        ["event_id"],
        unique=True
    )
    op.create_index(
        "idx_stripe_events_processed_at",
        "stripe_events",
        ["processed_at"]
    )


def downgrade() -> None:
    """Remove stripe_events table."""
    op.drop_index("idx_stripe_events_processed_at", table_name="stripe_events")
    op.drop_index("idx_stripe_events_event_id", table_name="stripe_events")
    op.drop_table("stripe_events")
