"""add_new_product_attribute_tables

Revision ID: 22e1178aebb9
Revises: f07d95981520
Create Date: 2025-12-08 14:20:13.446510+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '22e1178aebb9'
down_revision: Union[str, None] = 'f07d95981520'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ===== CREATE NEW ATTRIBUTE TABLES =====

    # Table: condition_sups
    op.create_table(
        'condition_sups',
        sa.Column('name_en', sa.String(length=100), nullable=False, comment='Nom de la condition supplémentaire (EN)'),
        sa.Column('name_fr', sa.String(length=100), nullable=True, comment='Nom de la condition supplémentaire (FR)'),
        sa.Column('name_de', sa.String(length=100), nullable=True, comment='Nom de la condition supplémentaire (DE)'),
        sa.Column('name_it', sa.String(length=100), nullable=True, comment='Nom de la condition supplémentaire (IT)'),
        sa.Column('name_es', sa.String(length=100), nullable=True, comment='Nom de la condition supplémentaire (ES)'),
        sa.Column('name_nl', sa.String(length=100), nullable=True, comment='Nom de la condition supplémentaire (NL)'),
        sa.Column('name_pl', sa.String(length=100), nullable=True, comment='Nom de la condition supplémentaire (PL)'),
        sa.PrimaryKeyConstraint('name_en'),
        schema='public'
    )
    op.create_index(op.f('ix_public_condition_sups_name_en'), 'condition_sups', ['name_en'], unique=False, schema='public')

    # Table: closures
    op.create_table(
        'closures',
        sa.Column('name_en', sa.String(length=100), nullable=False, comment='Nom de la fermeture (EN)'),
        sa.Column('name_fr', sa.String(length=100), nullable=True, comment='Nom de la fermeture (FR)'),
        sa.Column('name_de', sa.String(length=100), nullable=True, comment='Nom de la fermeture (DE)'),
        sa.Column('name_it', sa.String(length=100), nullable=True, comment='Nom de la fermeture (IT)'),
        sa.Column('name_es', sa.String(length=100), nullable=True, comment='Nom de la fermeture (ES)'),
        sa.Column('name_nl', sa.String(length=100), nullable=True, comment='Nom de la fermeture (NL)'),
        sa.Column('name_pl', sa.String(length=100), nullable=True, comment='Nom de la fermeture (PL)'),
        sa.PrimaryKeyConstraint('name_en'),
        schema='public'
    )
    op.create_index(op.f('ix_public_closures_name_en'), 'closures', ['name_en'], unique=False, schema='public')

    # Table: decades
    op.create_table(
        'decades',
        sa.Column('name_en', sa.String(length=100), nullable=False, comment='Nom de la décennie (EN)'),
        sa.Column('name_fr', sa.String(length=100), nullable=True, comment='Nom de la décennie (FR)'),
        sa.Column('name_de', sa.String(length=100), nullable=True, comment='Nom de la décennie (DE)'),
        sa.Column('name_it', sa.String(length=100), nullable=True, comment='Nom de la décennie (IT)'),
        sa.Column('name_es', sa.String(length=100), nullable=True, comment='Nom de la décennie (ES)'),
        sa.Column('name_nl', sa.String(length=100), nullable=True, comment='Nom de la décennie (NL)'),
        sa.Column('name_pl', sa.String(length=100), nullable=True, comment='Nom de la décennie (PL)'),
        sa.PrimaryKeyConstraint('name_en'),
        schema='public'
    )
    op.create_index(op.f('ix_public_decades_name_en'), 'decades', ['name_en'], unique=False, schema='public')

    # Table: origins
    op.create_table(
        'origins',
        sa.Column('name_en', sa.String(length=100), nullable=False, comment='Nom de l\'origine (EN)'),
        sa.Column('name_fr', sa.String(length=100), nullable=True, comment='Nom de l\'origine (FR)'),
        sa.Column('name_de', sa.String(length=100), nullable=True, comment='Nom de l\'origine (DE)'),
        sa.Column('name_it', sa.String(length=100), nullable=True, comment='Nom de l\'origine (IT)'),
        sa.Column('name_es', sa.String(length=100), nullable=True, comment='Nom de l\'origine (ES)'),
        sa.Column('name_nl', sa.String(length=100), nullable=True, comment='Nom de l\'origine (NL)'),
        sa.Column('name_pl', sa.String(length=100), nullable=True, comment='Nom de l\'origine (PL)'),
        sa.PrimaryKeyConstraint('name_en'),
        schema='public'
    )
    op.create_index(op.f('ix_public_origins_name_en'), 'origins', ['name_en'], unique=False, schema='public')

    # Table: rises
    op.create_table(
        'rises',
        sa.Column('name_en', sa.String(length=100), nullable=False, comment='Nom de la hauteur de taille (EN)'),
        sa.Column('name_fr', sa.String(length=100), nullable=True, comment='Nom de la hauteur de taille (FR)'),
        sa.Column('name_de', sa.String(length=100), nullable=True, comment='Nom de la hauteur de taille (DE)'),
        sa.Column('name_it', sa.String(length=100), nullable=True, comment='Nom de la hauteur de taille (IT)'),
        sa.Column('name_es', sa.String(length=100), nullable=True, comment='Nom de la hauteur de taille (ES)'),
        sa.Column('name_nl', sa.String(length=100), nullable=True, comment='Nom de la hauteur de taille (NL)'),
        sa.Column('name_pl', sa.String(length=100), nullable=True, comment='Nom de la hauteur de taille (PL)'),
        sa.PrimaryKeyConstraint('name_en'),
        schema='public'
    )
    op.create_index(op.f('ix_public_rises_name_en'), 'rises', ['name_en'], unique=False, schema='public')

    # Table: sleeve_lengths
    op.create_table(
        'sleeve_lengths',
        sa.Column('name_en', sa.String(length=100), nullable=False, comment='Nom de la longueur de manche (EN)'),
        sa.Column('name_fr', sa.String(length=100), nullable=True, comment='Nom de la longueur de manche (FR)'),
        sa.Column('name_de', sa.String(length=100), nullable=True, comment='Nom de la longueur de manche (DE)'),
        sa.Column('name_it', sa.String(length=100), nullable=True, comment='Nom de la longueur de manche (IT)'),
        sa.Column('name_es', sa.String(length=100), nullable=True, comment='Nom de la longueur de manche (ES)'),
        sa.Column('name_nl', sa.String(length=100), nullable=True, comment='Nom de la longueur de manche (NL)'),
        sa.Column('name_pl', sa.String(length=100), nullable=True, comment='Nom de la longueur de manche (PL)'),
        sa.PrimaryKeyConstraint('name_en'),
        schema='public'
    )
    op.create_index(op.f('ix_public_sleeve_lengths_name_en'), 'sleeve_lengths', ['name_en'], unique=False, schema='public')

    # Table: trends
    op.create_table(
        'trends',
        sa.Column('name_en', sa.String(length=100), nullable=False, comment='Nom de la tendance (EN)'),
        sa.Column('name_fr', sa.String(length=100), nullable=True, comment='Nom de la tendance (FR)'),
        sa.Column('name_de', sa.String(length=100), nullable=True, comment='Nom de la tendance (DE)'),
        sa.Column('name_it', sa.String(length=100), nullable=True, comment='Nom de la tendance (IT)'),
        sa.Column('name_es', sa.String(length=100), nullable=True, comment='Nom de la tendance (ES)'),
        sa.Column('name_nl', sa.String(length=100), nullable=True, comment='Nom de la tendance (NL)'),
        sa.Column('name_pl', sa.String(length=100), nullable=True, comment='Nom de la tendance (PL)'),
        sa.PrimaryKeyConstraint('name_en'),
        schema='public'
    )
    op.create_index(op.f('ix_public_trends_name_en'), 'trends', ['name_en'], unique=False, schema='public')

    # Table: unique_features
    op.create_table(
        'unique_features',
        sa.Column('name_en', sa.String(length=100), nullable=False, comment='Nom de la caractéristique unique (EN)'),
        sa.Column('name_fr', sa.String(length=100), nullable=True, comment='Nom de la caractéristique unique (FR)'),
        sa.Column('name_de', sa.String(length=100), nullable=True, comment='Nom de la caractéristique unique (DE)'),
        sa.Column('name_it', sa.String(length=100), nullable=True, comment='Nom de la caractéristique unique (IT)'),
        sa.Column('name_es', sa.String(length=100), nullable=True, comment='Nom de la caractéristique unique (ES)'),
        sa.Column('name_nl', sa.String(length=100), nullable=True, comment='Nom de la caractéristique unique (NL)'),
        sa.Column('name_pl', sa.String(length=100), nullable=True, comment='Nom de la caractéristique unique (PL)'),
        sa.PrimaryKeyConstraint('name_en'),
        schema='public'
    )
    op.create_index(op.f('ix_public_unique_features_name_en'), 'unique_features', ['name_en'], unique=False, schema='public')


def downgrade() -> None:
    # ===== DROP ALL NEW ATTRIBUTE TABLES =====
    op.drop_index(op.f('ix_public_unique_features_name_en'), table_name='unique_features', schema='public')
    op.drop_table('unique_features', schema='public')

    op.drop_index(op.f('ix_public_trends_name_en'), table_name='trends', schema='public')
    op.drop_table('trends', schema='public')

    op.drop_index(op.f('ix_public_sleeve_lengths_name_en'), table_name='sleeve_lengths', schema='public')
    op.drop_table('sleeve_lengths', schema='public')

    op.drop_index(op.f('ix_public_rises_name_en'), table_name='rises', schema='public')
    op.drop_table('rises', schema='public')

    op.drop_index(op.f('ix_public_origins_name_en'), table_name='origins', schema='public')
    op.drop_table('origins', schema='public')

    op.drop_index(op.f('ix_public_decades_name_en'), table_name='decades', schema='public')
    op.drop_table('decades', schema='public')

    op.drop_index(op.f('ix_public_closures_name_en'), table_name='closures', schema='public')
    op.drop_table('closures', schema='public')

    op.drop_index(op.f('ix_public_condition_sups_name_en'), table_name='condition_sups', schema='public')
    op.drop_table('condition_sups', schema='public')
