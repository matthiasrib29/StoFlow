"""populate_patterns_translations

Revision ID: c56fdfee5458
Revises: 1a0b7e32990f
Create Date: 2026-01-08 18:53:59.282796+01:00

Business Rules (2026-01-08):
- Add/update translations (FR, DE, IT, ES, NL, PL) to patterns table
- 18 pattern types total
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'c56fdfee5458'
down_revision: Union[str, None] = '1a0b7e32990f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Translation data: name_en -> (name_fr, name_de, name_it, name_es, name_nl, name_pl)
TRANSLATIONS = {
    'Abstract': ('Abstrait', 'Abstrakt', 'Astratto', 'Abstracto', 'Abstract', 'Abstrakcyjny'),
    'Animal print': ('Imprimé animal', 'Animal-Print', 'Stampa animalier', 'Estampado animal', 'Dierenprint', 'Print zwierzęcy'),
    'Camouflage': ('Camouflage', 'Camouflage', 'Camouflage', 'Camuflaje', 'Camouflage', 'Kamuflaż'),
    'Checkered': ('Carreaux', 'Kariert', 'A quadri', 'Cuadros', 'Geruit', 'Kratka'),
    'Color block': ('Color block', 'Color Block', 'Color block', 'Color block', 'Colorblock', 'Color block'),
    'Floral': ('Floral', 'Blumenmuster', 'Floreale', 'Floral', 'Bloemen', 'Kwiatowy'),
    'Geometric': ('Géométrique', 'Geometrisch', 'Geometrico', 'Geométrico', 'Geometrisch', 'Geometryczny'),
    'Graphic': ('Graphique', 'Grafisch', 'Grafico', 'Gráfico', 'Grafisch', 'Graficzny'),
    'Herringbone': ('Chevrons', 'Fischgrat', 'Spina di pesce', 'Espiguilla', 'Visgraat', 'Jodełka'),
    'Houndstooth': ('Pied-de-poule', 'Hahnentritt', 'Pied de poule', 'Pata de gallo', 'Pied-de-poule', 'Pepitka'),
    'Ombre': ('Ombré', 'Ombré', 'Sfumato', 'Degradado', 'Ombré', 'Ombre'),
    'Paisley': ('Cachemire', 'Paisley', 'Paisley', 'Cachemir', 'Paisley', 'Paisley'),
    'Plaid': ('Tartan', 'Karo', 'Tartan', 'Tartán', 'Tartan', 'Tartan'),
    'Polka dot': ('Pois', 'Punkte', 'Pois', 'Lunares', 'Stippen', 'Grochy'),
    'Solid': ('Uni', 'Unifarben', 'Tinta unita', 'Liso', 'Effen', 'Jednolity'),
    'Striped': ('Rayé', 'Gestreift', 'A righe', 'Rayas', 'Gestreept', 'Paski'),
    'Tie-dye': ('Tie-dye', 'Batik', 'Tie-dye', 'Tie-dye', 'Tie-dye', 'Tie-dye'),
    'Tropical': ('Tropical', 'Tropisch', 'Tropicale', 'Tropical', 'Tropisch', 'Tropikalny'),
}


def upgrade() -> None:
    """Add/update translations (FR, DE, IT, ES, NL, PL) to patterns."""
    import sqlalchemy as sa

    # Add missing translation columns if they don't exist
    conn = op.get_bind()

    # Check and add name_de if missing
    result = conn.execute(text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'product_attributes' AND table_name = 'patterns' AND column_name = 'name_de'
    """))
    if not result.fetchone():
        op.add_column('patterns', sa.Column('name_de', sa.String(100), nullable=True, comment="Nom du motif (DE)"), schema='product_attributes')

    # Check and add name_it if missing
    result = conn.execute(text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'product_attributes' AND table_name = 'patterns' AND column_name = 'name_it'
    """))
    if not result.fetchone():
        op.add_column('patterns', sa.Column('name_it', sa.String(100), nullable=True, comment="Nom du motif (IT)"), schema='product_attributes')

    # Check and add name_es if missing
    result = conn.execute(text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'product_attributes' AND table_name = 'patterns' AND column_name = 'name_es'
    """))
    if not result.fetchone():
        op.add_column('patterns', sa.Column('name_es', sa.String(100), nullable=True, comment="Nom du motif (ES)"), schema='product_attributes')

    # Check and add name_nl if missing
    result = conn.execute(text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'product_attributes' AND table_name = 'patterns' AND column_name = 'name_nl'
    """))
    if not result.fetchone():
        op.add_column('patterns', sa.Column('name_nl', sa.String(100), nullable=True, comment="Nom du motif (NL)"), schema='product_attributes')

    # Check and add name_pl if missing
    result = conn.execute(text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'product_attributes' AND table_name = 'patterns' AND column_name = 'name_pl'
    """))
    if not result.fetchone():
        op.add_column('patterns', sa.Column('name_pl', sa.String(100), nullable=True, comment="Nom du motif (PL)"), schema='product_attributes')

    # Now populate translations
    for name_en, (name_fr, name_de, name_it, name_es, name_nl, name_pl) in TRANSLATIONS.items():
        conn.execute(
            text("""
                UPDATE product_attributes.patterns
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
    """Remove translations (FR, DE, IT, ES, NL, PL) from patterns."""
    conn = op.get_bind()

    for name_en in TRANSLATIONS.keys():
        conn.execute(
            text("""
                UPDATE product_attributes.patterns
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
