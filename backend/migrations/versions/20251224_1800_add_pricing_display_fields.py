"""Add pricing display fields to subscription_quotas and create subscription_features table

Revision ID: 20251224_1800
Revises: 20251222_2100
Create Date: 2024-12-24 18:00:00

This migration adds:
1. Display fields to subscription_quotas for landing page pricing section
2. Creates subscription_features table for feature lists per plan
3. Seeds initial data for display names and features
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = "20251224_1800"
down_revision = "20251222_2100"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add display columns to subscription_quotas
    op.add_column(
        "subscription_quotas",
        sa.Column("display_name", sa.String(50), nullable=False, server_default=""),
        schema="public"
    )
    op.add_column(
        "subscription_quotas",
        sa.Column("description", sa.String(200), nullable=True),
        schema="public"
    )
    op.add_column(
        "subscription_quotas",
        sa.Column("annual_discount_percent", sa.Integer(), nullable=False, server_default="20"),
        schema="public"
    )
    op.add_column(
        "subscription_quotas",
        sa.Column("is_popular", sa.Boolean(), nullable=False, server_default="false"),
        schema="public"
    )
    op.add_column(
        "subscription_quotas",
        sa.Column("cta_text", sa.String(100), nullable=True),
        schema="public"
    )
    op.add_column(
        "subscription_quotas",
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        schema="public"
    )

    # 2. Create subscription_features table
    op.create_table(
        "subscription_features",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("subscription_quota_id", sa.Integer(), nullable=False),
        sa.Column("feature_text", sa.String(200), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(
            ["subscription_quota_id"],
            ["public.subscription_quotas.id"],
            ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="public"
    )
    op.create_index(
        "ix_subscription_features_subscription_quota_id",
        "subscription_features",
        ["subscription_quota_id"],
        schema="public"
    )

    # 3. Seed display data for existing subscription_quotas
    # Get connection for raw SQL updates
    conn = op.get_bind()

    # Update FREE tier
    conn.execute(sa.text("""
        UPDATE public.subscription_quotas
        SET display_name = 'Gratuit',
            description = 'Pour découvrir Stoflow',
            annual_discount_percent = 0,
            is_popular = false,
            cta_text = 'Commencer',
            display_order = 0,
            price = 0
        WHERE tier = 'FREE'
    """))

    # Update STARTER tier (displayed as "Pro")
    conn.execute(sa.text("""
        UPDATE public.subscription_quotas
        SET display_name = 'Pro',
            description = 'Pour les vendeurs actifs',
            annual_discount_percent = 20,
            is_popular = true,
            cta_text = 'Essai gratuit 14 jours',
            display_order = 1,
            price = 19
        WHERE tier = 'STARTER'
    """))

    # Update PRO tier (displayed as "Business")
    conn.execute(sa.text("""
        UPDATE public.subscription_quotas
        SET display_name = 'Business',
            description = 'Pour les professionnels',
            annual_discount_percent = 20,
            is_popular = false,
            cta_text = 'Essai gratuit 14 jours',
            display_order = 2,
            price = 49
        WHERE tier = 'PRO'
    """))

    # Update ENTERPRISE tier
    conn.execute(sa.text("""
        UPDATE public.subscription_quotas
        SET display_name = 'Enterprise',
            description = 'Pour les grandes équipes',
            annual_discount_percent = 20,
            is_popular = false,
            cta_text = 'Nous contacter',
            display_order = 3,
            price = 199
        WHERE tier = 'ENTERPRISE'
    """))

    # 4. Seed features for each tier
    # Get quota IDs
    result = conn.execute(sa.text("""
        SELECT id, tier FROM public.subscription_quotas
    """))
    quota_ids = {row[1]: row[0] for row in result}

    # FREE features
    if "FREE" in quota_ids:
        free_id = quota_ids["FREE"]
        conn.execute(sa.text("""
            INSERT INTO public.subscription_features (subscription_quota_id, feature_text, display_order)
            VALUES
                (:quota_id, 'Jusqu''à 50 produits', 0),
                (:quota_id, '1 marketplace', 1),
                (:quota_id, 'Support email', 2)
        """), {"quota_id": free_id})

    # STARTER (Pro) features
    if "STARTER" in quota_ids:
        starter_id = quota_ids["STARTER"]
        conn.execute(sa.text("""
            INSERT INTO public.subscription_features (subscription_quota_id, feature_text, display_order)
            VALUES
                (:quota_id, 'Produits illimités', 0),
                (:quota_id, 'Toutes les marketplaces', 1),
                (:quota_id, 'Génération IA (100/mois)', 2),
                (:quota_id, 'Support prioritaire', 3)
        """), {"quota_id": starter_id})

    # PRO (Business) features
    if "PRO" in quota_ids:
        pro_id = quota_ids["PRO"]
        conn.execute(sa.text("""
            INSERT INTO public.subscription_features (subscription_quota_id, feature_text, display_order)
            VALUES
                (:quota_id, 'Tout le plan Pro', 0),
                (:quota_id, 'Génération IA illimitée', 1),
                (:quota_id, 'API access', 2),
                (:quota_id, 'Support dédié', 3)
        """), {"quota_id": pro_id})

    # ENTERPRISE features
    if "ENTERPRISE" in quota_ids:
        enterprise_id = quota_ids["ENTERPRISE"]
        conn.execute(sa.text("""
            INSERT INTO public.subscription_features (subscription_quota_id, feature_text, display_order)
            VALUES
                (:quota_id, 'Tout illimité', 0),
                (:quota_id, 'Multi-utilisateurs', 1),
                (:quota_id, 'Intégration sur mesure', 2),
                (:quota_id, 'Account manager dédié', 3)
        """), {"quota_id": enterprise_id})


def downgrade() -> None:
    # Drop subscription_features table
    op.drop_index(
        "ix_subscription_features_subscription_quota_id",
        table_name="subscription_features",
        schema="public"
    )
    op.drop_table("subscription_features", schema="public")

    # Remove added columns from subscription_quotas
    op.drop_column("subscription_quotas", "display_order", schema="public")
    op.drop_column("subscription_quotas", "cta_text", schema="public")
    op.drop_column("subscription_quotas", "is_popular", schema="public")
    op.drop_column("subscription_quotas", "annual_discount_percent", schema="public")
    op.drop_column("subscription_quotas", "description", schema="public")
    op.drop_column("subscription_quotas", "display_name", schema="public")
