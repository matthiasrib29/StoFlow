"""populate_lengths_translations

Revision ID: 7c4e9d2b8f3a
Revises: e16fb76d1b4d
Create Date: 2026-01-08 18:53:10.123456+01:00

Business Rules (2026-01-08):
- Add/update translations (FR, DE, IT, ES, NL, PL) to lengths table
- 12 length types total
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '7c4e9d2b8f3a'
down_revision: Union[str, None] = 'e16fb76d1b4d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Translation data: name_en -> (name_fr, name_de, name_it, name_es, name_nl, name_pl)
TRANSLATIONS = {
    'Ankle': ('Cheville', 'Knöchellang', 'Alla caviglia', 'Tobillero', 'Enkellang', 'Do kostki'),
    'Capri': ('Capri', 'Capri', 'Capri', 'Capri', 'Capri', 'Capri'),
    'Cropped': ('Raccourci', 'Cropped', 'Cropped', 'Cropped', 'Cropped', 'Skrócony'),
    'Extra long': ('Extra long', 'Extralang', 'Extra lungo', 'Extra largo', 'Extra lang', 'Ekstra długi'),
    'Floor length': ('Longueur sol', 'Bodenlang', 'Lunghezza pavimento', 'Largo al suelo', 'Vloerlang', 'Do ziemi'),
    'Knee length': ('Mi-long', 'Knielang', 'Al ginocchio', 'Hasta la rodilla', 'Knielang', 'Do kolan'),
    'Long': ('Long', 'Lang', 'Lungo', 'Largo', 'Lang', 'Długi'),
    'Maxi': ('Maxi', 'Maxi', 'Maxi', 'Maxi', 'Maxi', 'Maxi'),
    'Midi': ('Midi', 'Midi', 'Midi', 'Midi', 'Midi', 'Midi'),
    'Mini': ('Mini', 'Mini', 'Mini', 'Mini', 'Mini', 'Mini'),
    'Regular': ('Standard', 'Regular', 'Regolare', 'Regular', 'Normaal', 'Standardowy'),
    'Short': ('Court', 'Kurz', 'Corto', 'Corto', 'Kort', 'Krótki'),
}


def upgrade() -> None:
    """Add/update translations (FR, DE, IT, ES, NL, PL) to lengths."""
    import sqlalchemy as sa

    # Add missing translation columns if they don't exist
    conn = op.get_bind()

    # Check and add name_de if missing
    result = conn.execute(text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'product_attributes' AND table_name = 'lengths' AND column_name = 'name_de'
    """))
    if not result.fetchone():
        op.add_column('lengths', sa.Column('name_de', sa.String(100), nullable=True, comment="Nom de la longueur (DE)"), schema='product_attributes')

    # Check and add name_it if missing
    result = conn.execute(text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'product_attributes' AND table_name = 'lengths' AND column_name = 'name_it'
    """))
    if not result.fetchone():
        op.add_column('lengths', sa.Column('name_it', sa.String(100), nullable=True, comment="Nom de la longueur (IT)"), schema='product_attributes')

    # Check and add name_es if missing
    result = conn.execute(text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'product_attributes' AND table_name = 'lengths' AND column_name = 'name_es'
    """))
    if not result.fetchone():
        op.add_column('lengths', sa.Column('name_es', sa.String(100), nullable=True, comment="Nom de la longueur (ES)"), schema='product_attributes')

    # Check and add name_nl if missing
    result = conn.execute(text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'product_attributes' AND table_name = 'lengths' AND column_name = 'name_nl'
    """))
    if not result.fetchone():
        op.add_column('lengths', sa.Column('name_nl', sa.String(100), nullable=True, comment="Nom de la longueur (NL)"), schema='product_attributes')

    # Check and add name_pl if missing
    result = conn.execute(text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'product_attributes' AND table_name = 'lengths' AND column_name = 'name_pl'
    """))
    if not result.fetchone():
        op.add_column('lengths', sa.Column('name_pl', sa.String(100), nullable=True, comment="Nom de la longueur (PL)"), schema='product_attributes')

    # Now populate translations
    for name_en, (name_fr, name_de, name_it, name_es, name_nl, name_pl) in TRANSLATIONS.items():
        conn.execute(
            text("""
                UPDATE product_attributes.lengths
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
    """Remove translations (FR, DE, IT, ES, NL, PL) from lengths."""
    conn = op.get_bind()

    for name_en in TRANSLATIONS.keys():
        conn.execute(
            text("""
                UPDATE product_attributes.lengths
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
