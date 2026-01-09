"""add_missing_sizes_for_dev_sync

Revision ID: 029b9f955564
Revises: 20260105_1500
Create Date: 2026-01-06 11:32:05.393388+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '029b9f955564'
down_revision: Union[str, None] = '20260105_1500'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Sizes manquantes à ajouter (synchronisation dev -> prod)
MISSING_SIZES = [
    {
        'name_en': 'W38/L26',
        'name_fr': 'W38/L26',
        'name_de': 'W38/L26',
        'name_it': 'W38/L26',
        'name_es': 'W38/L26',
        'name_nl': 'W38/L26',
        'name_pl': 'W38/L26',
        'ebay_size': None,
        'etsy_size': None,
        'vinted_women_id': 311,
        'vinted_men_id': 1644,
    },
    {
        'name_en': 'TAILLE UNIQUE',
        'name_fr': 'TAILLE UNIQUE',
        'name_de': 'TAILLE UNIQUE',
        'name_it': 'TAILLE UNIQUE',
        'name_es': 'TAILLE UNIQUE',
        'name_nl': 'TAILLE UNIQUE',
        'name_pl': 'TAILLE UNIQUE',
        'ebay_size': None,
        'etsy_size': None,
        'vinted_women_id': None,
        'vinted_men_id': None,
    },
    {
        'name_en': 'W22/L30',
        'name_fr': 'W22/L30',
        'name_de': 'W22/L30',
        'name_it': 'W22/L30',
        'name_es': 'W22/L30',
        'name_nl': 'W22/L30',
        'name_pl': 'W22/L30',
        'ebay_size': None,
        'etsy_size': None,
        'vinted_women_id': None,
        'vinted_men_id': None,
    },
    {
        'name_en': 'W338/L28',
        'name_fr': 'W338/L28',
        'name_de': 'W338/L28',
        'name_it': 'W338/L28',
        'name_es': 'W338/L28',
        'name_nl': 'W338/L28',
        'name_pl': 'W338/L28',
        'ebay_size': None,
        'etsy_size': None,
        'vinted_women_id': None,
        'vinted_men_id': None,
    },
    {
        'name_en': 'W36/L38',
        'name_fr': 'W36/L38',
        'name_de': 'W36/L38',
        'name_it': 'W36/L38',
        'name_es': 'W36/L38',
        'name_nl': 'W36/L38',
        'name_pl': 'W36/L38',
        'ebay_size': None,
        'etsy_size': None,
        'vinted_women_id': None,
        'vinted_men_id': None,
    },
    {
        'name_en': 'W38/L24',
        'name_fr': 'W38/L24',
        'name_de': 'W38/L24',
        'name_it': 'W38/L24',
        'name_es': 'W38/L24',
        'name_nl': 'W38/L24',
        'name_pl': 'W38/L24',
        'ebay_size': None,
        'etsy_size': None,
        'vinted_women_id': None,
        'vinted_men_id': None,
    },
    {
        'name_en': 'W40/L26',
        'name_fr': 'W40/L26',
        'name_de': 'W40/L26',
        'name_it': 'W40/L26',
        'name_es': 'W40/L26',
        'name_nl': 'W40/L26',
        'name_pl': 'W40/L26',
        'ebay_size': None,
        'etsy_size': None,
        'vinted_women_id': None,
        'vinted_men_id': None,
    },
    {
        'name_en': 'W48/L26',
        'name_fr': 'W48/L26',
        'name_de': 'W48/L26',
        'name_it': 'W48/L26',
        'name_es': 'W48/L26',
        'name_nl': 'W48/L26',
        'name_pl': 'W48/L26',
        'ebay_size': None,
        'etsy_size': None,
        'vinted_women_id': None,
        'vinted_men_id': None,
    },
    {
        'name_en': 'W50/L30',
        'name_fr': 'W50/L30',
        'name_de': 'W50/L30',
        'name_it': 'W50/L30',
        'name_es': 'W50/L30',
        'name_nl': 'W50/L30',
        'name_pl': 'W50/L30',
        'ebay_size': None,
        'etsy_size': None,
        'vinted_women_id': None,
        'vinted_men_id': None,
    },
]


def upgrade() -> None:
    conn = op.get_bind()

    for size in MISSING_SIZES:
        # Insert uniquement si n'existe pas déjà (idempotent)
        conn.execute(
            sa.text("""
                INSERT INTO product_attributes.sizes
                    (name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl,
                     ebay_size, etsy_size, vinted_women_id, vinted_men_id)
                VALUES
                    (:name_en, :name_fr, :name_de, :name_it, :name_es, :name_nl, :name_pl,
                     :ebay_size, :etsy_size, :vinted_women_id, :vinted_men_id)
                ON CONFLICT (name_en) DO NOTHING
            """),
            size
        )


def downgrade() -> None:
    conn = op.get_bind()

    for size in MISSING_SIZES:
        conn.execute(
            sa.text("""
                DELETE FROM product_attributes.sizes
                WHERE name_en = :name_en
            """),
            {'name_en': size['name_en']}
        )
