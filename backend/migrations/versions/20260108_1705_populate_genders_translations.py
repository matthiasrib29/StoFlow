"""populate_genders_translations

Revision ID: b5c9f3a2d4e1
Revises: a4d8e2f9c1b3
Create Date: 2026-01-08 17:05:23.123456+01:00

Business Rules (2026-01-08):
- Add missing translations (DE, IT, ES, NL, PL) to genders table
- FR translations already complete, not modified
- 5 genders total
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'b5c9f3a2d4e1'
down_revision: Union[str, None] = 'a4d8e2f9c1b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Translation data: name_en -> (name_de, name_it, name_es, name_nl, name_pl)
TRANSLATIONS = {
    'Boys': ('Jungen', 'Bambini', 'Niños', 'Jongens', 'Chłopcy'),
    'Girls': ('Mädchen', 'Bambine', 'Niñas', 'Meisjes', 'Dziewczynki'),
    'Men': ('Herren', 'Uomo', 'Hombre', 'Heren', 'Mężczyźni'),
    'Unisex': ('Unisex', 'Unisex', 'Unisex', 'Unisex', 'Unisex'),
    'Women': ('Damen', 'Donna', 'Mujer', 'Dames', 'Kobiety'),
}


def upgrade() -> None:
    """Add missing translations (DE, IT, ES, NL, PL) to genders."""
    conn = op.get_bind()

    for name_en, (name_de, name_it, name_es, name_nl, name_pl) in TRANSLATIONS.items():
        conn.execute(
            text("""
                UPDATE product_attributes.genders
                SET name_de = :name_de,
                    name_it = :name_it,
                    name_es = :name_es,
                    name_nl = :name_nl,
                    name_pl = :name_pl
                WHERE name_en = :name_en
            """),
            {
                'name_en': name_en,
                'name_de': name_de,
                'name_it': name_it,
                'name_es': name_es,
                'name_nl': name_nl,
                'name_pl': name_pl,
            }
        )


def downgrade() -> None:
    """Remove translations (DE, IT, ES, NL, PL) from genders."""
    conn = op.get_bind()

    for name_en in TRANSLATIONS.keys():
        conn.execute(
            text("""
                UPDATE product_attributes.genders
                SET name_de = NULL,
                    name_it = NULL,
                    name_es = NULL,
                    name_nl = NULL,
                    name_pl = NULL
                WHERE name_en = :name_en
            """),
            {'name_en': name_en}
        )
