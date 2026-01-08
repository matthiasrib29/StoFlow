"""populate_sleeve_lengths_translations

Revision ID: 115b8afdd149
Revises: d28e411c3b0f
Create Date: 2026-01-08 18:53:59.784711+01:00

Business Rules (2026-01-08):
- Add/update translations (FR, DE, IT, ES, NL, PL) to sleeve_lengths table
- 4 sleeve length types total
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '115b8afdd149'
down_revision: Union[str, None] = 'd28e411c3b0f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Translation data: name_en -> (name_fr, name_de, name_it, name_es, name_nl, name_pl)
TRANSLATIONS = {
    '3/4 sleeve': ('Manches 3/4', '3/4-Arm', 'Manica 3/4', 'Manga 3/4', '3/4 mouw', 'Rękaw 3/4'),
    'Long sleeve': ('Manches longues', 'Langarm', 'Manica lunga', 'Manga larga', 'Lange mouw', 'Długi rękaw'),
    'Short sleeve': ('Manches courtes', 'Kurzarm', 'Manica corta', 'Manga corta', 'Korte mouw', 'Krótki rękaw'),
    'Sleeveless': ('Sans manches', 'Ärmellos', 'Senza maniche', 'Sin mangas', 'Mouwloos', 'Bez rękawów'),
}


def upgrade() -> None:
    """Add/update translations (FR, DE, IT, ES, NL, PL) to sleeve_lengths."""
    conn = op.get_bind()

    for name_en, (name_fr, name_de, name_it, name_es, name_nl, name_pl) in TRANSLATIONS.items():
        conn.execute(
            text("""
                UPDATE product_attributes.sleeve_lengths
                SET name_fr = :name_fr,
                    name_de = :name_de,
                    name_it = :name_it,
                    name_es = :name_es,
                    name_nl = :name_nl,
                    name_pl = :name_pl
                WHERE name_en = :name_en
            """),
            {
                'name_en': name_en,
                'name_fr': name_fr,
                'name_de': name_de,
                'name_it': name_it,
                'name_es': name_es,
                'name_nl': name_nl,
                'name_pl': name_pl,
            }
        )


def downgrade() -> None:
    """Remove translations (FR, DE, IT, ES, NL, PL) from sleeve_lengths."""
    conn = op.get_bind()

    for name_en in TRANSLATIONS.keys():
        conn.execute(
            text("""
                UPDATE product_attributes.sleeve_lengths
                SET name_fr = NULL,
                    name_de = NULL,
                    name_it = NULL,
                    name_es = NULL,
                    name_nl = NULL,
                    name_pl = NULL
                WHERE name_en = :name_en
            """),
            {'name_en': name_en}
        )
