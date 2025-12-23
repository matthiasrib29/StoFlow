"""fix_genders_add_sizes

Revision ID: 20251222_2100
Revises: fd3f2868d0c9
Create Date: 2025-12-22 21:00:00.000000+01:00

Fixes:
1. Remove duplicate gender entry (unisex vs Unisex)
2. Add numeric clothing sizes (36-46, W28-W38, etc.)
3. Add common materials if missing
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251222_2100'
down_revision: Union[str, None] = 'fd3f2868d0c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Additional sizes to add
SIZES_DATA = [
    # Numeric EU sizes
    ("36", "36", "36", "36", "36", "36", "36"),
    ("38", "38", "38", "38", "38", "38", "38"),
    ("40", "40", "40", "40", "40", "40", "40"),
    ("42", "42", "42", "42", "42", "42", "42"),
    ("44", "44", "44", "44", "44", "44", "44"),
    ("46", "46", "46", "46", "46", "46", "46"),
    ("48", "48", "48", "48", "48", "48", "48"),
    ("50", "50", "50", "50", "50", "50", "50"),
    # XXS and XXL
    ("XXS", "XXS", "XXS", "XXS", "XXS", "XXS", "XXS"),
    ("XXL", "XXL", "XXL", "XXL", "XXL", "XXL", "XXL"),
    ("XXXL", "XXXL", "XXXL", "XXXL", "XXXL", "XXXL", "XXXL"),
    # Waist sizes (jeans)
    ("W28", "W28", "W28", "W28", "W28", "W28", "W28"),
    ("W30", "W30", "W30", "W30", "W30", "W30", "W30"),
    ("W32", "W32", "W32", "W32", "W32", "W32", "W32"),
    ("W34", "W34", "W34", "W34", "W34", "W34", "W34"),
    ("W36", "W36", "W36", "W36", "W36", "W36", "W36"),
    ("W38", "W38", "W38", "W38", "W38", "W38", "W38"),
    # One size
    ("One Size", "Taille Unique", "Einheitsgröße", "Taglia Unica", "Talla Única", "One Size", "Jeden Rozmiar"),
]

# Additional materials to add
MATERIALS_DATA = [
    ("Silk", "Soie", "Seide", "Seta", "Seda", "Zijde", "Jedwab"),
    ("Linen", "Lin", "Leinen", "Lino", "Lino", "Linnen", "Len"),
    ("Cashmere", "Cachemire", "Kaschmir", "Cashmere", "Cachemira", "Kasjmier", "Kaszmir"),
    ("Velvet", "Velours", "Samt", "Velluto", "Terciopelo", "Fluweel", "Aksamit"),
    ("Suede", "Daim", "Wildleder", "Scamosciato", "Ante", "Suède", "Zamsz"),
    ("Nylon", "Nylon", "Nylon", "Nylon", "Nylon", "Nylon", "Nylon"),
    ("Viscose", "Viscose", "Viskose", "Viscosa", "Viscosa", "Viscose", "Wiskoza"),
    ("Acrylic", "Acrylique", "Acryl", "Acrilico", "Acrílico", "Acryl", "Akryl"),
    ("Spandex", "Élasthanne", "Elasthan", "Elastan", "Elastano", "Spandex", "Spandeks"),
    ("Fleece", "Polaire", "Fleece", "Pile", "Polar", "Fleece", "Polar"),
]


def upgrade() -> None:
    """Apply fixes and add data."""

    # 1. Fix duplicate gender - delete lowercase 'unisex' if both exist
    # First check if both exist and delete the one with lowercase
    op.execute(
        sa.text("""
            DELETE FROM product_attributes.genders
            WHERE name_en = 'unisex'
            AND EXISTS (SELECT 1 FROM product_attributes.genders WHERE name_en = 'Unisex')
        """)
    )

    # 2. Add new sizes
    for name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl in SIZES_DATA:
        op.execute(
            sa.text("""
                INSERT INTO product_attributes.sizes (name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl)
                VALUES (:name_en, :name_fr, :name_de, :name_it, :name_es, :name_nl, :name_pl)
                ON CONFLICT (name_en) DO NOTHING
            """).bindparams(
                name_en=name_en,
                name_fr=name_fr,
                name_de=name_de,
                name_it=name_it,
                name_es=name_es,
                name_nl=name_nl,
                name_pl=name_pl,
            )
        )

    # 3. Add new materials
    for name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl in MATERIALS_DATA:
        op.execute(
            sa.text("""
                INSERT INTO product_attributes.materials (name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl)
                VALUES (:name_en, :name_fr, :name_de, :name_it, :name_es, :name_nl, :name_pl)
                ON CONFLICT (name_en) DO NOTHING
            """).bindparams(
                name_en=name_en,
                name_fr=name_fr,
                name_de=name_de,
                name_it=name_it,
                name_es=name_es,
                name_nl=name_nl,
                name_pl=name_pl,
            )
        )


def downgrade() -> None:
    """Remove added data (cannot restore deleted duplicate)."""

    # Remove added sizes
    for name_en, *_ in SIZES_DATA:
        op.execute(
            sa.text("""
                DELETE FROM product_attributes.sizes WHERE name_en = :name_en
            """).bindparams(name_en=name_en)
        )

    # Remove added materials
    for name_en, *_ in MATERIALS_DATA:
        op.execute(
            sa.text("""
                DELETE FROM product_attributes.materials WHERE name_en = :name_en
            """).bindparams(name_en=name_en)
        )
