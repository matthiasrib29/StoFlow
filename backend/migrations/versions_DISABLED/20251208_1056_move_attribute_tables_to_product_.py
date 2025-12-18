"""move_attribute_tables_to_product_attributes_schema

Revision ID: 4f3b04388fe7
Revises: ba7bb9ecdbf4
Create Date: 2025-12-08 10:56:20.796288+01:00

Cette migration documente la refactorisation architecturale pour déplacer
toutes les tables d'attributs produit du schema 'public' vers un nouveau
schema dédié 'product_attributes'.

Business rationale (2025-12-08):
- Meilleure séparation des responsabilités
- Organisation plus claire du code
- Facilite la gestion des permissions
- Améliore la scalabilité

Tables migrées:
- categories (avec 65 catégories de vêtements)
- brands
- colors
- conditions
- sizes
- materials
- seasons

IMPORTANT: Cette migration a déjà été appliquée manuellement sur la base de données.
Elle sert uniquement à documenter le changement pour les déploiements futurs.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4f3b04388fe7'
down_revision: Union[str, None] = 'ba7bb9ecdbf4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Refactorisation: Déplacement des tables d'attributs produit vers schema product_attributes.

    ATTENTION: Cette migration a déjà été appliquée manuellement.
    Sur une nouvelle installation, exécuter:
    1. CREATE SCHEMA IF NOT EXISTS product_attributes;
    2. ALTER TABLE public.categories SET SCHEMA product_attributes;
    3. ALTER TABLE public.brands SET SCHEMA product_attributes;
    4. ALTER TABLE public.colors SET SCHEMA product_attributes;
    5. ALTER TABLE public.conditions SET SCHEMA product_attributes;
    6. ALTER TABLE public.sizes SET SCHEMA product_attributes;
    7. ALTER TABLE public.materials SET SCHEMA product_attributes;
    8. ALTER TABLE public.seasons SET SCHEMA product_attributes;
    """
    # Cette migration est documentaire seulement - les opérations ont déjà été effectuées
    # Pour une nouvelle installation, décommenter les lignes suivantes:

    # op.execute("CREATE SCHEMA IF NOT EXISTS product_attributes")
    # op.execute("ALTER TABLE public.categories SET SCHEMA product_attributes")
    # op.execute("ALTER TABLE public.brands SET SCHEMA product_attributes")
    # op.execute("ALTER TABLE public.colors SET SCHEMA product_attributes")
    # op.execute("ALTER TABLE public.conditions SET SCHEMA product_attributes")
    # op.execute("ALTER TABLE public.sizes SET SCHEMA product_attributes")
    # op.execute("ALTER TABLE public.materials SET SCHEMA product_attributes")
    # op.execute("ALTER TABLE public.seasons SET SCHEMA product_attributes")
    pass


def downgrade() -> None:
    """
    Rollback: Déplacement des tables de product_attributes vers public.

    ATTENTION: Cette opération déplace les tables mais peut casser les FK existantes.
    """
    # Pour rollback, décommenter les lignes suivantes:

    # op.execute("ALTER TABLE product_attributes.seasons SET SCHEMA public")
    # op.execute("ALTER TABLE product_attributes.materials SET SCHEMA public")
    # op.execute("ALTER TABLE product_attributes.sizes SET SCHEMA public")
    # op.execute("ALTER TABLE product_attributes.conditions SET SCHEMA public")
    # op.execute("ALTER TABLE product_attributes.colors SET SCHEMA public")
    # op.execute("ALTER TABLE product_attributes.brands SET SCHEMA public")
    # op.execute("ALTER TABLE product_attributes.categories SET SCHEMA public")
    # op.execute("DROP SCHEMA IF EXISTS product_attributes CASCADE")
    pass
