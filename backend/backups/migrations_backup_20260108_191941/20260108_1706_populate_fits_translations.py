"""populate_fits_translations

Revision ID: c6d0a4b3e5f2
Revises: b5c9f3a2d4e1
Create Date: 2026-01-08 17:06:34.123456+01:00

Business Rules (2026-01-08):
- Add/update translations (FR, DE, IT, ES, NL, PL) to fits table
- 13 fits total
- Some FR translations were missing, now completed
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'c6d0a4b3e5f2'
down_revision: Union[str, None] = 'b5c9f3a2d4e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Translation data: name_en -> (name_fr, name_de, name_it, name_es, name_nl, name_pl)
TRANSLATIONS = {
    'Slim': ('Slim', 'Slim', 'Slim', 'Slim', 'Slim', 'Slim'),
    'Regular': ('Regular', 'Regular', 'Regular', 'Regular', 'Regular', 'Regular'),
    'Relaxed': ('Relaxed', 'Relaxed', 'Relaxed', 'Relaxed', 'Relaxed', 'Relaxed'),
    'Oversized': ('Oversize', 'Oversized', 'Oversize', 'Oversize', 'Oversized', 'Oversize'),
    'Tight': ('Moulant', 'Eng', 'Aderente', 'Ajustado', 'Strak', 'Obcisły'),
    'Loose': ('Loose', 'Weit', 'Ampio', 'Holgado', 'Ruim', 'Luźny'),
    'Athletic': ('Athlétique', 'Athletisch', 'Atletico', 'Atlético', 'Atletisch', 'Atletyczny'),
    'Baggy': ('Baggy', 'Baggy', 'Baggy', 'Baggy', 'Baggy', 'Baggy'),
    'Bootcut': ('Bootcut', 'Bootcut', 'Bootcut', 'Bootcut', 'Bootcut', 'Bootcut'),
    'Flare': ('Évasé', 'Schlaghose', 'Svasato', 'Acampanado', 'Flared', 'Dzwony'),
    'Skinny': ('Skinny', 'Skinny', 'Skinny', 'Skinny', 'Skinny', 'Skinny'),
    'Straight': ('Droit', 'Gerade', 'Dritto', 'Recto', 'Recht', 'Prosty'),
    'Balloon': ('Balloon', 'Ballon', 'Palloncino', 'Globo', 'Ballon', 'Balonowy'),
}


def upgrade() -> None:
    """Add/update translations (FR, DE, IT, ES, NL, PL) to fits."""
    conn = op.get_bind()

    for name_en, (name_fr, name_de, name_it, name_es, name_nl, name_pl) in TRANSLATIONS.items():
        conn.execute(
            text("""
                UPDATE product_attributes.fits
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
    """Remove translations (FR, DE, IT, ES, NL, PL) from fits."""
    conn = op.get_bind()

    for name_en in TRANSLATIONS.keys():
        conn.execute(
            text("""
                UPDATE product_attributes.fits
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
