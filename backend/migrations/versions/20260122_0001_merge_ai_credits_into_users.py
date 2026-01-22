"""merge ai_credits table into users

Revision ID: 8a4c2e1f3d5b
Revises: b7af373f1ff0
Create Date: 2026-01-22

Merge the ai_credits table (1:1 relation) directly into the users table.
This simplifies the data model and removes unnecessary joins.

Columns moved:
- ai_credits_purchased -> users.ai_credits_purchased
- ai_credits_used_this_month -> users.ai_credits_used_this_month
- last_reset_date -> users.ai_credits_last_reset_date
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8a4c2e1f3d5b'
down_revision = 'b7af373f1ff0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    1. Add AI credits columns to users table
    2. Copy existing data from ai_credits
    3. Drop ai_credits table
    """
    conn = op.get_bind()

    # 1. Add columns to users table
    op.add_column(
        'users',
        sa.Column(
            'ai_credits_purchased',
            sa.Integer(),
            nullable=False,
            server_default='0',
            comment='Purchased AI credits (cumulative, never expire)'
        ),
        schema='public'
    )
    op.add_column(
        'users',
        sa.Column(
            'ai_credits_used_this_month',
            sa.Integer(),
            nullable=False,
            server_default='0',
            comment='AI credits used this month'
        ),
        schema='public'
    )
    op.add_column(
        'users',
        sa.Column(
            'ai_credits_last_reset_date',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            comment='Last monthly reset date'
        ),
        schema='public'
    )

    # 2. Copy existing data from ai_credits to users
    conn.execute(sa.text("""
        UPDATE public.users u
        SET ai_credits_purchased = ac.ai_credits_purchased,
            ai_credits_used_this_month = ac.ai_credits_used_this_month,
            ai_credits_last_reset_date = ac.last_reset_date
        FROM public.ai_credits ac
        WHERE u.id = ac.user_id
    """))

    # 3. Drop the ai_credits table
    op.drop_table('ai_credits', schema='public')


def downgrade() -> None:
    """
    1. Recreate ai_credits table
    2. Copy data back from users
    3. Drop columns from users
    """
    # 1. Recreate ai_credits table
    op.create_table(
        'ai_credits',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            'user_id',
            sa.Integer(),
            sa.ForeignKey('public.users.id', ondelete='CASCADE'),
            unique=True,
            nullable=False,
            index=True,
            comment='User owner'
        ),
        sa.Column(
            'ai_credits_purchased',
            sa.Integer(),
            nullable=False,
            default=0,
            comment='Purchased AI credits (cumulative, never expire)'
        ),
        sa.Column(
            'ai_credits_used_this_month',
            sa.Integer(),
            nullable=False,
            default=0,
            comment='AI credits used this month'
        ),
        sa.Column(
            'last_reset_date',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            comment='Last monthly reset date'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False
        ),
        schema='public'
    )

    # 2. Copy data back from users to ai_credits
    conn = op.get_bind()
    conn.execute(sa.text("""
        INSERT INTO public.ai_credits (user_id, ai_credits_purchased, ai_credits_used_this_month, last_reset_date)
        SELECT id, ai_credits_purchased, ai_credits_used_this_month, ai_credits_last_reset_date
        FROM public.users
        WHERE ai_credits_purchased > 0 OR ai_credits_used_this_month > 0
    """))

    # 3. Drop columns from users
    op.drop_column('users', 'ai_credits_last_reset_date', schema='public')
    op.drop_column('users', 'ai_credits_used_this_month', schema='public')
    op.drop_column('users', 'ai_credits_purchased', schema='public')
