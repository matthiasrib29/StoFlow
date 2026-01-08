"""populate_trends_translations

Revision ID: 16d3cf7c978a
Revises: 6fa36291de2a
Create Date: 2026-01-08 18:49:23.117150+01:00

Business Rules (2026-01-08):
- Add/update translations (FR, DE, IT, ES, NL, PL) to trends table
- 41 fashion trends total
- Most trends are international terms kept as-is
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '16d3cf7c978a'
down_revision: Union[str, None] = '6fa36291de2a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Translation data: name_en -> (name_fr, name_de, name_it, name_es, name_nl, name_pl)
TRANSLATIONS = {
    'Athleisure': ('Athleisure', 'Athleisure', 'Athleisure', 'Athleisure', 'Athleisure', 'Athleisure'),
    'Bohemian': ('Bohème', 'Bohemian', 'Bohémien', 'Bohemio', 'Bohemian', 'Bohema'),
    'Cottagecore': ('Cottagecore', 'Cottagecore', 'Cottagecore', 'Cottagecore', 'Cottagecore', 'Cottagecore'),
    'Dark academia': ('Dark academia', 'Dark Academia', 'Dark academia', 'Dark academia', 'Dark academia', 'Dark academia'),
    'Geek chic': ('Geek chic', 'Geek Chic', 'Geek chic', 'Geek chic', 'Geek chic', 'Geek chic'),
    'Gothic': ('Gothique', 'Gothic', 'Gotico', 'Gótico', 'Gothic', 'Gotycki'),
    'Grunge': ('Grunge', 'Grunge', 'Grunge', 'Grunge', 'Grunge', 'Grunge'),
    'Japanese streetwear': ('Streetwear japonais', 'Japanese Streetwear', 'Streetwear giapponese', 'Streetwear japonés', 'Japanse streetwear', 'Japoński streetwear'),
    'Minimalist': ('Minimaliste', 'Minimalistisch', 'Minimalista', 'Minimalista', 'Minimalistisch', 'Minimalistyczny'),
    'Modern': ('Moderne', 'Modern', 'Moderno', 'Moderno', 'Modern', 'Nowoczesny'),
    'Normcore': ('Normcore', 'Normcore', 'Normcore', 'Normcore', 'Normcore', 'Normcore'),
    'Preppy': ('Preppy', 'Preppy', 'Preppy', 'Preppy', 'Preppy', 'Preppy'),
    'Punk': ('Punk', 'Punk', 'Punk', 'Punk', 'Punk', 'Punk'),
    'Retro': ('Rétro', 'Retro', 'Retrò', 'Retro', 'Retro', 'Retro'),
    'Skater': ('Skater', 'Skater', 'Skater', 'Skater', 'Skater', 'Skater'),
    'Sportswear': ('Sportswear', 'Sportswear', 'Sportswear', 'Sportswear', 'Sportswear', 'Sportswear'),
    'Streetwear': ('Streetwear', 'Streetwear', 'Streetwear', 'Streetwear', 'Streetwear', 'Streetwear'),
    'Techwear': ('Techwear', 'Techwear', 'Techwear', 'Techwear', 'Techwear', 'Techwear'),
    'Vintage': ('Vintage', 'Vintage', 'Vintage', 'Vintage', 'Vintage', 'Vintage'),
    'Western': ('Western', 'Western', 'Western', 'Western', 'Western', 'Western'),
    'Workwear': ('Workwear', 'Workwear', 'Workwear', 'Workwear', 'Workwear', 'Workwear'),
    'Y2k': ('Y2K', 'Y2K', 'Y2K', 'Y2K', 'Y2K', 'Y2K'),
    'Old money': ('Old money', 'Old Money', 'Old money', 'Old money', 'Old money', 'Old money'),
    'Quiet luxury': ('Quiet luxury', 'Quiet Luxury', 'Quiet luxury', 'Quiet luxury', 'Quiet luxury', 'Quiet luxury'),
    'Coquette': ('Coquette', 'Coquette', 'Coquette', 'Coquette', 'Coquette', 'Coquette'),
    'Clean girl': ('Clean girl', 'Clean Girl', 'Clean girl', 'Clean girl', 'Clean girl', 'Clean girl'),
    'Light academia': ('Light academia', 'Light Academia', 'Light academia', 'Light academia', 'Light academia', 'Light academia'),
    'Balletcore': ('Balletcore', 'Balletcore', 'Balletcore', 'Balletcore', 'Balletcore', 'Balletcore'),
    'Gorpcore': ('Gorpcore', 'Gorpcore', 'Gorpcore', 'Gorpcore', 'Gorpcore', 'Gorpcore'),
    'Boho revival': ('Boho revival', 'Boho Revival', 'Boho revival', 'Boho revival', 'Boho revival', 'Boho revival'),
    'Downtown girl': ('Downtown girl', 'Downtown Girl', 'Downtown girl', 'Downtown girl', 'Downtown girl', 'Downtown girl'),
    'Eclectic grandpa': ('Eclectic grandpa', 'Eclectic Grandpa', 'Eclectic grandpa', 'Eclectic grandpa', 'Eclectic grandpa', 'Eclectic grandpa'),
    'Glamoratti': ('Glamoratti', 'Glamoratti', 'Glamoratti', 'Glamoratti', 'Glamoratti', 'Glamoratti'),
    'Indie sleaze': ('Indie sleaze', 'Indie Sleaze', 'Indie sleaze', 'Indie sleaze', 'Indie sleaze', 'Indie sleaze'),
    'Khaki coded': ('Khaki coded', 'Khaki Coded', 'Khaki coded', 'Khaki coded', 'Khaki coded', 'Khaki coded'),
    'Mob wife': ('Mob wife', 'Mob Wife', 'Mob wife', 'Mob wife', 'Mob wife', 'Mob wife'),
    'Neo deco': ('Néo déco', 'Neo Deco', 'Neo deco', 'Neo deco', 'Neo deco', 'Neo deco'),
    'Office siren': ('Office siren', 'Office Siren', 'Office siren', 'Office siren', 'Office siren', 'Office siren'),
    'Poetcore': ('Poetcore', 'Poetcore', 'Poetcore', 'Poetcore', 'Poetcore', 'Poetcore'),
    'Vamp romance': ('Vamp romance', 'Vamp Romance', 'Vamp romance', 'Vamp romance', 'Vamp romance', 'Vamp romance'),
    'Wilderkind': ('Wilderkind', 'Wilderkind', 'Wilderkind', 'Wilderkind', 'Wilderkind', 'Wilderkind'),
}


def upgrade() -> None:
    """Add/update translations (FR, DE, IT, ES, NL, PL) to trends."""
    conn = op.get_bind()

    for name_en, (name_fr, name_de, name_it, name_es, name_nl, name_pl) in TRANSLATIONS.items():
        conn.execute(
            text("""
                UPDATE product_attributes.trends
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
    """Remove translations (FR, DE, IT, ES, NL, PL) from trends."""
    conn = op.get_bind()

    for name_en in TRANSLATIONS.keys():
        conn.execute(
            text("""
                UPDATE product_attributes.trends
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
