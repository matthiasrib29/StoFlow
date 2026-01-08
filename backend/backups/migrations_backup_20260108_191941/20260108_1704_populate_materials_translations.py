"""populate_materials_translations

Revision ID: a4d8e2f9c1b3
Revises: 93a8fb1b3d42
Create Date: 2026-01-08 17:04:12.123456+01:00

Business Rules (2026-01-08):
- Add/update translations (FR, DE, IT, ES, NL, PL) to materials table
- 27 materials total
- Some FR translations were missing, now completed
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'a4d8e2f9c1b3'
down_revision: Union[str, None] = '93a8fb1b3d42'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Translation data: name_en -> (name_fr, name_de, name_it, name_es, name_nl, name_pl)
TRANSLATIONS = {
    'Crochet': ('Crochet', 'Häkelstoff', 'Uncinetto', 'Crochet', 'Gehaakt', 'Szydełkowy'),
    'Lace': ('Dentelle', 'Spitze', 'Pizzo', 'Encaje', 'Kant', 'Koronka'),
    'Technical fabric': ('Tissu technique', 'Funktionsstoff', 'Tessuto tecnico', 'Tejido técnico', 'Technische stof', 'Tkanina techniczna'),
    'Silk': ('Soie', 'Seide', 'Seta', 'Seda', 'Zijde', 'Jedwab'),
    'Cotton': ('Coton', 'Baumwolle', 'Cotone', 'Algodón', 'Katoen', 'Bawełna'),
    'Polyester': ('Polyester', 'Polyester', 'Poliestere', 'Poliéster', 'Polyester', 'Poliester'),
    'Wool': ('Laine', 'Wolle', 'Lana', 'Lana', 'Wol', 'Wełna'),
    'Leather': ('Cuir', 'Leder', 'Pelle', 'Cuero', 'Leer', 'Skóra'),
    'Denim': ('Denim', 'Denim', 'Denim', 'Denim', 'Denim', 'Denim'),
    'Linen': ('Lin', 'Leinen', 'Lino', 'Lino', 'Linnen', 'Len'),
    'Cashmere': ('Cachemire', 'Kaschmir', 'Cashmere', 'Cachemir', 'Kasjmier', 'Kaszmir'),
    'Velvet': ('Velours', 'Samt', 'Velluto', 'Terciopelo', 'Fluweel', 'Aksamit'),
    'Suede': ('Daim', 'Wildleder', 'Scamosciato', 'Ante', 'Suède', 'Zamsz'),
    'Nylon': ('Nylon', 'Nylon', 'Nylon', 'Nailon', 'Nylon', 'Nylon'),
    'Viscose': ('Viscose', 'Viskose', 'Viscosa', 'Viscosa', 'Viscose', 'Wiskoza'),
    'Acrylic': ('Acrylique', 'Acryl', 'Acrilico', 'Acrílico', 'Acryl', 'Akryl'),
    'Spandex': ('Élasthanne', 'Elasthan', 'Spandex', 'Spandex', 'Spandex', 'Spandex'),
    'Fleece': ('Polaire', 'Fleece', 'Pile', 'Forro polar', 'Fleece', 'Polar'),
    'Corduroy': ('Velours côtelé', 'Cord', 'Velluto a coste', 'Pana', 'Ribfluweel', 'Sztruks'),
    'Elastane': ('Élasthanne', 'Elasthan', 'Elastan', 'Elastano', 'Elastaan', 'Elastan'),
    'Flannel': ('Flanelle', 'Flanell', 'Flanella', 'Franela', 'Flanel', 'Flanela'),
    'Hemp': ('Chanvre', 'Hanf', 'Canapa', 'Cáñamo', 'Hennep', 'Konopie'),
    'Lyocell': ('Lyocell', 'Lyocell', 'Lyocell', 'Lyocell', 'Lyocell', 'Lyocell'),
    'Modal': ('Modal', 'Modal', 'Modal', 'Modal', 'Modal', 'Modal'),
    'Rayon': ('Rayonne', 'Rayon', 'Rayon', 'Rayón', 'Rayon', 'Wiskoza sztuczna'),
    'Satin': ('Satin', 'Satin', 'Raso', 'Satén', 'Satijn', 'Satyna'),
    'Tweed': ('Tweed', 'Tweed', 'Tweed', 'Tweed', 'Tweed', 'Tweed'),
}


def upgrade() -> None:
    """Add/update translations (FR, DE, IT, ES, NL, PL) to materials."""
    conn = op.get_bind()

    for name_en, (name_fr, name_de, name_it, name_es, name_nl, name_pl) in TRANSLATIONS.items():
        conn.execute(
            text("""
                UPDATE product_attributes.materials
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
    """Remove translations (FR, DE, IT, ES, NL, PL) from materials."""
    conn = op.get_bind()

    for name_en in TRANSLATIONS.keys():
        conn.execute(
            text("""
                UPDATE product_attributes.materials
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
