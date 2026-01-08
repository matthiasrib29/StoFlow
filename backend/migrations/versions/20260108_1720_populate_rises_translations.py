"""populate_rises_translations

Revision ID: 6fa36291de2a
Revises: 4a281fb619e9
Create Date: 2026-01-08 17:20:49.304906+01:00

Business Rules (2026-01-08):
- Add/update translations (FR, DE, IT, ES, NL, PL) to rises table
- 6 rise types total
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '6fa36291de2a'
down_revision: Union[str, None] = '4a281fb619e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Translation data: name_en -> (name_fr, name_de, name_it, name_es, name_nl, name_pl)
TRANSLATIONS = {
    'High-rise': ('Taille haute', 'High-Rise', 'Vita alta', 'Tiro alto', 'Hoge taille', 'Wysoki stan'),
    'Low-rise': ('Taille basse', 'Low-Rise', 'Vita bassa', 'Tiro bajo', 'Lage taille', 'Niski stan'),
    'Mid-rise': ('Taille moyenne', 'Mid-Rise', 'Vita media', 'Tiro medio', 'Middelhoge taille', 'Średni stan'),
    'Regular rise': ('Taille normale', 'Regular Rise', 'Vita normale', 'Tiro normal', 'Normale taille', 'Normalny stan'),
    'Super low-rise': ('Taille très basse', 'Super Low-Rise', 'Vita molto bassa', 'Tiro muy bajo', 'Zeer lage taille', 'Bardzo niski stan'),
    'Ultra high-rise': ('Taille très haute', 'Ultra High-Rise', 'Vita molto alta', 'Tiro muy alto', 'Zeer hoge taille', 'Bardzo wysoki stan'),
}


def upgrade() -> None:
    """Add/update translations (FR, DE, IT, ES, NL, PL) to rises."""
    conn = op.get_bind()

    for name_en, (name_fr, name_de, name_it, name_es, name_nl, name_pl) in TRANSLATIONS.items():
        conn.execute(
            text("""
                UPDATE product_attributes.rises
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
    """Remove translations (FR, DE, IT, ES, NL, PL) from rises."""
    conn = op.get_bind()

    for name_en in TRANSLATIONS.keys():
        conn.execute(
            text("""
                UPDATE product_attributes.rises
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
