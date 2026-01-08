"""populate_seasons_translations

Revision ID: d28e411c3b0f
Revises: c56fdfee5458
Create Date: 2026-01-08 18:53:59.540287+01:00

Business Rules (2026-01-08):
- Add/update translations (FR, DE, IT, ES, NL, PL) to seasons table
- 5 seasons total
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'd28e411c3b0f'
down_revision: Union[str, None] = 'c56fdfee5458'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Translation data: name_en -> (name_fr, name_de, name_it, name_es, name_nl, name_pl)
TRANSLATIONS = {
    'Spring': ('Printemps', 'Frühling', 'Primavera', 'Primavera', 'Lente', 'Wiosna'),
    'Summer': ('Été', 'Sommer', 'Estate', 'Verano', 'Zomer', 'Lato'),
    'Autumn': ('Automne', 'Herbst', 'Autunno', 'Otoño', 'Herfst', 'Jesień'),
    'Winter': ('Hiver', 'Winter', 'Inverno', 'Invierno', 'Winter', 'Zima'),
    'All seasons': ('Toutes saisons', 'Ganzjährig', 'Tutte le stagioni', 'Todas las temporadas', 'Alle seizoenen', 'Wszystkie pory roku'),
}


def upgrade() -> None:
    """Add/update translations (FR, DE, IT, ES, NL, PL) to seasons."""
    conn = op.get_bind()

    for name_en, (name_fr, name_de, name_it, name_es, name_nl, name_pl) in TRANSLATIONS.items():
        conn.execute(
            text("""
                UPDATE product_attributes.seasons
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
    """Remove translations (FR, DE, IT, ES, NL, PL) from seasons."""
    conn = op.get_bind()

    for name_en in TRANSLATIONS.keys():
        conn.execute(
            text("""
                UPDATE product_attributes.seasons
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
