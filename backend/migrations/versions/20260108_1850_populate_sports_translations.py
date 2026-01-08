"""populate_sports_translations

Revision ID: e16fb76d1b4d
Revises: 16d3cf7c978a
Create Date: 2026-01-08 18:50:30.318939+01:00

Business Rules (2026-01-08):
- Add/update translations (FR, DE, IT, ES, NL, PL) to sports table
- 28 sport types total
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'e16fb76d1b4d'
down_revision: Union[str, None] = '16d3cf7c978a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Translation data: name_en -> (name_fr, name_de, name_it, name_es, name_nl, name_pl)
TRANSLATIONS = {
    'American football': ('Football américain', 'American Football', 'Football americano', 'Fútbol americano', 'American football', 'Futbol amerykański'),
    'Baseball': ('Baseball', 'Baseball', 'Baseball', 'Béisbol', 'Honkbal', 'Baseball'),
    'Basketball': ('Basketball', 'Basketball', 'Basket', 'Baloncesto', 'Basketbal', 'Koszykówka'),
    'Boxing': ('Boxe', 'Boxen', 'Boxe', 'Boxeo', 'Boksen', 'Boks'),
    'Climbing': ('Escalade', 'Klettern', 'Arrampicata', 'Escalada', 'Klimmen', 'Wspinaczka'),
    'Crossfit': ('Crossfit', 'Crossfit', 'Crossfit', 'Crossfit', 'Crossfit', 'Crossfit'),
    'Cycling': ('Cyclisme', 'Radsport', 'Ciclismo', 'Ciclismo', 'Wielrennen', 'Kolarstwo'),
    'Dance': ('Danse', 'Tanz', 'Danza', 'Baile', 'Dans', 'Taniec'),
    'Equestrian': ('Équitation', 'Reitsport', 'Equitazione', 'Equitación', 'Paardrijden', 'Jeździectwo'),
    'Fitness': ('Fitness', 'Fitness', 'Fitness', 'Fitness', 'Fitness', 'Fitness'),
    'Football/soccer': ('Football', 'Fußball', 'Calcio', 'Fútbol', 'Voetbal', 'Piłka nożna'),
    'Golf': ('Golf', 'Golf', 'Golf', 'Golf', 'Golf', 'Golf'),
    'Gymnastics': ('Gymnastique', 'Turnen', 'Ginnastica', 'Gimnasia', 'Gymnastiek', 'Gimnastyka'),
    'Hiking': ('Randonnée', 'Wandern', 'Escursionismo', 'Senderismo', 'Wandelen', 'Turystyka piesza'),
    'Hockey': ('Hockey', 'Hockey', 'Hockey', 'Hockey', 'Hockey', 'Hokej'),
    'Martial arts': ('Arts martiaux', 'Kampfsport', 'Arti marziali', 'Artes marciales', 'Vechtsporten', 'Sztuki walki'),
    'Motorsport': ('Sport automobile', 'Motorsport', 'Motorsport', 'Automovilismo', 'Autosport', 'Sporty motorowe'),
    'Pilates': ('Pilates', 'Pilates', 'Pilates', 'Pilates', 'Pilates', 'Pilates'),
    'Rugby': ('Rugby', 'Rugby', 'Rugby', 'Rugby', 'Rugby', 'Rugby'),
    'Running': ('Course à pied', 'Laufen', 'Corsa', 'Running', 'Hardlopen', 'Bieganie'),
    'Skateboarding': ('Skateboard', 'Skateboarding', 'Skateboard', 'Skateboard', 'Skateboarden', 'Skateboarding'),
    'Ski': ('Ski', 'Ski', 'Sci', 'Esquí', 'Skiën', 'Narciarstwo'),
    'Snowboard': ('Snowboard', 'Snowboard', 'Snowboard', 'Snowboard', 'Snowboard', 'Snowboard'),
    'Surfing': ('Surf', 'Surfen', 'Surf', 'Surf', 'Surfen', 'Surfing'),
    'Swimming': ('Natation', 'Schwimmen', 'Nuoto', 'Natación', 'Zwemmen', 'Pływanie'),
    'Tennis': ('Tennis', 'Tennis', 'Tennis', 'Tenis', 'Tennis', 'Tenis'),
    'Volleyball': ('Volleyball', 'Volleyball', 'Pallavolo', 'Voleibol', 'Volleybal', 'Siatkówka'),
    'Yoga': ('Yoga', 'Yoga', 'Yoga', 'Yoga', 'Yoga', 'Joga'),
}


def upgrade() -> None:
    """Add/update translations (FR, DE, IT, ES, NL, PL) to sports."""
    import sqlalchemy as sa

    # Add missing translation columns if they don't exist
    conn = op.get_bind()

    # Check and add name_de if missing
    result = conn.execute(text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'product_attributes' AND table_name = 'sports' AND column_name = 'name_de'
    """))
    if not result.fetchone():
        op.add_column('sports', sa.Column('name_de', sa.String(100), nullable=True, comment="Nom du sport (DE)"), schema='product_attributes')

    # Check and add name_it if missing
    result = conn.execute(text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'product_attributes' AND table_name = 'sports' AND column_name = 'name_it'
    """))
    if not result.fetchone():
        op.add_column('sports', sa.Column('name_it', sa.String(100), nullable=True, comment="Nom du sport (IT)"), schema='product_attributes')

    # Check and add name_es if missing
    result = conn.execute(text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'product_attributes' AND table_name = 'sports' AND column_name = 'name_es'
    """))
    if not result.fetchone():
        op.add_column('sports', sa.Column('name_es', sa.String(100), nullable=True, comment="Nom du sport (ES)"), schema='product_attributes')

    # Check and add name_nl if missing
    result = conn.execute(text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'product_attributes' AND table_name = 'sports' AND column_name = 'name_nl'
    """))
    if not result.fetchone():
        op.add_column('sports', sa.Column('name_nl', sa.String(100), nullable=True, comment="Nom du sport (NL)"), schema='product_attributes')

    # Check and add name_pl if missing
    result = conn.execute(text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'product_attributes' AND table_name = 'sports' AND column_name = 'name_pl'
    """))
    if not result.fetchone():
        op.add_column('sports', sa.Column('name_pl', sa.String(100), nullable=True, comment="Nom du sport (PL)"), schema='product_attributes')

    # Now populate translations
    for name_en, (name_fr, name_de, name_it, name_es, name_nl, name_pl) in TRANSLATIONS.items():
        conn.execute(
            text("""
                UPDATE product_attributes.sports
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
    """Remove translations (FR, DE, IT, ES, NL, PL) from sports."""
    conn = op.get_bind()

    for name_en in TRANSLATIONS.keys():
        conn.execute(
            text("""
                UPDATE product_attributes.sports
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
