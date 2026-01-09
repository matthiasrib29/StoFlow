"""seed_fits_data

Revision ID: fd3f2868d0c9
Revises: 20251222_1200
Create Date: 2025-12-22 19:43:44.432351+01:00

Inserts standard fit types into product_attributes.fits table.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fd3f2868d0c9'
down_revision: Union[str, None] = '20251222_1200'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Fits data to seed
FITS_DATA = [
    ("Slim", "Ajusté", "Slim", "Aderente", "Ajustado", "Slim", "Dopasowany"),
    ("Regular", "Regular", "Regular", "Regular", "Regular", "Normaal", "Regularny"),
    ("Relaxed", "Décontracté", "Entspannt", "Rilassato", "Relajado", "Relaxed", "Luźny"),
    ("Oversized", "Oversize", "Oversized", "Oversize", "Oversize", "Oversized", "Oversize"),
    ("Tight", "Moulant", "Eng", "Aderente", "Ceñido", "Strak", "Obcisły"),
    ("Loose", "Ample", "Locker", "Largo", "Holgado", "Ruim", "Luźny"),
]


def upgrade() -> None:
    """Insert fits data."""
    # Use raw SQL for data migration
    for name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl in FITS_DATA:
        op.execute(
            sa.text("""
                INSERT INTO product_attributes.fits (name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl)
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
    """Remove fits data."""
    for name_en, *_ in FITS_DATA:
        op.execute(
            sa.text("""
                DELETE FROM product_attributes.fits WHERE name_en = :name_en
            """).bindparams(name_en=name_en)
        )
