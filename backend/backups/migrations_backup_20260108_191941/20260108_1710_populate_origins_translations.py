"""populate_origins_translations

Revision ID: e8f2c6d5a7b4
Revises: d7e1b5c4f6a3
Create Date: 2026-01-08 17:10:56.123456+01:00

Business Rules (2026-01-08):
- Add missing translations (DE, IT, ES, NL, PL) to origins table
- FR translations already complete, not modified
- 48 countries total
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'e8f2c6d5a7b4'
down_revision: Union[str, None] = 'd7e1b5c4f6a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Translation data: name_en -> (name_de, name_it, name_es, name_nl, name_pl)
TRANSLATIONS = {
    'Australia': ('Australien', 'Australia', 'Australia', 'Australië', 'Australia'),
    'Bahrain': ('Bahrain', 'Bahrein', 'Baréin', 'Bahrein', 'Bahrajn'),
    'Bangladesh': ('Bangladesch', 'Bangladesh', 'Bangladés', 'Bangladesh', 'Bangladesz'),
    'Belgium': ('Belgien', 'Belgio', 'Bélgica', 'België', 'Belgia'),
    'Brazil': ('Brasilien', 'Brasile', 'Brasil', 'Brazilië', 'Brazylia'),
    'Brunei': ('Brunei', 'Brunei', 'Brunéi', 'Brunei', 'Brunei'),
    'Cambodia': ('Kambodscha', 'Cambogia', 'Camboya', 'Cambodja', 'Kambodża'),
    'Canada': ('Kanada', 'Canada', 'Canadá', 'Canada', 'Kanada'),
    'China': ('China', 'Cina', 'China', 'China', 'Chiny'),
    'Colombia': ('Kolumbien', 'Colombia', 'Colombia', 'Colombia', 'Kolumbia'),
    'Costa rica': ('Costa Rica', 'Costa Rica', 'Costa Rica', 'Costa Rica', 'Kostaryka'),
    'Dominican republic': ('Dominikanische Republik', 'Repubblica Dominicana', 'República Dominicana', 'Dominicaanse Republiek', 'Dominikana'),
    'Egypt': ('Ägypten', 'Egitto', 'Egipto', 'Egypte', 'Egipt'),
    'El salvador': ('El Salvador', 'El Salvador', 'El Salvador', 'El Salvador', 'Salwador'),
    'France': ('Frankreich', 'Francia', 'Francia', 'Frankrijk', 'Francja'),
    'Germany': ('Deutschland', 'Germania', 'Alemania', 'Duitsland', 'Niemcy'),
    'Guatemala': ('Guatemala', 'Guatemala', 'Guatemala', 'Guatemala', 'Gwatemala'),
    'Haiti': ('Haiti', 'Haiti', 'Haití', 'Haïti', 'Haiti'),
    'Honduras': ('Honduras', 'Honduras', 'Honduras', 'Honduras', 'Honduras'),
    'Hong kong': ('Hongkong', 'Hong Kong', 'Hong Kong', 'Hongkong', 'Hongkong'),
    'India': ('Indien', 'India', 'India', 'India', 'Indie'),
    'Indonesia': ('Indonesien', 'Indonesia', 'Indonesia', 'Indonesië', 'Indonezja'),
    'Italy': ('Italien', 'Italia', 'Italia', 'Italië', 'Włochy'),
    'Japan': ('Japan', 'Giappone', 'Japón', 'Japan', 'Japonia'),
    'Jordan': ('Jordanien', 'Giordania', 'Jordania', 'Jordanië', 'Jordania'),
    'Kenya': ('Kenia', 'Kenya', 'Kenia', 'Kenia', 'Kenia'),
    'Malaysia': ('Malaysia', 'Malesia', 'Malasia', 'Maleisië', 'Malezja'),
    'Malta': ('Malta', 'Malta', 'Malta', 'Malta', 'Malta'),
    'Mauritius': ('Mauritius', 'Mauritius', 'Mauricio', 'Mauritius', 'Mauritius'),
    'Mexico': ('Mexiko', 'Messico', 'México', 'Mexico', 'Meksyk'),
    'Morocco': ('Marokko', 'Marocco', 'Marruecos', 'Marokko', 'Maroko'),
    'Netherlands': ('Niederlande', 'Paesi Bassi', 'Países Bajos', 'Nederland', 'Holandia'),
    'Nicaragua': ('Nicaragua', 'Nicaragua', 'Nicaragua', 'Nicaragua', 'Nikaragua'),
    'Norway': ('Norwegen', 'Norvegia', 'Noruega', 'Noorwegen', 'Norwegia'),
    'Pakistan': ('Pakistan', 'Pakistan', 'Pakistán', 'Pakistan', 'Pakistan'),
    'Philippines': ('Philippinen', 'Filippine', 'Filipinas', 'Filipijnen', 'Filipiny'),
    'Poland': ('Polen', 'Polonia', 'Polonia', 'Polen', 'Polska'),
    'Portugal': ('Portugal', 'Portogallo', 'Portugal', 'Portugal', 'Portugalia'),
    'Slovakia': ('Slowakei', 'Slovacchia', 'Eslovaquia', 'Slowakije', 'Słowacja'),
    'South korea': ('Südkorea', 'Corea del Sud', 'Corea del Sur', 'Zuid-Korea', 'Korea Południowa'),
    'Spain': ('Spanien', 'Spagna', 'España', 'Spanje', 'Hiszpania'),
    'Taiwan': ('Taiwan', 'Taiwan', 'Taiwán', 'Taiwan', 'Tajwan'),
    'Tunisia': ('Tunesien', 'Tunisia', 'Túnez', 'Tunesië', 'Tunezja'),
    'Turkey': ('Türkei', 'Turchia', 'Turquía', 'Turkije', 'Turcja'),
    'Turkmenistan': ('Turkmenistan', 'Turkmenistan', 'Turkmenistán', 'Turkmenistan', 'Turkmenistan'),
    'United kingdom': ('Vereinigtes Königreich', 'Regno Unito', 'Reino Unido', 'Verenigd Koninkrijk', 'Wielka Brytania'),
    'Usa': ('USA', 'USA', 'EE. UU.', 'VS', 'USA'),
    'Vietnam': ('Vietnam', 'Vietnam', 'Vietnam', 'Vietnam', 'Wietnam'),
}


def upgrade() -> None:
    """Add missing translations (DE, IT, ES, NL, PL) to origins."""
    conn = op.get_bind()

    for name_en, (name_de, name_it, name_es, name_nl, name_pl) in TRANSLATIONS.items():
        conn.execute(
            text("""
                UPDATE product_attributes.origins
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
    """Remove translations (DE, IT, ES, NL, PL) from origins."""
    conn = op.get_bind()

    for name_en in TRANSLATIONS.keys():
        conn.execute(
            text("""
                UPDATE product_attributes.origins
                SET name_de = NULL,
                    name_it = NULL,
                    name_es = NULL,
                    name_nl = NULL,
                    name_pl = NULL
                WHERE name_en = :name_en
            """),
            {'name_en': name_en}
        )
