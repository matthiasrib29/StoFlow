"""Create documentation tables (doc_categories, doc_articles)

Revision ID: 20251224_1900
Revises: 20251224_1800
Create Date: 2024-12-24 19:00:00

This migration creates:
1. doc_categories table - for organizing documentation
2. doc_articles table - for storing article content (Markdown)
3. Seeds initial categories (Guide, FAQ)
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = "20251224_1900"
down_revision = "20251224_1800"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create doc_categories table
    op.create_table(
        "doc_categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False, comment="URL-friendly identifier"),
        sa.Column("name", sa.String(100), nullable=False, comment="Display name"),
        sa.Column("description", sa.Text(), nullable=True, comment="Short description"),
        sa.Column("icon", sa.String(50), nullable=True, comment="PrimeIcons class"),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0", comment="Order in navigation"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true", comment="Whether visible"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="public"
    )
    op.create_index("ix_doc_categories_slug", "doc_categories", ["slug"], unique=True, schema="public")
    op.create_index("ix_doc_categories_display_order", "doc_categories", ["display_order"], schema="public")

    # 2. Create doc_articles table
    op.create_table(
        "doc_articles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False, comment="Parent category ID"),
        sa.Column("slug", sa.String(200), nullable=False, comment="URL-friendly identifier"),
        sa.Column("title", sa.String(200), nullable=False, comment="Article title"),
        sa.Column("summary", sa.String(500), nullable=True, comment="Short excerpt"),
        sa.Column("content", sa.Text(), nullable=False, comment="Markdown content"),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0", comment="Order within category"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true", comment="Whether visible"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["public.doc_categories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema="public"
    )
    op.create_index("ix_doc_articles_slug", "doc_articles", ["slug"], unique=True, schema="public")
    op.create_index("ix_doc_articles_category_id", "doc_articles", ["category_id"], schema="public")
    op.create_index("ix_doc_articles_display_order", "doc_articles", ["display_order"], schema="public")

    # 3. Seed initial categories
    op.execute("""
        INSERT INTO public.doc_categories (slug, name, description, icon, display_order, is_active)
        VALUES
            ('guide', 'Guide d''utilisation', 'Apprenez à utiliser Stoflow étape par étape', 'pi-book', 0, true),
            ('faq', 'FAQ', 'Questions fréquemment posées', 'pi-question-circle', 1, true)
    """)

    # 4. Seed initial articles
    op.execute("""
        INSERT INTO public.doc_articles (category_id, slug, title, summary, content, display_order, is_active)
        VALUES
            (
                (SELECT id FROM public.doc_categories WHERE slug = 'guide'),
                'premiers-pas',
                'Premiers pas avec Stoflow',
                'Découvrez comment démarrer avec Stoflow et configurer votre compte.',
                '# Premiers pas avec Stoflow

Bienvenue sur Stoflow ! Ce guide vous accompagne dans vos premiers pas.

## 1. Créer votre compte

Rendez-vous sur la page d''inscription et remplissez le formulaire avec vos informations.

## 2. Connecter votre première marketplace

Une fois connecté, accédez à **Paramètres > Intégrations** pour connecter Vinted, eBay ou Etsy.

## 3. Créer votre premier produit

Cliquez sur **Produits > Créer un produit** pour ajouter votre premier article.

---

Besoin d''aide ? Consultez notre FAQ ou contactez notre support.',
                0,
                true
            ),
            (
                (SELECT id FROM public.doc_categories WHERE slug = 'guide'),
                'creer-produit',
                'Comment créer un produit',
                'Apprenez à créer et publier vos produits sur les marketplaces.',
                '# Comment créer un produit

Ce guide vous explique comment créer un produit dans Stoflow.

## Étape 1 : Informations de base

- **Titre** : Le nom de votre produit
- **Description** : Une description détaillée
- **Prix** : Le prix de vente

## Étape 2 : Photos

Ajoutez jusqu''à 10 photos de votre produit. La première photo sera la photo principale.

## Étape 3 : Attributs

Sélectionnez la catégorie, la taille, la couleur et les autres attributs.

## Étape 4 : Publication

Cliquez sur **Publier** pour envoyer votre produit sur les marketplaces connectées.',
                1,
                true
            ),
            (
                (SELECT id FROM public.doc_categories WHERE slug = 'faq'),
                'abonnement',
                'Questions sur les abonnements',
                'Tout savoir sur les plans et tarifs Stoflow.',
                '# Questions sur les abonnements

## Quels sont les plans disponibles ?

Stoflow propose 4 plans :
- **Gratuit** : Pour découvrir la plateforme (50 produits, 1 marketplace)
- **Pro** : Pour les vendeurs actifs (500 produits, toutes marketplaces)
- **Business** : Pour les professionnels (2000 produits)
- **Enterprise** : Pour les grandes équipes (illimité)

## Puis-je changer de plan ?

Oui, vous pouvez upgrader ou downgrader à tout moment depuis **Paramètres > Abonnement**.

## Comment fonctionne la facturation ?

La facturation est mensuelle ou annuelle (avec 20% de réduction).',
                0,
                true
            )
    """)


def downgrade() -> None:
    # Drop tables in reverse order (articles first due to FK)
    op.drop_index("ix_doc_articles_display_order", table_name="doc_articles", schema="public")
    op.drop_index("ix_doc_articles_category_id", table_name="doc_articles", schema="public")
    op.drop_index("ix_doc_articles_slug", table_name="doc_articles", schema="public")
    op.drop_table("doc_articles", schema="public")

    op.drop_index("ix_doc_categories_display_order", table_name="doc_categories", schema="public")
    op.drop_index("ix_doc_categories_slug", table_name="doc_categories", schema="public")
    op.drop_table("doc_categories", schema="public")
