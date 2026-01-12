"""cleanup_fits_lengths_duplicate_cropped

Revision ID: 0j1k2l3m4n5o
Revises: 9i0j1k2l3m4n
Create Date: 2025-12-11 17:39:00.000000+01:00

Cette migration nettoie le doublon entre les tables fits et lengths.

Business Rule (Validé 2025-12-11):
- "cropped" est une longueur (length), pas une coupe (fit)
- Cette valeur doit être retirée de fits

Actions:
- Supprime "cropped" de fits (existe déjà dans lengths comme "Cropped")

Note: "cropped" (fits) vs "Cropped" (lengths) - même concept, casse différente

Author: Claude
Date: 2025-12-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0j1k2l3m4n5o'
down_revision: Union[str, None] = '9i0j1k2l3m4n'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Supprime le doublon "cropped" de fits qui est en fait une longueur.
    """
    connection = op.get_bind()

    # Vérifier si la valeur existe dans fits
    result = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT FROM product_attributes.fits
            WHERE name_en = 'cropped'
        )
    """))

    exists = result.scalar()

    if exists:
        # Supprimer la valeur
        connection.execute(sa.text("""
            DELETE FROM product_attributes.fits
            WHERE name_en = 'cropped'
        """))
        print("  ✓ Deleted 'cropped' from fits (already in lengths as 'Cropped')")
    else:
        print("  ⏭️  'cropped' not found in fits, skipping (already deleted)")

    # Vérifier que Cropped existe dans lengths
    result = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT FROM product_attributes.lengths
            WHERE name_en = 'Cropped'
        )
    """))

    exists_in_lengths = result.scalar()

    if exists_in_lengths:
        print("  ✓ Verified: 'Cropped' exists in lengths")
    else:
        print("  ⚠️  Warning: 'Cropped' NOT FOUND in lengths")

    # Afficher le résumé
    result = connection.execute(sa.text("SELECT COUNT(*) FROM product_attributes.fits"))
    count = result.scalar()
    print(f"  ℹ️  Remaining fits: {count}")


def downgrade() -> None:
    """
    Restaure la valeur supprimée (pour rollback).
    """
    connection = op.get_bind()

    # Vérifier si la valeur existe déjà dans fits
    result = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT FROM product_attributes.fits
            WHERE name_en = 'cropped'
        )
    """))

    exists = result.scalar()

    if not exists:
        # Ré-insérer la valeur
        connection.execute(sa.text("""
            INSERT INTO product_attributes.fits (name_en, name_fr)
            VALUES ('cropped', 'court')
        """))
        print("  ✓ Restored 'cropped' to fits")
    else:
        print("  ⏭️  'cropped' already exists in fits, skipping")
