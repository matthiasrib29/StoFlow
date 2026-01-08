"""populate_closures_translations

Revision ID: 4886bd185f07
Revises: ec223113457e
Create Date: 2026-01-08 17:18:48.938550+01:00

Business Rules (2026-01-08):
- Add/update translations (FR, DE, IT, ES, NL, PL) to closures table
- 12 closure types total
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '4886bd185f07'
down_revision: Union[str, None] = 'ec223113457e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Translation data: name_en -> (name_fr, name_de, name_it, name_es, name_nl, name_pl)
TRANSLATIONS = {
    'Button fly': ('Braguette à boutons', 'Knopfleiste', 'Patta con bottoni', 'Bragueta de botones', 'Knoopsluiting', 'Rozporek na guziki'),
    'Buttons': ('Boutons', 'Knöpfe', 'Bottoni', 'Botones', 'Knopen', 'Guziki'),
    'Elastic': ('Élastique', 'Gummibund', 'Elastico', 'Elástico', 'Elastiek', 'Guma'),
    'Laces': ('Lacets', 'Schnürung', 'Lacci', 'Cordones', 'Veters', 'Sznurowanie'),
    'Pull-on': ('Enfilable', 'Schlupf', 'Pull-on', 'Sin cierre', 'Pull-on', 'Wciągany'),
    'Zip fly': ('Braguette zippée', 'Reißverschluss', 'Patta con zip', 'Bragueta de cremallera', 'Ritssluiting', 'Rozporek na zamek'),
    'Zipper': ('Fermeture éclair', 'Reißverschluss', 'Cerniera', 'Cremallera', 'Rits', 'Zamek błyskawiczny'),
    'Hook and eye': ('Agrafe', 'Haken und Öse', 'Gancio e occhiello', 'Corchete', 'Haak en oog', 'Haftka'),
    'Snap buttons': ('Boutons-pression', 'Druckknöpfe', 'Bottoni a pressione', 'Botones de presión', 'Drukknopen', 'Zatrzaski'),
    'Toggle': ('Brandebourg', 'Knebelknopf', 'Alamaro', 'Botón de palanca', 'Toggle', 'Szpila'),
    'Velcro': ('Velcro', 'Klettverschluss', 'Velcro', 'Velcro', 'Klittenband', 'Rzep'),
    'Drawstring': ('Cordon de serrage', 'Kordelzug', 'Coulisse', 'Cordón ajustable', 'Trekkoord', 'Ściągacz'),
}


def upgrade() -> None:
    """Add/update translations (FR, DE, IT, ES, NL, PL) to closures."""
    conn = op.get_bind()

    for name_en, (name_fr, name_de, name_it, name_es, name_nl, name_pl) in TRANSLATIONS.items():
        conn.execute(
            text("""
                UPDATE product_attributes.closures
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
    """Remove translations (FR, DE, IT, ES, NL, PL) from closures."""
    conn = op.get_bind()

    for name_en in TRANSLATIONS.keys():
        conn.execute(
            text("""
                UPDATE product_attributes.closures
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
