"""populate_necklines_translations

Revision ID: 1a0b7e32990f
Revises: 3b2f8560a840
Create Date: 2026-01-08 18:53:59.044770+01:00

Business Rules (2026-01-08):
- Add/update translations (FR, DE, IT, ES, NL, PL) to necklines table
- 20 neckline types total
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '1a0b7e32990f'
down_revision: Union[str, None] = '7c4e9d2b8f3a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Translation data: name_en -> (name_fr, name_de, name_it, name_es, name_nl, name_pl)
TRANSLATIONS = {
    'Boat neck': ('Col bateau', 'Bootausschnitt', 'Scollo a barca', 'Cuello barco', 'Boothals', 'Dekolt łódka'),
    'Collared': ('Col chemise', 'Mit Kragen', 'Con colletto', 'Con cuello', 'Met kraag', 'Z kołnierzem'),
    'Cowl neck': ('Col bénitier', 'Wasserfallausschnitt', 'Collo a cascata', 'Cuello drapeado', 'Cowlhals', 'Dekolt wodospad'),
    'Crew neck': ('Col rond', 'Rundhalsausschnitt', 'Girocollo', 'Cuello redondo', 'Ronde hals', 'Okrągły dekolt'),
    'Halter': ('Col licou', 'Neckholder', 'Collo all\'americana', 'Cuello halter', 'Halter', 'Wiązany na szyi'),
    'Henley': ('Col tunisien', 'Henley-Kragen', 'Collo serafino', 'Cuello panadero', 'Henley', 'Henley'),
    'Hood': ('Capuche', 'Kapuze', 'Cappuccio', 'Capucha', 'Capuchon', 'Kaptur'),
    'Mandarin collar': ('Col mao', 'Stehkragen', 'Collo alla coreana', 'Cuello mao', 'Maokraag', 'Kołnierz stójka'),
    'Mock neck': ('Col montant', 'Stehkragen', 'Collo alto', 'Cuello alto', 'Opstaande kraag', 'Półgolf'),
    'Notch lapel': ('Revers cranté', 'Fallrevers', 'Rever classico', 'Solapa de muesca', 'Inkeping revers', 'Klapa z wcięciem'),
    'Off-shoulder': ('Épaules dénudées', 'Schulterfrei', 'Spalle scoperte', 'Hombros descubiertos', 'Off-shoulder', 'Opadające ramiona'),
    'Peak lapel': ('Revers pointu', 'Spitzrevers', 'Rever a punta', 'Solapa de pico', 'Puntige revers', 'Klapa szpicowa'),
    'Polo collar': ('Col polo', 'Polokragen', 'Collo polo', 'Cuello polo', 'Polokraag', 'Kołnierz polo'),
    'Round neck': ('Col rond', 'Rundhals', 'Scollo tondo', 'Cuello redondo', 'Ronde hals', 'Okrągły dekolt'),
    'Scoop neck': ('Col échancré', 'U-Ausschnitt', 'Scollo ampio', 'Cuello redondo amplio', 'Lage ronde hals', 'Głęboki dekolt'),
    'Shawl collar': ('Col châle', 'Schalkragen', 'Collo a scialle', 'Cuello chal', 'Sjaalkraag', 'Kołnierz szalowy'),
    'Square neck': ('Col carré', 'Karree-Ausschnitt', 'Scollo quadrato', 'Cuello cuadrado', 'Vierkante hals', 'Dekolt karo'),
    'Turtleneck': ('Col roulé', 'Rollkragen', 'Collo alto', 'Cuello alto', 'Coltrui', 'Golf'),
    'V-neck': ('Col V', 'V-Ausschnitt', 'Scollo a V', 'Cuello en V', 'V-hals', 'Dekolt V'),
    'Funnel neck': ('Col cheminée', 'Trichterkragen', 'Collo a imbuto', 'Cuello chimenea', 'Tunnelkraag', 'Kołnierz lejek'),
}


def upgrade() -> None:
    """Add/update translations (FR, DE, IT, ES, NL, PL) to necklines."""
    import sqlalchemy as sa

    # Add missing translation columns if they don't exist
    conn = op.get_bind()

    # Check and add name_de if missing
    result = conn.execute(text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'product_attributes' AND table_name = 'necklines' AND column_name = 'name_de'
    """))
    if not result.fetchone():
        op.add_column('necklines', sa.Column('name_de', sa.String(100), nullable=True, comment="Nom de l'encolure (DE)"), schema='product_attributes')

    # Check and add name_it if missing
    result = conn.execute(text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'product_attributes' AND table_name = 'necklines' AND column_name = 'name_it'
    """))
    if not result.fetchone():
        op.add_column('necklines', sa.Column('name_it', sa.String(100), nullable=True, comment="Nom de l'encolure (IT)"), schema='product_attributes')

    # Check and add name_es if missing
    result = conn.execute(text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'product_attributes' AND table_name = 'necklines' AND column_name = 'name_es'
    """))
    if not result.fetchone():
        op.add_column('necklines', sa.Column('name_es', sa.String(100), nullable=True, comment="Nom de l'encolure (ES)"), schema='product_attributes')

    # Check and add name_nl if missing
    result = conn.execute(text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'product_attributes' AND table_name = 'necklines' AND column_name = 'name_nl'
    """))
    if not result.fetchone():
        op.add_column('necklines', sa.Column('name_nl', sa.String(100), nullable=True, comment="Nom de l'encolure (NL)"), schema='product_attributes')

    # Check and add name_pl if missing
    result = conn.execute(text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'product_attributes' AND table_name = 'necklines' AND column_name = 'name_pl'
    """))
    if not result.fetchone():
        op.add_column('necklines', sa.Column('name_pl', sa.String(100), nullable=True, comment="Nom de l'encolure (PL)"), schema='product_attributes')

    # Now populate translations
    for name_en, (name_fr, name_de, name_it, name_es, name_nl, name_pl) in TRANSLATIONS.items():
        conn.execute(
            text("""
                UPDATE product_attributes.necklines
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
    """Remove translations (FR, DE, IT, ES, NL, PL) from necklines."""
    conn = op.get_bind()

    for name_en in TRANSLATIONS.keys():
        conn.execute(
            text("""
                UPDATE product_attributes.necklines
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
