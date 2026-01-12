"""cleanup_seasons_duplicates

Revision ID: 1k2l3m4n5o6p
Revises: 0j1k2l3m4n5o
Create Date: 2025-12-11 17:51:00.000000+01:00

Cette migration nettoie les doublons et redondances dans la table seasons.

Business Rule (Validé 2025-12-11):
- "autumn" et "fall" sont la même saison → garder "autumn", supprimer "fall"
- "all season" et "year round" sont la même chose → garder "all season", supprimer "year round"
- "fall/winter" est redondant (composé de autumn + winter) → supprimer
- "spring/summer" est redondant (composé de spring + summer) → supprimer

Résultat final: 5 saisons de base (all season, autumn, spring, summer, winter)

Actions:
- Supprime "fall" (doublon de "autumn")
- Supprime "year round" (doublon de "all season")
- Supprime "fall/winter" (redondant)
- Supprime "spring/summer" (redondant)

Author: Claude
Date: 2025-12-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1k2l3m4n5o6p'
down_revision: Union[str, None] = '0j1k2l3m4n5o'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Supprime les doublons et redondances de la table seasons.
    """
    connection = op.get_bind()

    # Liste des valeurs à supprimer avec leur raison
    duplicates = [
        ('fall', 'doublon de "autumn"'),
        ('year round', 'doublon de "all season"'),
        ('fall/winter', 'redondant (autumn + winter)'),
        ('spring/summer', 'redondant (spring + summer)'),
    ]

    deleted_count = 0

    for value, reason in duplicates:
        # Vérifier si la valeur existe
        result = connection.execute(sa.text("""
            SELECT EXISTS (
                SELECT FROM product_attributes.seasons
                WHERE name_en = :value
            )
        """), {"value": value})

        exists = result.scalar()

        if exists:
            # Supprimer la valeur
            connection.execute(sa.text("""
                DELETE FROM product_attributes.seasons
                WHERE name_en = :value
            """), {"value": value})
            print(f"  ✓ Deleted '{value}' from seasons ({reason})")
            deleted_count += 1
        else:
            print(f"  ⏭️  '{value}' not found in seasons, skipping")

    # Afficher le résumé
    result = connection.execute(sa.text("SELECT COUNT(*) FROM product_attributes.seasons"))
    count = result.scalar()
    print(f"  ℹ️  Remaining seasons: {count} (deleted {deleted_count} duplicates)")

    # Lister les saisons restantes
    result = connection.execute(sa.text("SELECT name_en FROM product_attributes.seasons ORDER BY name_en"))
    remaining = [row[0] for row in result]
    print(f"  📋 Seasons: {', '.join(remaining)}")


def downgrade() -> None:
    """
    Restaure les valeurs supprimées (pour rollback).
    """
    connection = op.get_bind()

    # Ré-insérer les valeurs supprimées
    values_to_restore = [
        ('fall', 'automne'),
        ('year round', 'toute l\'année'),
        ('fall/winter', 'automne/hiver'),
        ('spring/summer', 'printemps/été'),
    ]

    for name_en, name_fr in values_to_restore:
        # Vérifier si la valeur existe déjà
        result = connection.execute(sa.text("""
            SELECT EXISTS (
                SELECT FROM product_attributes.seasons
                WHERE name_en = :value
            )
        """), {"value": name_en})

        exists = result.scalar()

        if not exists:
            # Ré-insérer la valeur
            connection.execute(sa.text("""
                INSERT INTO product_attributes.seasons (name_en, name_fr)
                VALUES (:name_en, :name_fr)
            """), {"name_en": name_en, "name_fr": name_fr})
            print(f"  ✓ Restored '{name_en}' to seasons")
        else:
            print(f"  ⏭️  '{name_en}' already exists in seasons, skipping")
